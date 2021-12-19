import csv
from collections import Counter, deque
from dataclasses import dataclass, field
from random import shuffle

from war_of_the_ring_ai.agent import Agent, random_strategy
from war_of_the_ring_ai.game_objects import (
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


def init_fellowship() -> Fellowship:
    initial_companions = []
    with open("data/characters.csv", newline="", encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter="|")
        for name, level, leadership in reader:
            if CharacterID[name] in INITIAL_COMPANION_IDS:
                companion = Companion(CharacterID[name], int(level), int(leadership))
                initial_companions.append(companion)
    guide = next(c for c in initial_companions if c.name == CharacterID.GANDALF_GREY)
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


def init_region_map() -> dict[str, Region]:
    regions: dict[str, Region] = {}
    neighbors: dict[str, list[str]] = {}
    with open("data/worldmap.csv", newline="", encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter="|")
        for name, neighbor_str, nation_str, settlement_str, _, _, _ in reader:
            nation = None if nation_str == "None" else Nation[nation_str.upper()]
            settlement = (
                None if settlement_str == "None" else Settlement[settlement_str.upper()]
            )
            regions[name] = Region(name, [], nation, settlement)
            neighbors[name] = neighbor_str.split(",")
    for name, region in regions.items():
        region.neighbors = [regions[neighbor] for neighbor in neighbors[name]]
    return regions


def init_army_map() -> dict[str, list[ArmyUnit]]:
    armies: dict[str, list[ArmyUnit]] = {}
    with open("data/worldmap.csv", newline="", encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter="|")
        for name, _, nation_str, _, regulars_str, elites_str, leaders_str in reader:
            regulars, elites, leaders = (
                int(regulars_str),
                int(elites_str),
                int(leaders_str),
            )
            if regulars > 0 or elites > 0 or leaders > 0:
                nation = (
                    # This only occurs in Osgiliath - which has Gondor units.
                    Nation.GONDOR
                    if nation_str == "None"
                    else Nation[nation_str.upper()]
                )
                army = []
                for _ in range(int(regulars)):
                    army.append(ArmyUnit(UnitType.REGULAR, nation))
                for _ in range(int(elites)):
                    army.append(ArmyUnit(UnitType.ELITE, nation))
                for _ in range(int(leaders)):
                    army.append(ArmyUnit(UnitType.LEADER, nation))
                armies[name] = army
    return armies


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


@dataclass
class GameState:  # pylint: disable=too-many-instance-attributes
    region_map: dict[str, Region] = field(default_factory=init_region_map)
    army_map: dict[str, list[ArmyUnit]] = field(default_factory=init_army_map)

    fellowship: Fellowship = field(default_factory=init_fellowship)
    elven_rings: ElvenRings = field(default_factory=ElvenRings)
    politics: dict[Nation, PoliticalStatus] = field(default_factory=init_politics)

    free_player: PlayerState = field(default_factory=lambda: init_player(Side.FREE))
    shadow_player: PlayerState = field(default_factory=lambda: init_player(Side.SHADOW))
    players: tuple[PlayerState, PlayerState] = field(init=False)

    hunt_box_eyes: int = 0
    hunt_box_character: int = 0

    def __post_init__(self) -> None:
        self.fellowship.location = self.region_map[INITIAL_FELLOWSHIP_LOCATION]
        self.players = self.free_player, self.shadow_player
