import csv
import random
from collections import Counter
from dataclasses import dataclass, field
from typing import NamedTuple

from war_of_the_ring_ai.constants import (
    FELLOWSHIP_START,
    INITIAL_GUIDE_ID,
    CharacterType,
    DieResult,
    UnitRank,
)
from war_of_the_ring_ai.game_objects import (
    ArmyUnit,
    Card,
    CardCategory,
    Character,
    CharacterID,
    HuntTile,
    Nation,
    Region,
    Settlement,
    Side,
)

IN_FELLOWSHIP = Region("Fellowship")
IN_REINFORCEMENTS = Region("Reinforcements")
IN_CASUALTIES = Region("Casualties")
IN_MORDOR = Region("Mordor")


class RegionMap:
    def __init__(self):
        self._regions_by_name: dict[str, Region] = {}
        self._regions: dict[Region, list[Region]] = {}

    def add_region(self, region: Region) -> None:
        if region in self._regions:
            raise ValueError(f"Region {region.name} already added to map.")
        self._regions_by_name[region.name] = region
        self._regions[region] = []

    def add_connection(self, from_region: Region, to_region: Region) -> None:
        self._regions[from_region].append(to_region)

    def get_region(self, name: str) -> Region:
        return self._regions_by_name[name]

    def neighbors(self, region: Region) -> list[Region]:
        return self._regions[region]

    def reachable_regions(self, start: Region, distance: int) -> set[Region]:
        return self._reachable_region_search(distance, {start}, {start})

    def _reachable_region_search(
        self, distance: int, search: set[Region], reached: set[Region]
    ) -> set[Region]:
        if distance == 0:
            return reached

        next_search = {
            neighbor
            for region in search
            for neighbor in self.neighbors(region)
            if neighbor not in reached
        }
        reached |= next_search
        return self._reachable_region_search(distance - 1, next_search, reached)


@dataclass
class Fellowship:
    guide: Character
    location: Region
    revealed: bool = False
    progress: int = 0
    corruption: int = 0


@dataclass
class PoliticalStatus:
    disposition: int
    active: bool

    def is_at_war(self) -> bool:
        return self.disposition == 0

    def can_advance(self) -> bool:
        if self.disposition > 1:
            return True
        if self.disposition == 1:
            return self.active
        return False


@dataclass
class HuntBox:
    eyes: int = 0
    character: int = 0


class HuntPool:
    def __init__(self):
        self._pool: list[HuntTile] = []
        self._discarded: list[HuntTile] = []

    def add_tile(self, tile: HuntTile) -> None:
        self._pool.append(tile)

    def draw(self) -> HuntTile:
        return random.choice(self._pool)

    def discard(self, tile: HuntTile) -> None:
        self._pool.remove(tile)
        self._discarded.append(tile)

    def remove(self, tile: HuntTile) -> None:
        self._pool.remove(tile)


@dataclass
class PublicPlayerState:  # pylint: disable=too-many-instance-attributes
    starting_dice: int
    elven_rings: int
    character_deck_size: int
    strategy_deck_size: int
    character_deck_played: list[Card] = field(default_factory=list)
    strategy_deck_played: list[Card] = field(default_factory=list)
    dice: Counter[DieResult] = field(default_factory=Counter)
    victory_points: int = 0


@dataclass
class PrivatePlayerState:
    character_deck: list[Card]
    strategy_deck: list[Card]
    hand: list[Card] = field(default_factory=list)


@dataclass
class GameState:  # pylint: disable=too-many-instance-attributes
    def __init__(self):
        self.regions: RegionMap = init_region_map()
        self.armies: list[ArmyUnit] = init_armies(self.regions)
        self.characters: dict[CharacterID, Character] = init_characters()
        self.reinforcements: dict[Nation, dict[UnitRank, int]] = init_reinforcements()
        self.politics: dict[Nation, PoliticalStatus] = init_politics()
        self.hunt_pool: HuntPool = init_hunt_pool()
        self.hunt_box = HuntBox()
        self.fellowship = Fellowship(
            self.characters[INITIAL_GUIDE_ID], self.regions.get_region(FELLOWSHIP_START)
        )
        self.free_player: PublicPlayerState = init_public_player_state(Side.FREE)
        self.shadow_player: PublicPlayerState = init_public_player_state(Side.SHADOW)


def init_region_map() -> RegionMap:
    class RegionData(NamedTuple):
        name: str
        neighbors: list[str]
        nation: str
        settlement: str

    regions: RegionMap = RegionMap()
    region_data: list[RegionData] = []

    with open("data/worldmap.csv", newline="", encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter="|")
        for name, neighbors, nation, settlement, _, _, _ in reader:
            region_data.append(
                RegionData(
                    name, neighbors.split(","), nation.upper(), settlement.upper()
                )
            )

    for data in region_data:
        nation = None if data.nation == "NONE" else Nation[data.nation]
        match data.settlement:
            case "NONE":
                settlement = None
                is_fortification = False
            case "FORTIFICATION":
                settlement = None
                is_fortification = True
            case _:
                settlement = Settlement[data.settlement]
                is_fortification = False

        region = Region(data.name, nation, settlement, is_fortification)
        regions.add_region(region)

    for data in region_data:
        from_region = regions.get_region(data.name)
        for neighbor in data.neighbors:
            regions.add_connection(from_region, regions.get_region(neighbor))

    return regions


def init_armies(regions: RegionMap) -> list[ArmyUnit]:
    armies: list[ArmyUnit] = []

    with open("data/worldmap.csv", newline="", encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter="|")
        for name, _, _, _, regulars, elites, leaders in reader:
            unit_counts = {
                UnitRank.REGULAR: int(regulars),
                UnitRank.ELITE: int(elites),
                UnitRank.LEADER: int(leaders),
            }
            if any(count > 0 for count in unit_counts.values()):
                region = regions.get_region(name)
                nation = region.nation if region.nation else Nation.GONDOR
                units = [
                    ArmyUnit(region, rank, nation)
                    for rank, count in unit_counts.items()
                    for _ in range(count)
                ]
                armies.extend(units)

    return armies


def init_characters() -> dict[CharacterID, Character]:
    characters: dict[CharacterID, Character] = {}

    with open("data/characters.csv", newline="", encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter="|")
        for character_id, location_str, character_type, level, leadership in reader:
            character = Character(
                IN_FELLOWSHIP if location_str == "IN_FELLOWSHIP" else IN_REINFORCEMENTS,
                CharacterID[character_id],
                CharacterType[character_type],
                int(level),
                int(leadership),
            )
            characters[character.id] = character

    return characters


def init_reinforcements() -> dict[Nation, dict[UnitRank, int]]:
    reinforcements: dict[Nation, dict[UnitRank, int]] = {}

    with open("data/reinforcements.csv", newline="", encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter="|")
        for nation, regulars, elites, leaders in reader:
            reinforcements[Nation[nation]] = {
                UnitRank.REGULAR: int(regulars),
                UnitRank.ELITE: int(elites),
                UnitRank.LEADER: int(leaders),
            }

    return reinforcements


def init_politics() -> dict[Nation, PoliticalStatus]:
    politics: dict[Nation, PoliticalStatus] = {}

    with open("data/politics.csv", newline="", encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter="|")
        for nation, disposition, active in reader:
            political_status = PoliticalStatus(int(disposition), active == "active")
            politics[Nation[nation]] = political_status

    return politics


def init_hunt_pool() -> HuntPool:
    hunt_pool = HuntPool()

    with open("data/hunt.csv", newline="", encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter="|")
        for corruption, reveal in reader:
            tile = HuntTile(int(corruption), reveal == "REVEAL", None)
            hunt_pool.add_tile(tile)

    return hunt_pool


def init_public_player_state(player_side: Side) -> PublicPlayerState:
    starting_dice = 4 if player_side == Side.FREE else 7
    elven_rings = 3 if player_side == Side.FREE else 0
    character_deck_size = 0
    strategy_deck_size = 0

    with open("data/cards.csv", newline="", encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter="|")
        for _, _, side, category in reader:
            if Side[side] == player_side:
                if CardCategory[category] == CardCategory.CHARACTER:
                    character_deck_size += 1
                else:
                    strategy_deck_size += 1

    return PublicPlayerState(
        starting_dice, elven_rings, character_deck_size, strategy_deck_size
    )


def init_private_player_state(player_side: Side) -> PrivatePlayerState:
    character_deck: list[Card] = []
    strategy_deck: list[Card] = []

    with open("data/cards.csv", newline="", encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter="|")
        for event, combat, side, category in reader:
            if Side[side] == player_side:
                card = Card(event, combat, Side[side], CardCategory[category])
                if card.category == CardCategory.CHARACTER:
                    character_deck.append(card)
                else:
                    strategy_deck.append(card)

    return PrivatePlayerState(character_deck, strategy_deck)
