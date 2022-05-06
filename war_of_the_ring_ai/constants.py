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


NATIONS = {
    Side.FREE: (
        Nation.ELVES,
        Nation.DWARVES,
        Nation.NORTH,
        Nation.GONDOR,
        Nation.ROHAN,
    ),
    Side.SHADOW: (Nation.SAURON, Nation.ISENGARD, Nation.SOUTHRON),
}

ACTION_DIE = {
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


HEROES = {
    Side.FREE: (CharacterID.GANDALF_WHITE, CharacterID.ARAGORN),
    Side.SHADOW: (
        CharacterID.SARUMAN,
        CharacterID.WITCH_KING,
        CharacterID.MOUTH_OF_SAURON,
    ),
}


class Action(Enum):
    SKIP = auto()
    DRAW_CHARACTER_EVENT = auto()
    DRAW_STRATEGY_EVENT = auto()
    PLAY_CHARACTER_EVENT = auto()
    PLAY_ARMY_EVENT = auto()
    PLAY_MUSTER_EVENT = auto()
    DIPLOMACY = auto()
    MUSTER_UNITS = auto()
    MUSTER_SARUMAN = auto()
    MUSTER_WITCH_KING = auto()
    MUSTER_MOUTH_OF_SAURON = auto()
    MOVE_ARMIES = auto()
    ATTACK = auto()
    LEADER_MOVE = auto()
    LEADER_ATTACK = auto()
    MOVE_FELLOWSHIP = auto()
    HIDE_FELLOWSHIP = auto()
    SEPARATE_COMPANIONS = auto()
    MOVE_COMPANIONS = auto()
    MOVE_MINIONS = auto()
    MUSTER_GANDALF = auto()
    MUSTER_ARAGORN = auto()


ACTIONS = {
    DieResult.CHARACTER: (
        Action.SKIP,
        Action.LEADER_MOVE,
        Action.LEADER_ATTACK,
        Action.MOVE_FELLOWSHIP,
        Action.HIDE_FELLOWSHIP,
        Action.SEPARATE_COMPANIONS,
        Action.MOVE_COMPANIONS,
        Action.MOVE_MINIONS,
        Action.PLAY_CHARACTER_EVENT,
    ),
    DieResult.ARMY: (
        Action.SKIP,
        Action.MOVE_ARMIES,
        Action.ATTACK,
        Action.PLAY_ARMY_EVENT,
    ),
    DieResult.MUSTER: (
        Action.SKIP,
        Action.DIPLOMACY,
        Action.MUSTER_UNITS,
        Action.MUSTER_SARUMAN,
        Action.MUSTER_WITCH_KING,
        Action.MUSTER_MOUTH_OF_SAURON,
        Action.PLAY_MUSTER_EVENT,
    ),
    DieResult.HYBRID: (
        Action.SKIP,
        Action.MOVE_ARMIES,
        Action.ATTACK,
        Action.PLAY_ARMY_EVENT,
        Action.DIPLOMACY,
        Action.MUSTER_UNITS,
        Action.MUSTER_SARUMAN,
        Action.MUSTER_WITCH_KING,
        Action.MUSTER_MOUTH_OF_SAURON,
        Action.PLAY_MUSTER_EVENT,
    ),
    DieResult.PALANTIR: (
        Action.SKIP,
        Action.DRAW_CHARACTER_EVENT,
        Action.DRAW_STRATEGY_EVENT,
        Action.PLAY_CHARACTER_EVENT,
        Action.PLAY_ARMY_EVENT,
        Action.PLAY_MUSTER_EVENT,
    ),
    DieResult.WILL: (
        Action.SKIP,
        Action.MUSTER_GANDALF,
        Action.MUSTER_ARAGORN,
        Action.MOVE_FELLOWSHIP,
        Action.HIDE_FELLOWSHIP,
        Action.SEPARATE_COMPANIONS,
        Action.MOVE_COMPANIONS,
        Action.PLAY_CHARACTER_EVENT,
        Action.MOVE_ARMIES,
        Action.ATTACK,
        Action.PLAY_ARMY_EVENT,
        Action.DIPLOMACY,
        Action.MUSTER_UNITS,
        Action.PLAY_MUSTER_EVENT,
        Action.DRAW_CHARACTER_EVENT,
        Action.DRAW_STRATEGY_EVENT,
    ),
}

INITIAL_GUIDE_ID = CharacterID.GANDALF_GREY
FELLOWSHIP_START = "Rivendell"
MORDOR_ENTRANCES = ("Morannon", "Minas Morgul")
GANDALF_LOCATION = "Fangorn"
SARUMAN_LOCATION = "Orthanc"

EYE_CORRUPTION_FLAG = 100
SHELOB_CORRUPTION_FLAG = 200

NAZGUL_LEVEL_FLAG = -1

MAX_HAND_SIZE = 6

FREE_VP_GOAL = 4
SHADOW_VP_GOAL = 10
