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
