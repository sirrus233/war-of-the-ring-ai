from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Optional

from war_of_the_ring_ai.constants import (
    EYE_CORRUPTION_FLAG,
    NATIONS,
    SHELOB_CORRUPTION_FLAG,
    CardType,
    CharacterID,
    Nation,
    Settlement,
    Side,
    UnitRank,
)


@dataclass(frozen=True)
class Region:
    name: str
    nation: Optional[Nation] = None
    settlement: Optional[Settlement] = None
    is_fortification: bool = False

    def __repr__(self) -> str:
        return self.name


FELLOWSHIP = Region("Fellowship")
REINFORCEMENTS = Region("Reinforcements")
CASUALTIES = Region("Casualties")
MORDOR = Region("Mordor")


@dataclass
class Figure:
    location: Region

    @property
    def in_play(self) -> bool:
        return self.location not in (FELLOWSHIP, REINFORCEMENTS, CASUALTIES)


@dataclass
class ArmyUnit(Figure):
    rank: UnitRank
    nation: Nation

    @property
    def is_nazgul(self) -> bool:
        return self.rank == UnitRank.LEADER and self.nation == Nation.SAURON

    @property
    def is_unit(self) -> bool:
        return self.rank in (UnitRank.REGULAR, UnitRank.ELITE)

    @property
    def side(self) -> Side:
        return Side.FREE if self.nation in NATIONS[Side.FREE] else Side.SHADOW


@dataclass
class Character(Figure):
    id: CharacterID
    side: Side
    level: int
    leadership: int

    def __repr__(self) -> str:
        return f"{self.id.name} ({self.location.name})"

    @property
    def can_move(self) -> bool:
        return self.level > 0


@dataclass
class Army:
    units: ArmyUnitCollection
    leaders: ArmyUnitCollection
    characters: CharacterCollection

    @property
    def is_combat_army(self) -> bool:
        return any(self.units)

    @property
    def leadership(self) -> int:
        unit_leadership = sum(1 for _ in self.leaders)
        char_leadership = sum(character.leadership for character in self.characters)
        return unit_leadership + char_leadership


@dataclass(frozen=True)
class CharacterCollection:
    characters: list[Character]

    def __iter__(self) -> Iterator[Character]:
        return iter(self.characters)

    def with_id(self, id_: CharacterID) -> Character:
        return next(char for char in self.characters if char.id is id_)

    def with_ids(self, *ids: CharacterID) -> CharacterCollection:
        return CharacterCollection([char for char in self.characters if char.id in ids])

    def with_location(self, *regions: Region) -> CharacterCollection:
        return CharacterCollection(
            [char for char in self.characters if char.location in regions]
        )

    def with_side(self, side: Side) -> CharacterCollection:
        return CharacterCollection(
            [char for char in self.characters if char.side is side]
        )

    def with_level(self, level: int) -> CharacterCollection:
        return CharacterCollection(
            [char for char in self.characters if char.level == level]
        )

    def can_move(self) -> CharacterCollection:
        return CharacterCollection([char for char in self.characters if char.can_move])

    def in_play(self) -> CharacterCollection:
        return CharacterCollection([char for char in self.characters if char.in_play])


@dataclass(frozen=True)
class RegionCollection:
    regions: list[Region]

    def __iter__(self) -> Iterator[Region]:
        return iter(self.regions)

    def with_side(self, side: Side) -> RegionCollection:
        return RegionCollection(
            [region for region in self.regions if region.nation in NATIONS[side]]
        )

    def with_nation(self, *nations: Nation) -> RegionCollection:
        return RegionCollection(
            [region for region in self.regions if region.nation in nations]
        )

    def with_settlement(self, *settlements: Settlement) -> RegionCollection:
        return RegionCollection(
            [region for region in self.regions if region.settlement in settlements]
        )

    def with_any_settlement(self) -> RegionCollection:
        return RegionCollection(
            [region for region in self.regions if region.settlement is not None]
        )


@dataclass(frozen=True)
class ArmyUnitCollection:
    units: list[ArmyUnit]

    def __iter__(self) -> Iterator[ArmyUnit]:
        return iter(self.units)

    def with_side(self, side: Side) -> ArmyUnitCollection:
        return ArmyUnitCollection(
            [unit for unit in self.units if unit.nation in NATIONS[side]]
        )

    def with_location(self, *regions: Region) -> ArmyUnitCollection:
        return ArmyUnitCollection(
            [unit for unit in self.units if unit.location in regions]
        )

    def with_nation(self, *nations: Nation) -> ArmyUnitCollection:
        return ArmyUnitCollection(
            [unit for unit in self.units if unit.nation in nations]
        )

    def with_rank(self, *ranks: UnitRank) -> ArmyUnitCollection:
        return ArmyUnitCollection([unit for unit in self.units if unit.rank in ranks])

    def units_only(self) -> ArmyUnitCollection:
        return ArmyUnitCollection(
            [
                unit
                for unit in self.units
                if unit.rank in (UnitRank.REGULAR, UnitRank.ELITE)
            ]
        )

    def in_play(self) -> ArmyUnitCollection:
        return ArmyUnitCollection([unit for unit in self.units if unit.in_play])

    def nazgul(self) -> ArmyUnitCollection:
        return ArmyUnitCollection([unit for unit in self.units if unit.is_nazgul])


@dataclass(frozen=True)
class Card:
    event_name: str
    combat_name: str
    side: Side
    type: CardType

    def __repr__(self) -> str:
        return f"{self.type.name[0]}|{self.event_name}|{self.combat_name}"


@dataclass(frozen=True)
class HuntTile:
    corruption: int
    reveal: bool
    side: Optional[Side]

    @property
    def is_eye(self) -> bool:
        return self.corruption == EYE_CORRUPTION_FLAG

    @property
    def is_shelob(self) -> bool:
        return self.corruption == SHELOB_CORRUPTION_FLAG

    @property
    def is_stop(self) -> bool:
        return self.side == Side.SHADOW
