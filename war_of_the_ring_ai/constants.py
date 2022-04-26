from enum import Enum, auto


class Side(Enum):
    FREE = auto()
    SHADOW = auto()


class Nation(Enum):
    ELVES = auto()
    DWARVES = auto()
    NORTH = auto()
    ROHAN = auto()
    GONDOR = auto()
    SAURON = auto()
    ISENGARD = auto()
    SOUTHRON = auto()


class Settlement(Enum):
    TOWN = auto()
    CITY = auto()
    STRONGHOLD = auto()


class CharacterID(Enum):
    GANDALF_GREY = auto()
    STRIDER = auto()
    GIMLI = auto()
    LEGOLAS = auto()
    BOROMIR = auto()
    MERRY = auto()
    PIPPIN = auto()
    GANDALF_WHITE = auto()
    ARAGORN = auto()
    SARUMAN = auto()
    WITCH_KING = auto()
    MOUTH_OF_SAURON = auto()
    GOLLUM = auto()


class CharacterType(Enum):
    COMPANION = auto()
    MINION = auto()


class DieResult(Enum):
    CHARACTER = auto()
    ARMY = auto()
    MUSTER = auto()
    HYBRID = auto()
    PALANTIR = auto()
    EYE = auto()
    WILL = auto()


class DeckType(Enum):
    CHARACTER = auto()
    STRATEGY = auto()


class CardType(Enum):
    CHARACTER = auto()
    ARMY = auto()
    MUSTER = auto()


class UnitRank(Enum):
    REGULAR = auto()
    ELITE = auto()
    LEADER = auto()


class Casualty(Enum):
    NONE = auto()
    GUIDE = auto()
    RANDOM = auto()


class Victory(Enum):
    FPRV = auto()
    FPMV = auto()
    SPRV = auto()
    SPMV = auto()


FREE_NATIONS = (
    Nation.ELVES,
    Nation.DWARVES,
    Nation.NORTH,
    Nation.GONDOR,
    Nation.ROHAN,
)
SHADOW_NATIONS = (Nation.SAURON, Nation.ISENGARD, Nation.SOUTHRON)


FREE_ACTION_DIE = (
    DieResult.CHARACTER,
    DieResult.CHARACTER,
    DieResult.MUSTER,
    DieResult.HYBRID,
    DieResult.PALANTIR,
    DieResult.WILL,
)
SHADOW_ACTION_DIE = (
    DieResult.CHARACTER,
    DieResult.ARMY,
    DieResult.MUSTER,
    DieResult.HYBRID,
    DieResult.PALANTIR,
    DieResult.EYE,
)

FREE_HEROES = (CharacterID.GANDALF_WHITE, CharacterID.ARAGORN)
SHADOW_HEROES = (
    CharacterID.SARUMAN,
    CharacterID.WITCH_KING,
    CharacterID.MOUTH_OF_SAURON,
)

INITIAL_GUIDE_ID = CharacterID.GANDALF_GREY
FELLOWSHIP_START = "Rivendell"
MORDOR_ENTRANCES = ("Morannon", "Minas Morgul")

EYE_CORRUPTION_FLAG = 100
SHELOB_CORRUPTION_FLAG = 200

NAZGUL_LEVEL_FLAG = -1

MAX_HAND_SIZE = 6

FREE_VP_GOAL = 4
SHADOW_VP_GOAL = 10
