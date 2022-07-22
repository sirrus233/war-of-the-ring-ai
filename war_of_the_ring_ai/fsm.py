from __future__ import annotations

from dataclasses import Field, dataclass, field
from enum import Enum
from typing import (
    Any,
    Callable,
    Generic,
    Optional,
    Protocol,
    Sequence,
    Type,
    TypeAlias,
    TypeVar,
)

StateId: TypeAlias = Enum | str
EventId: TypeAlias = str

C = TypeVar("C")
E = TypeVar("E", bound="Event")


class Event(Protocol):  # pylint: disable=too-few-public-methods
    __dataclass_fields__: dict[str, Field[Any]]


@dataclass(frozen=True, kw_only=True)
class EventlessTransition(Generic[C]):
    target: Optional[StateId] = None
    guard: Callable[[C], bool] = lambda ctx: True
    action: Callable[[C], None] = lambda ctx: None


@dataclass(frozen=True, kw_only=True)
class Transition(Generic[C, E]):
    event: Type[E]
    target: Optional[StateId] = None
    guard: Callable[[C, E], bool] = lambda ctx, event: True
    action: Callable[[C, E], None] = lambda ctx, event: None


@dataclass(frozen=True)
class State(Generic[C, E]):
    on: list[Transition[C, E]] = field(default_factory=list)
    entry: list[Callable[[C], None]] = field(default_factory=list)
    exit: list[Callable[[C], None]] = field(default_factory=list)
    always: list[EventlessTransition[C]] = field(default_factory=list)


class StateMachine(Generic[C, E]):
    def __init__(
        self,
        context: C,
        initial_state: StateId,
        final_states: Optional[Sequence[StateId]] = None,
    ) -> None:
        if final_states is None:
            final_states = []

        self._running = False
        self._context = context
        self._current_state_id = self._normalize_state_id(initial_state)
        self._final_states = [self._normalize_state_id(state) for state in final_states]
        self._states: dict[str, State[C, E]] = {}

    @property
    def current_state(self) -> State[C, E]:
        try:
            return self._states[self._current_state_id]
        except KeyError as e:
            raise RuntimeError(
                f"No configuration for state: {self._current_state_id}."
            ) from e

    def _normalize_state_id(self, state_id: StateId) -> str:
        return state_id if isinstance(state_id, str) else state_id.name

    def add_state(self, state_id: StateId, state: State[C, E]) -> None:
        self._states[self._normalize_state_id(state_id)] = state

    def add_states(self, states: dict[StateId, State[C, E]]) -> None:
        for state_id, state in states.items():
            self.add_state(state_id, state)

    def _change_state(self, target: StateId) -> None:
        for exit_action in self.current_state.exit:
            exit_action(self._context)
        self._current_state_id = self._normalize_state_id(target)
        for entry_action in self.current_state.entry:
            entry_action(self._context)
        self._process_eventless_transitions()

    def _process_eventless_transitions(self) -> None:
        for eventless_transition in self.current_state.always:
            if eventless_transition.guard(self._context):
                eventless_transition.action(self._context)
                if eventless_transition.target is not None:
                    self._change_state(eventless_transition.target)
                    break

    def send(self, event: E) -> None:
        if not self._running:
            raise RuntimeError(
                "State machine must be started before it can recieve events."
            )

        event_transition = next(
            (
                transition
                for transition in self.current_state.on
                if isinstance(event, transition.event)
                and transition.guard(self._context, event)
            ),
            None,
        )

        if event_transition:
            event_transition.action(self._context, event)
            if event_transition.target is None:
                self._process_eventless_transitions()
            else:
                self._change_state(event_transition.target)

    def start(self) -> None:
        if self._running:
            raise RuntimeError("Attempted to start a running state machine.")

        self._running = True

        for entry_action in self.current_state.entry:
            entry_action(self._context)
        self._process_eventless_transitions()
