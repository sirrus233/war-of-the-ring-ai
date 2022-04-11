from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from war_of_the_ring_ai.constants import (
    EYE_CORRUPTION_FLAG,
    SHELOB_CORRUPTION_FLAG,
    CardCategory,
    CharacterID,
    CharacterType,
    Nation,
    Settlement,
    Side,
    UnitRank,
)


@dataclass(frozen=True)
class Placeable:
    location: Region


@dataclass(frozen=True)
class ArmyUnit(Placeable):
    rank: UnitRank
    nation: Nation

    def is_nazgul(self) -> bool:
        return self.rank == UnitRank.LEADER and self.nation == Nation.SAURON


@dataclass(frozen=True)
class Character(Placeable):
    id: CharacterID
    type: CharacterType
    level: int
    leadership: int


@dataclass(frozen=True)
class Region:
    name: str
    nation: Optional[Nation] = None
    settlement: Optional[Settlement] = None
    is_fortification: bool = False


@dataclass(frozen=True)
class Card:
    event_name: str
    combat_name: str
    side: Side
    category: CardCategory


@dataclass(frozen=True)
class HuntTile:
    corruption: int
    reveal: bool
    side: Optional[Side]

    def is_eye(self) -> bool:
        return self.corruption == EYE_CORRUPTION_FLAG

    def is_shelob(self) -> bool:
        return self.corruption == SHELOB_CORRUPTION_FLAG

    def is_stop(self) -> bool:
        return self.side == Side.SHADOW
