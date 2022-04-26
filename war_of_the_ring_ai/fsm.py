from __future__ import annotations

from dataclasses import dataclass
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
E = TypeVar("E", bound=Enum)


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
EntryAction: TypeAlias = Callable[[T], None]
ExitAction: TypeAlias = Callable[[T], None]


@dataclass(frozen=True)
class Transition(Generic[E, T, U]):
    event: Type[Event[U]]
    type: TransitionType
    next: Optional[E] = None
    guard: TransitionGuard[T, U] = lambda _context, _param: True
    action: TransitionAction[T, U] = lambda _context, _param: None


class StateMachine(Generic[E, T]):
    def __init__(
        self, model: Type[E], context: T, initial: E, final: Iterable[E] = ()
    ) -> None:
        self.context = context
        self.state = [initial]
        self.final_states = final

        self.entry_actions: dict[E, list[EntryAction[T]]] = {
            state: [] for state in model
        }
        self.exit_actions: dict[E, list[ExitAction[T]]] = {state: [] for state in model}
        self.transitions: dict[E, list[Transition[E, T, Any]]] = {
            state: [] for state in model
        }

    def current_state(self) -> E:
        return self.state[-1]

    def add_transition(self, state: E, transition: Transition[E, T, Any]) -> None:
        if transition.next is None and transition.type is not TransitionType.POP:
            raise ValueError(
                "Transition must define a next state unless TransitionType is POP."
            )
        self.transitions[state].append(transition)

    def add_entry_action(self, state: E, action: EntryAction[T]) -> None:
        self.entry_actions[state].append(action)

    def add_exit_action(self, state: E, action: ExitAction[T]) -> None:
        self.exit_actions[state].append(action)

    def perform_entry_actions(self, state: E) -> None:
        for action in self.entry_actions[state]:
            action(self.context)

    def perform_exit_actions(self, state: E) -> None:
        for action in self.exit_actions[state]:
            action(self.context)

    def _handle_event(self, event: Event[Any]) -> None:
        for transition in self.transitions[self.current_state()]:
            if isinstance(event, transition.event):
                if transition.guard(self.context, event.payload):
                    transition.action(self.context, event.payload)
                    self.perform_exit_actions(self.current_state())
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
                    self.perform_entry_actions(self.current_state())
                    return

    def _start(self) -> Generator[None, Event[Any], E]:
        while self.current_state() not in self.final_states:
            event = yield
            self._handle_event(event)

        return self.current_state()

    def start(self) -> Generator[None, Event[Any], E]:
        machine = self._start()
        next(machine)  # Prime the generator
        return machine
