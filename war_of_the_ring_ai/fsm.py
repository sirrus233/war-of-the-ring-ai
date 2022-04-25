from collections import defaultdict
from dataclasses import dataclass
from enum import Enum, auto
from typing import (
    Any,
    Callable,
    Generator,
    Generic,
    Iterable,
    Optional,
    TypeAlias,
    TypeVar,
)

# General use type vars
T = TypeVar("T")
U = TypeVar("U")

# StateMachine type vars
Tstate = TypeVar("Tstate", bound=Enum)
Tevent = TypeVar("Tevent", bound=Enum)
Tpayload = TypeVar("Tpayload")
Tpayloadtype = TypeVar("Tpayloadtype")
Tcontext = TypeVar("Tcontext")

Tout = TypeVar("Tout")


@dataclass(frozen=True)
class Event(Generic[Tevent, Tpayloadtype]):
    id: Tevent
    payload: Optional[Tpayloadtype] = None


class TransitionType(Enum):
    FIRE = auto()
    PUSH = auto()


TransitionGuard: TypeAlias = Callable[[Tstate, Tcontext, Tpayload], bool]
TransitionAction: TypeAlias = Callable[[Tstate, Tcontext, Tpayload], None]


@dataclass(frozen=True)
class Transition(Generic[Tevent, Tpayload, Tstate, Tcontext]):
    event: Tevent
    type: TransitionType
    next: Tstate
    guard: TransitionGuard[Tstate, Tcontext, Tpayload]
    action: TransitionAction[Tstate, Tcontext, Tpayload]


class StateMachine(Generic[Tstate, Tevent, Tcontext]):
    def __init__(
        self, initial: Tstate, context: Tcontext, final: Iterable[Tstate] = ()
    ) -> None:
        self.state = [initial]
        self.final_states = set(final)
        self.context = context
        # Nested mapping of State -> Event -> Seq(Transition)
        self.transitions: defaultdict[
            Tstate, defaultdict[Tevent, list[Transition[Tevent, Any, Tstate, Tcontext]]]
        ] = defaultdict(lambda: defaultdict(list))

    @property
    def current_state(self) -> Tstate:
        return self.state[-1]

    def add_transition(
        self,
        start: Tstate,
        event: Tevent,
        transition_type: TransitionType,
        next_state: Tstate,
        guard: Optional[TransitionGuard[Tstate, Tcontext, Tpayload]] = None,
        action: Optional[TransitionAction[Tstate, Tcontext, Tpayload]] = None,
    ) -> None:
        def default_guard(_1: Tstate, _2: Tcontext, _3: Tpayload) -> bool:
            return True

        def default_action(_1: Tstate, _2: Tcontext, _3: Tpayload) -> None:
            return None

        if guard is None:
            guard = default_guard

        if action is None:
            action = default_action

        transition = Transition(event, transition_type, next_state, guard, action)
        self.transitions[start][transition.event].append(transition)

    def _handle(self, event: Event[Tevent, Any]) -> None:
        transitions = self.transitions[self.current_state][event.id]
        for transition in transitions:
            if transition.guard(self.current_state, self.context, event.payload):
                transition.action(self.current_state, self.context, event.payload)
                match transition.type:
                    case TransitionType.FIRE:
                        self.state.pop()
                        self.state.append(transition.next)
                    case TransitionType.PUSH:
                        self.state.append(transition.next)
                break

    def start(self) -> Generator[None, Event[Tevent, Any], Tstate]:
        while self.current_state not in self.final_states:
            event = yield
            self._handle(event)

        return self.current_state
