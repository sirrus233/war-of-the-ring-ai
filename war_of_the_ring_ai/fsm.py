from collections import defaultdict
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, Generic, Optional, Type, TypeAlias, TypeVar, cast

# General use type vars
T = TypeVar("T")
U = TypeVar("U")

# StateMachine type vars
Tmodel = TypeVar("Tmodel", bound=Enum)
Tout = TypeVar("Tout")
Tcontext = TypeVar("Tcontext")


class TransitionType(Enum):
    FIRE = auto()
    PUSH = auto()


TransitionAction: TypeAlias = Callable[[T], U]
TransitionGuard: TypeAlias = Callable[[T], bool]


class StateMachine(Generic[Tmodel, Tout, Tcontext]):
    @dataclass(frozen=True)
    class Transition(Generic[T]):
        type: TransitionType
        start: Tmodel
        end: Tmodel
        guard: TransitionGuard[T] = lambda _: True
        action: Optional[]

    # TODO Docs
    TransitionsMapping: TypeAlias = dict[Enum, list[Transition[Any]]]
    # Current Hierarchical State, Context Vars, Next State Input
    # TODO Docs
    StateContext: TypeAlias = tuple[list[Enum], T, U]

    def __init__(self, initial: Enum, context: Tcontext = None) -> None:
        self.state: list[Enum] = [initial]
        self.final_state: list[Enum] = []
        self.transitions: StateMachine.TransitionsMapping = defaultdict(list)

    @property
    def current_state(self) -> Enum:
        return self.state[-1]

    def add_state(self, state: Enum, final: Optional[bool] = False):

        pass

    def add_transition(
        self,
        transition_type: TransitionType,
        start: State[Any, T],
        end: State[T, Any],
        guard: TransitionGuard[T] = lambda _: True,
    ) -> None:
        transition = StateMachine.Transition[T](transition_type, start, end, guard)
        self.transitions[start].append(transition)

    def next_state(self, payload: Any) -> None:
        transitions = self.transitions[self.current_state]

        valid_transitions = [
            transition for transition in transitions if transition.guard(payload)
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

    def start(self) -> Tout:
        payload = self.initial_payload

        while self.current_state is not self.final_state:
            payload = self.current_state(payload)
            self.next_state(payload)

        # Guaranteed to be in a non-null final state, which has a return type of S
        return cast(Tout, self.current_state(payload))
