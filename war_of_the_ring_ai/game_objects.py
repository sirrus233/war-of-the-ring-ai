from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from war_of_the_ring_ai.constants import (
    EYE_CORRUPTION_FLAG,
    SHELOB_CORRUPTION_FLAG,
    CardType,
    CharacterID,
    CharacterType,
    Nation,
    Settlement,
    Side,
    UnitRank,
)


@dataclass
class Placeable:
    location: Region


@dataclass
class ArmyUnit(Placeable):
    rank: UnitRank
    nation: Nation

    def is_nazgul(self) -> bool:
        return self.rank == UnitRank.LEADER and self.nation == Nation.SAURON

    def is_unit(self) -> bool:
        return self.rank in (UnitRank.REGULAR, UnitRank.ELITE)


@dataclass
class Character(Placeable):
    id: CharacterID
    type: CharacterType
    level: int
    leadership: int

    def __repr__(self) -> str:
        return f"{self.id.name} ({self.location.name})"


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
    type: CardType

    def __repr__(self) -> str:
        return f"{self.type.name[0]}|{self.event_name}|{self.combat_name}"


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
