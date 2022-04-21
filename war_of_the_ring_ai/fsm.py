import random
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, Generic, Optional, TypeAlias, TypeVar

A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")
D = TypeVar("D")

T = TypeVar("T", covariant=True)
U = TypeVar("U", covariant=True)
U_inv = TypeVar("U_inv")
V = TypeVar("V", covariant=True)


class TransitionType(Enum):
    FIRE = auto()
    PUSH = auto()


State: TypeAlias = Callable[[T], U]  # TODO: Use a Protocol to allow variadic signature

TransitionCondition: TypeAlias = Callable[[T], bool]  # TODO Make variadic. See State.


@dataclass(frozen=True)
class Transition(Generic[T, U_inv, V]):
    type: TransitionType
    start: State[T, U_inv]
    end: State[U_inv, V]
    condition: TransitionCondition[U_inv] = lambda _: True


TransitionsMapping: TypeAlias = dict[State[T, U], list[Transition[T, U, V]]]


class StateMachine:
    def __init__(
        self,
        initial: State[A, B],
        initial_payload: Optional[A] = None,
        final: Optional[State[A, B]] = None,
    ) -> None:
        self.initial_payload = initial_payload
        self.state = [initial]
        self.final_state = final
        self.transitions: TransitionsMapping[T, U, V] = defaultdict(list)

    def add_transition(self, transition: Transition[T, U, V]) -> None:
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
