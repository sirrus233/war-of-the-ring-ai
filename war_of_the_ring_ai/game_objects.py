import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


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

    # Will
    MUSTER_GANDALF = 23
    MUSTER_ARAGORN = 24


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
    army: Optional["Army"] = None
    is_conquered: bool = field(default=False)

    def __hash__(self) -> int:
        return hash(self.name)

    def is_enemy_controlled(self, side: Side) -> bool:
        if self.nation is None:
            return False
        if self.nation in NATION_SIDE[side]:
            return self.is_conquered
        return not self.is_conquered

    def has_friendly_army(self, side: Side) -> bool:
        if self.army is None:
            return False
        return self.army.has_units() and self.army.side == side

    def has_enemy_army(self, side: Side) -> bool:
        if self.army is None:
            return False
        return self.army.has_units() and self.army.side != side

    def is_free(self, side: Side) -> bool:
        # A besieged stronghold is free for a player if that player controls the
        # besieging army. Otherwise, an enemy-controlled settlement is never free.
        # All other regions are free if there is no enemy army present.
        if self.is_enemy_controlled(side):
            return self.has_friendly_army(side)
        return not self.has_enemy_army(side)

    def is_free_for_movement(self, side: Side) -> bool:
        # All free regions are free for army movement. A non-free region is free for
        # movement if there are no enemy units present. In practice, this applies only
        # to enemy-controlled settlements, since any other region with no enemy units
        # is free by default.
        if self.is_free(side):
            return True
        return self.army is None or not self.army.has_units()

    def can_heal_fellowship(self) -> bool:
        return (
            self.nation in NATION_SIDE[Side.FREE]
            and self.settlement in (Settlement.CITY, Settlement.STRONGHOLD)
            and not self.is_conquered
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
class RegionMap:
    regions_by_name: dict[str, Region] = field(default_factory=dict)

    def insert(self, region: Region) -> None:
        self.regions_by_name[region.name] = region

    def with_predicate(self, predicate: Callable[[Region], bool]) -> set[Region]:
        return {region for region in self.regions_by_name.values() if predicate(region)}

    def with_name(self, name: str) -> Region:
        return self.regions_by_name[name]

    def with_side(self, side: Side) -> set[Region]:
        return self.with_predicate(
            lambda r: r.nation is not None and r.nation in NATION_SIDE[side]
        )

    def with_nation(self, nation: Nation) -> set[Region]:
        return self.with_predicate(lambda r: r.nation == nation)

    def with_army_units(self, side: Optional[Side] = None) -> set[Region]:
        if side:
            return self.with_predicate(
                lambda r: r.army is not None
                and r.army.has_units()
                and r.army.side == side
            )
        return self.with_predicate(lambda r: r.army is not None and r.army.has_units())

    def with_characters(self, side: Optional[Side] = None) -> set[Region]:
        if side:
            return self.with_predicate(
                lambda r: r.army is not None
                and r.army.has_characters()
                and r.army.side == side
            )
        return self.with_predicate(
            lambda r: r.army is not None and r.army.has_characters()
        )

    def with_character(self, character: CharacterID) -> set[Region]:
        return self.with_predicate(
            lambda r: r.army is not None and r.army.has_character(character)
        )


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
    companions: dict[CharacterID, Companion]
    guide: Companion
    location: Optional[Region] = None
    revealed: bool = False
    progress: int = 0
    corruption: int = 0

    def in_mordor(self) -> bool:
        return self.location is None


@dataclass
class ElvenRings:
    free: int = 3
    shadow: int = 0


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
    side: Side
    region: Region
    units: list[ArmyUnit] = field(default_factory=list)
    characters: list[Character] = field(default_factory=list)

    def has_units(self) -> bool:
        return len(self.units) > 0

    def has_characters(self) -> bool:
        return len(self.characters) > 0

    def has_character(self, character: CharacterID) -> bool:
        return character in {c.name for c in self.characters}

    def regulars(self) -> int:
        return sum(1 for unit in self.units if unit.type == UnitType.REGULAR)

    def elites(self) -> int:
        return sum(1 for unit in self.units if unit.type == UnitType.ELITE)

    def leaders(self) -> int:
        return sum(1 for unit in self.units if unit.type == UnitType.LEADER)

    def valid_moves(self) -> list[Region]:
        return [
            region
            for region in self.region.neighbors
            if region.is_free_for_movement(self.side)
        ]

    def valid_attacks(self) -> list[Region]:
        return [
            region
            for region in self.region.neighbors
            if region.has_enemy_army(self.side)
        ]

    def leadership(self) -> int:
        character_leadership = sum(
            character.leadership for character in self.characters
        )
        return self.leaders() + character_leadership


@dataclass
class HuntTile:
    corruption: int
    reveal: bool
    side: Optional[Side]

    def is_eye(self) -> bool:
        return self.corruption == 100

    def is_shelob(self) -> bool:
        return self.corruption == 200


@dataclass
class HuntPool:
    tiles: list[HuntTile]
    reserve: list[HuntTile] = field(default_factory=list)

    def __post_init__(self) -> None:
        random.shuffle(self.tiles)

    def draw(self) -> HuntTile:
        return self.tiles.pop()

    def enter_mordor(self) -> None:
        self.tiles.extend(self.reserve)
        self.reserve = []
        random.shuffle(self.tiles)
