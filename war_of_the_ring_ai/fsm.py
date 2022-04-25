from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    Any,
    Callable,
    Generator,
    Generic,
    Iterable,
    Optional,
    Type,
    TypeAlias,
    TypeVar,
)

T = TypeVar("T")
U = TypeVar("U")


@dataclass(frozen=True)
class Event(Generic[T]):
    payload: T


@dataclass(frozen=True)
class EmptyEvent(Event[None]):
    payload: None = None


class TransitionType(Enum):
    FIRE = auto()
    PUSH = auto()
    POP = auto()


TransitionGuard: TypeAlias = Callable[[T, U], bool]
TransitionAction: TypeAlias = Callable[[T, U], None]


@dataclass(frozen=True)
class Transition(Generic[T, U]):
    event: Type[Event[U]]
    type: TransitionType
    next: Optional[State[T]] = None
    guard: TransitionGuard[T, U] = lambda _context, _param: True
    action: TransitionAction[T, U] = lambda _context, _param: None

    def __post_init__(self) -> None:
        if self.next is None and self.type is not TransitionType.POP:
            raise ValueError(
                "Transition must define a next state unless TransitionType is POP."
            )


@dataclass(frozen=True)
class State(Generic[T]):
    transitions: list[Transition[T, Any]] = field(default_factory=list)
    on_enter: Callable[[T], None] = lambda _context: None
    on_exit: Callable[[T], None] = lambda _context: None

    def add_transition(self, transition: Transition[T, Any]) -> None:
        self.transitions.append(transition)


class StateMachine(Generic[T]):
    def __init__(
        self, context: T, initial: State[T], final: Iterable[State[T]] = ()
    ) -> None:
        self.context = context
        self.state = [initial]
        self.final_states = final

    @property
    def current_state(self) -> State[T]:
        return self.state[-1]

    def _handle(self, event: Event[Any]) -> None:
        for transition in self.current_state.transitions:
            if isinstance(event, transition.event):
                if transition.guard(self.context, event.payload):
                    transition.action(self.context, event.payload)
                    self.current_state.on_exit(self.context)
                    match transition.type:
                        case TransitionType.FIRE:
                            assert transition.next is not None
                            self.state.pop()
                            self.state.append(transition.next)
                        case TransitionType.PUSH:
                            assert transition.next is not None
                            self.state.append(transition.next)
                        case TransitionType.POP:  # pragma: no branch
                            self.state.pop()
                    self.current_state.on_enter(self.context)
                    return

    def _start(self) -> Generator[None, Event[Any], State[T]]:
        while self.current_state not in self.final_states:
            event = yield
            self._handle(event)

        return self.current_state

    def start(self) -> Generator[None, Event[Any], State[T]]:
        machine = self._start()
        next(machine)
        return machine
