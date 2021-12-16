import random
from dataclasses import dataclass, field
from typing import Any

from war_of_the_ring_ai.game_objects import Card, Companion, Region


@dataclass
class Request:
    options: Any = field(init=False)


@dataclass
class Discard(Request):
    hand: list[Card]

    def __post_init__(self) -> None:
        self.options: list[Card] = self.hand


@dataclass
class ChangeGuide(Request):
    fellowship: list[Companion]

    def __post_init__(self) -> None:
        max_level = max(companion.level for companion in self.fellowship)
        self.options: list[Companion] = [
            companion for companion in self.fellowship if companion.level == max_level
        ]


@dataclass
class DeclareFellowship(Request):
    def __post_init__(self) -> None:
        self.options: list[bool] = [True, False]


@dataclass
class DeclareFellowshipLocation(Request):
    location: Region
    progress: int

    def __post_init__(self) -> None:
        self.options: list[Region] = list(
            self.location.reachable_regions(self.progress)
        )


@dataclass
class EnterMordor(Request):
    def __post_init__(self) -> None:
        self.options: list[bool] = [True, False]


@dataclass
class HuntAllocation(Request):
    min_allocation: int
    unused_dice: int
    companions: int

    def __post_init__(self) -> None:
        max_allocation = min(self.companions, self.unused_dice)
        self.options: list[int] = list(range(self.min_allocation, max_allocation + 1))


def handler(request: Request) -> Any:
    # TODO Temporary handler
    choice = random.choice(request.options)
    print(f"{type(request).__name__}: {choice}")
    return choice
