import csv
import random
from dataclasses import dataclass, field
from typing import Mapping, NamedTuple

from war_of_the_ring_ai.constants import (
    FELLOWSHIP_START,
    INITIAL_GUIDE_ID,
    CardType,
    CharacterID,
    DeckType,
    DieResult,
    Nation,
    Settlement,
    Side,
    UnitRank,
)
from war_of_the_ring_ai.game_objects import (
    FELLOWSHIP,
    REINFORCEMENTS,
    ArmyUnit,
    ArmyUnitCollection,
    Card,
    Character,
    CharacterCollection,
    HuntTile,
    Region,
    RegionCollection,
)


class RegionMap:
    def __init__(self) -> None:
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

    def all_regions(self) -> RegionCollection:
        return RegionCollection(self._regions.keys())

    def neighbors(self, region: Region) -> list[Region]:
        return self._regions[region]

    def reachable_regions(self, start: Region, distance: int) -> list[Region]:
        return list(self._reachable_region_search(distance, {start}, {start}))

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
    is_revealed: bool = False
    progress: int = 0
    corruption: int = 0
    moved: bool = False


@dataclass
class PoliticalStatus:
    disposition: int
    active: bool

    @property
    def is_at_war(self) -> bool:
        return self.disposition == 0

    @property
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
    def __init__(self) -> None:
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
class PublicDeckData:
    size: int
    played: list[Card] = field(default_factory=list)
    discarded: int = 0


@dataclass
class PublicPlayerData:
    side: Side
    starting_dice: int
    elven_rings: int
    decks: Mapping[DeckType, PublicDeckData]
    hand: list[DeckType] = field(default_factory=list)
    dice: list[DieResult] = field(default_factory=list)
    victory_points: int = 0


@dataclass
class PrivateDeckData:
    cards: list[Card]
    discarded: list[Card] = field(default_factory=list)


@dataclass
class PrivatePlayerData:
    decks: Mapping[DeckType, PrivateDeckData]
    hand: list[Card] = field(default_factory=list)


@dataclass
class PlayerData:
    public: PublicPlayerData
    private: PrivatePlayerData


@dataclass
class GameData:  # pylint: disable=too-many-instance-attributes
    def __init__(self, free: PublicPlayerData, shadow: PublicPlayerData) -> None:
        self.turn: int = 0
        self.regions: RegionMap = init_region_map()
        self.conquered: set[Region] = set()
        self.armies: ArmyUnitCollection = ArmyUnitCollection(
            init_armies(self.regions) + init_reinforcements()
        )
        self.characters: CharacterCollection = CharacterCollection(init_characters())
        self.politics: dict[Nation, PoliticalStatus] = init_politics()
        self.hunt_pool: HuntPool = init_hunt_pool()
        self.hunt_box = HuntBox()
        self.fellowship = Fellowship(
            self.characters.with_id(INITIAL_GUIDE_ID),
            self.regions.get_region(FELLOWSHIP_START),
        )
        self.players: Mapping[Side, PublicPlayerData] = {
            Side.FREE: free,
            Side.SHADOW: shadow,
        }
        self._active_side: Side = Side.FREE

    @property
    def active_side(self) -> Side:
        return self._active_side

    @active_side.setter
    def active_side(self, side: Side) -> None:
        self._active_side = side

    @property
    def inactive_side(self) -> Side:
        return Side.FREE if self.active_side == Side.SHADOW else Side.SHADOW


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
        region = Region(
            name=data.name,
            nation=None if data.nation == "NONE" else Nation[data.nation],
            settlement=None
            if data.settlement in ("NONE", "FORTIFICATION")
            else Settlement[data.settlement],
            is_fortification=data.settlement == "FORTIFICATION",
        )
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
            region = regions.get_region(name)
            nation = region.nation if region.nation else Nation.GONDOR
            units = [
                ArmyUnit(region, rank, nation)
                for rank, count in unit_counts.items()
                for _ in range(count)
            ]
            armies.extend(units)

    return armies


def init_reinforcements() -> list[ArmyUnit]:
    armies: list[ArmyUnit] = []

    with open("data/reinforcements.csv", newline="", encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter="|")
        for nation, regulars, elites, leaders in reader:
            unit_counts = {
                UnitRank.REGULAR: int(regulars),
                UnitRank.ELITE: int(elites),
                UnitRank.LEADER: int(leaders),
            }
            units = [
                ArmyUnit(REINFORCEMENTS, rank, Nation[nation])
                for rank, count in unit_counts.items()
                for _ in range(count)
            ]
            armies.extend(units)

    return armies


def init_characters() -> list[Character]:
    characters: list[Character] = []

    with open("data/characters.csv", newline="", encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter="|")
        for character_id, location_str, side, level, leadership in reader:
            character = Character(
                FELLOWSHIP if location_str == "IN_FELLOWSHIP" else REINFORCEMENTS,
                CharacterID[character_id],
                Side[side],
                int(level),
                int(leadership),
            )
            characters.append(character)

    return characters


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


def init_public_player_data(player_side: Side) -> PublicPlayerData:
    starting_dice = 4 if player_side == Side.FREE else 7
    elven_rings = 3 if player_side == Side.FREE else 0
    decks = {
        DeckType.CHARACTER: PublicDeckData(size=0),
        DeckType.STRATEGY: PublicDeckData(size=0),
    }

    with open("data/cards.csv", newline="", encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter="|")
        for _, _, side, card_type in reader:
            if Side[side] == player_side:
                if CardType[card_type] == CardType.CHARACTER:
                    decks[DeckType.CHARACTER].size += 1
                else:
                    decks[DeckType.STRATEGY].size += 1

    return PublicPlayerData(player_side, starting_dice, elven_rings, decks)


def init_private_player_data(player_side: Side) -> PrivatePlayerData:
    decks = {
        DeckType.CHARACTER: PrivateDeckData(cards=[]),
        DeckType.STRATEGY: PrivateDeckData(cards=[]),
    }

    with open("data/cards.csv", newline="", encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter="|")
        for event, combat, side, card_type in reader:
            if Side[side] == player_side:
                card = Card(event, combat, Side[side], CardType[card_type])
                if card.type == CardType.CHARACTER:
                    decks[DeckType.CHARACTER].cards.append(card)
                else:
                    decks[DeckType.STRATEGY].cards.append(card)

    return PrivatePlayerData(decks)
