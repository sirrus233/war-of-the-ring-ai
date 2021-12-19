from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Side(Enum):
    FREE = 0
    SHADOW = 1


class Nation(Enum):
    ELVES = 0
    DWARVES = 1
    NORTH = 2
    ROHAN = 3
    GONDOR = 4
    SAURON = 5
    ISENGARD = 6
    SOUTHRON = 7


class Settlement(Enum):
    TOWN = 0
    CITY = 1
    STRONGHOLD = 2
    FORTIFICATION = 3


class CharacterID(Enum):
    GANDALF_GREY = 0
    STRIDER = 1
    GIMLI = 2
    LEGOLAS = 3
    BOROMIR = 4
    MERRY = 5
    PIPPIN = 6
    GANDALF_WHITE = 7
    ARAGORN = 8
    SARUMAN = 9
    WITCH_KING = 10
    MOUTH_OF_SAURON = 11


class DieResult(Enum):
    CHARACTER = 0
    ARMY = 1
    MUSTER = 2
    HYBRID = 3
    PALANTIR = 4
    EYE = 5
    WILL = 6


class CardCategory(Enum):
    CHARACTER = 0
    ARMY = 1
    MUSTER = 2


class UnitType(Enum):
    REGULAR = 0
    ELITE = 1
    LEADER = 2


class Action(Enum):
    # Any die can be thrown away without taking an action
    SKIP = 0

    # Palantir
    DRAW_CHARACTER_EVENT = 1
    DRAW_STRATEGY_EVENT = 2
    PLAY_CHARACTER_EVENT = 3
    PLAY_ARMY_EVENT = 4
    PLAY_MUSTER_EVENT = 5

    # Muster
    DIPLOMACY = 6
    MUSTER_ELITE = 7
    MUSTER_REGULAR_REGULAR = 8
    MUSTER_REGULAR_LEADER = 9
    MUSTER_LEADER_LEADER = 10
    MUSTER_SARUMAN = 11
    MUSTER_WITCH_KING = 12
    MUSTER_MOUTH_OF_SAURON = 13

    # Army
    MOVE_ARMIES = 14
    ATTACK = 15

    # Character
    LEADER_MOVE = 16
    LEADER_ATTACK = 17
    MOVE_FELLOWSHIP = 18
    HIDE_FELLOWSHIP = 19
    SEPARATE_COMPANIONS = 20
    MOVE_COMPANIONS = 21
    MOVE_MINIONS = 22


NATION_SIDE = {
    Side.FREE: (
        Nation.ELVES,
        Nation.DWARVES,
        Nation.NORTH,
        Nation.GONDOR,
        Nation.ROHAN,
    ),
    Side.SHADOW: (Nation.SAURON, Nation.ISENGARD, Nation.SOUTHRON),
}

DIE = {
    Side.FREE: (
        DieResult.CHARACTER,
        DieResult.CHARACTER,
        DieResult.MUSTER,
        DieResult.HYBRID,
        DieResult.PALANTIR,
        DieResult.WILL,
    ),
    Side.SHADOW: (
        DieResult.CHARACTER,
        DieResult.ARMY,
        DieResult.MUSTER,
        DieResult.HYBRID,
        DieResult.PALANTIR,
        DieResult.EYE,
    ),
}


@dataclass
class Region:
    name: str
    neighbors: list["Region"] = field(repr=False)
    nation: Optional[Nation] = None
    settlement: Optional[Settlement] = None
    is_unconquered: bool = field(default=True)

    def __hash__(self) -> int:
        return hash(self.name)

    def can_heal_fellowship(self) -> bool:
        return (
            self.nation in NATION_SIDE[Side.FREE]
            and self.settlement in (Settlement.CITY, Settlement.STRONGHOLD)
            and self.is_unconquered
        )

    def can_enter_mordor(self) -> bool:
        return self.name in ("Morannon", "Minas Morgul")

    def reachable_regions(self, distance: int) -> set["Region"]:
        return self._reachable_region_search(distance, {self}, {self})

    def _reachable_region_search(
        self, distance: int, search: set["Region"], reached: set["Region"]
    ) -> set["Region"]:
        if distance == 0:
            return reached

        next_search = {
            neighbor
            for region in search
            for neighbor in region.neighbors
            if neighbor not in reached
        }
        reached |= next_search
        return self._reachable_region_search(distance - 1, next_search, reached)


@dataclass
class Character:
    name: CharacterID
    level: int
    leadership: int


@dataclass
class Companion(Character):
    pass


@dataclass
class Minion(Character):
    pass


@dataclass
class Fellowship:
    companions: list[Companion]
    guide: Companion
    location: Optional[Region] = None
    revealed: bool = False
    progress: int = 0
    corruption: int = 0


@dataclass
class ElvenRings:
    free: int = 3
    shadow: int = 0


@dataclass
class PoliticalStatus:
    disposition: int
    active: bool


@dataclass
class Card:
    event_name: str
    combat_name: str
    side: Side
    category: CardCategory


@dataclass(frozen=True)
class ArmyUnit:
    type: UnitType
    nation: Nation


@dataclass
class Army:
    units: list[ArmyUnit] = field(default_factory=list)
    characters: list[Character] = field(default_factory=list)
