import csv
from collections import Counter, deque
from copy import deepcopy
from dataclasses import dataclass, field
from random import shuffle
from typing import Optional

from war_of_the_ring_ai.agent import Agent, random_strategy
from war_of_the_ring_ai.game_objects import (
    NATION_SIDE,
    Army,
    ArmyUnit,
    Card,
    CardCategory,
    CharacterID,
    Companion,
    DieResult,
    ElvenRings,
    Fellowship,
    Nation,
    PoliticalStatus,
    Region,
    RegionMap,
    Settlement,
    Side,
    UnitType,
)

INITIAL_COMPANION_IDS = [
    CharacterID.GANDALF_GREY,
    CharacterID.STRIDER,
    CharacterID.GIMLI,
    CharacterID.LEGOLAS,
    CharacterID.BOROMIR,
    CharacterID.MERRY,
    CharacterID.PIPPIN,
]

INITIAL_GUIDE_ID = CharacterID.GANDALF_GREY
INITIAL_FELLOWSHIP_LOCATION = "Rivendell"

INITIAL_REINFORCEMENTS = {
    Nation.DWARVES: [2, 3, 3],
    Nation.ELVES: [2, 4, 0],
    Nation.GONDOR: [6, 4, 3],
    Nation.NORTH: [6, 4, 3],
    Nation.ROHAN: [6, 4, 3],
    Nation.ISENGARD: [6, 5],
    Nation.SAURON: [8, 4, 4],
    Nation.SOUTHRON: [10, 3],
}


def init_fellowship() -> Fellowship:
    initial_companions = {}
    with open("data/characters.csv", newline="", encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter="|")
        for name, level, leadership in reader:
            if CharacterID[name] in INITIAL_COMPANION_IDS:
                companion = Companion(CharacterID[name], int(level), int(leadership))
                initial_companions[companion.name] = companion
    guide = initial_companions[INITIAL_GUIDE_ID]
    return Fellowship(initial_companions, guide)


def init_politics() -> dict[Nation, PoliticalStatus]:
    politics = {}
    with open("data/politics.csv", newline="", encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter="|")
        for nation, disposition, active in reader:
            politics[Nation[nation]] = PoliticalStatus(
                int(disposition), active == "active"
            )
    return politics


def init_deck(side: Side, categories: set[CardCategory]) -> deque[Card]:
    deck: deque[Card] = deque()
    with open("data/cards.csv", newline="", encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter="|")
        for event, combat, side_str, category_str in reader:
            if Side[side_str] == side and CardCategory[category_str] in categories:
                card = Card(event, combat, Side[side_str], CardCategory[category_str])
                deck.append(card)
    shuffle(deck)
    return deck


def init_region_map() -> RegionMap:
    regions: RegionMap = RegionMap()
    neighbors: dict[str, list[str]] = {}
    with open("data/worldmap.csv", newline="", encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter="|")
        for (
            name,
            neighbor_str,
            nation_str,
            settlement_str,
            regulars_str,
            elites_str,
            leaders_str,
        ) in reader:
            nation = None if nation_str == "None" else Nation[nation_str.upper()]
            settlement = (
                None if settlement_str == "None" else Settlement[settlement_str.upper()]
            )
            region = Region(name, [], nation, settlement, army=None)
            region.army = init_army(
                int(regulars_str), int(elites_str), int(leaders_str), nation, region
            )
            neighbors[name] = neighbor_str.split(",")
            regions.insert(region)
    for name, region in regions.regions_by_name.items():
        region.neighbors = [regions.with_name(neighbor) for neighbor in neighbors[name]]
    return regions


def init_army(
    regulars: int, elites: int, leaders: int, nation: Optional[Nation], region: Region
) -> Optional[Army]:
    army = None
    if regulars > 0 or elites > 0 or leaders > 0:
        # This only occurs in Osgiliath - which has Gondor units.
        nation = Nation.GONDOR if nation is None else nation
        army = Army(
            Side.FREE if nation in NATION_SIDE[Side.FREE] else Side.SHADOW, region
        )
        for _ in range(regulars):
            army.units.append(ArmyUnit(UnitType.REGULAR, nation))
        for _ in range(elites):
            army.units.append(ArmyUnit(UnitType.ELITE, nation))
        for _ in range(leaders):
            army.units.append(ArmyUnit(UnitType.LEADER, nation))
    return army


def init_player(side: Side) -> "PlayerState":
    return PlayerState(
        Agent(random_strategy),
        side,
        init_deck(side, {CardCategory.CHARACTER}),
        init_deck(side, {CardCategory.ARMY, CardCategory.MUSTER}),
        4 if side == Side.FREE else 7,
    )


@dataclass
class PlayerState:  # pylint: disable=too-many-instance-attributes
    agent: Agent
    side: Side
    character_deck: deque[Card]
    strategy_deck: deque[Card]
    max_dice: int

    dice: Counter[DieResult] = field(default_factory=Counter)
    hand: list[Card] = field(default_factory=list)
    victory_points: int = 0

    def dice_count(self) -> int:
        # TODO This can be player.dice.total() when mypy supports python 3.10
        return sum(self.dice.values())


@dataclass
class GameState:  # pylint: disable=too-many-instance-attributes
    regions: RegionMap = field(default_factory=init_region_map)
    reinforcements: dict[Nation, list[int]] = field(
        default_factory=lambda: deepcopy(INITIAL_REINFORCEMENTS)
    )

    fellowship: Fellowship = field(default_factory=init_fellowship)
    elven_rings: ElvenRings = field(default_factory=ElvenRings)
    politics: dict[Nation, PoliticalStatus] = field(default_factory=init_politics)

    free_player: PlayerState = field(default_factory=lambda: init_player(Side.FREE))
    shadow_player: PlayerState = field(default_factory=lambda: init_player(Side.SHADOW))
    players: tuple[PlayerState, PlayerState] = field(init=False)

    hunt_box_eyes: int = 0
    hunt_box_character: int = 0

    characters_mustered: set[CharacterID] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.fellowship.location = self.regions.with_name(INITIAL_FELLOWSHIP_LOCATION)
        self.players = self.free_player, self.shadow_player
