import random
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, Generic, Optional, Protocol, TypeAlias, TypeVar

T = TypeVar("T")
T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")
T4 = TypeVar("T4")


class TransitionType(Enum):
    FIRE = auto()
    PUSH = auto()


State: TypeAlias = Callable[[T1], T2]

TransitionCondition: TypeAlias = Callable[[T], bool]


@dataclass(frozen=True)
class Transition(Generic[T1, T2, T3]):
    type: TransitionType
    start: State[T1, T2]
    end: State[T2, T3]
    condition: TransitionCondition[T2] = lambda _: True


TransitionsMapping: TypeAlias = dict[State[T1, T2], list[Transition[T1, T2, T3]]]


class TransitionsMappingP(Protocol):
    def __getitem__(self, item: State[T1, T2]) -> list[Transition[T1, T2, object]]:
        ...


class StateMachine:
    def __init__(
        self,
        initial: State[T1, T2],
        initial_payload: Optional[T1] = None,
        final: Optional[State[T3, T4]] = None,
    ) -> None:
        self.initial_payload = initial_payload
        self.state = [initial]
        self.final_state = final
        self.transitions: TransitionsMapping[Any, Any, Any] = defaultdict(list)

    def add_transition(self, transition: Transition[Any, Any, Any]) -> None:
        self.transitions[transition.start].append(transition)

    @property
    def current_state(self) -> State[Any, Any]:
        return self.state[-1]

    def next_state(self, payload: Any) -> None:
        transitions = self.transitions[self.current_state]

        valid_transitions = [
            transition for transition in transitions if transition.condition(payload)
        ]

        if len(valid_transitions) == 0:
            raise ValueError(
                f"No valid transitions from state {self.current_state.__name__}"
            )

        if len(valid_transitions) > 1:
            raise ValueError(
                f"Multiple valid transitions from state {self.current_state.__name__}. "
                f"Transitions: {valid_transitions}"
            )

        transition = valid_transitions[0]

        match transition.type:
            case TransitionType.FIRE:
                self.state.pop()
                self.state.append(transition.end)
            case TransitionType.PUSH:
                self.state.append(transition.end)

    def start(self) -> None:
        payload = self.initial_payload
        while self.current_state is not self.final_state:
            payload = self.current_state(payload)
            self.next_state(payload)


def start_turn(payload: tuple[int, int]) -> tuple[int, int]:
    return (payload[0] + 1, payload[1])


def roll_die(payload: tuple[int, int]) -> tuple[int, int]:
    result = random.choice(list(range(1, 7)))
    print(f"rolled {result}")
    return (payload[0], payload[1] + result)


def report_score(payload: tuple[int, int]) -> int:
    print(f"Game ended on turn {payload[0]} with score {payload[1]}")
    return 0


def end_game(_: None) -> None:
    pass


def is_game_over(payload: tuple[int, bool]) -> bool:
    return payload[1] >= 20


def isnt_game_over(payload: tuple[int, int]) -> bool:
    return payload[1] < 20


Transition(TransitionType.FIRE, roll_die, start_turn, isnt_game_over)
Transition(TransitionType.FIRE, roll_die, report_score, is_game_over)
Transition(TransitionType.FIRE, report_score, end_game)

sm = StateMachine(initial=start_turn, initial_payload=(0, 0), final=end_game)
sm.add_transition(Transition(TransitionType.FIRE, start_turn, roll_die))
sm.add_transition(Transition(TransitionType.FIRE, roll_die, start_turn, isnt_game_over))
sm.add_transition(Transition(TransitionType.FIRE, roll_die, report_score, is_game_over))
sm.add_transition(Transition(TransitionType.FIRE, report_score, end_game))
sm.start()
