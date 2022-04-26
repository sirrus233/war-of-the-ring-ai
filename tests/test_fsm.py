from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterable, TypeVar

import pytest

from war_of_the_ring_ai.fsm import (
    EmptyEvent,
    Event,
    StateMachine,
    Transition,
    TransitionType,
)


@dataclass
class GameContext:
    turn: int = 1
    score: int = 0
    pause_count: int = 0


###
# Action and Guard functions
###
def incr_turn(context: GameContext) -> None:
    context.turn += 1


def incr_pause(context: GameContext) -> None:
    context.pause_count += 1


def roll_die(context: GameContext, roll: int) -> None:
    context.score += roll


def is_game_over(context: GameContext, _param: None) -> bool:
    return context.score > 20


###
# States
###
class State(Enum):
    TURN_START = auto()
    COMPUTE_SCORE = auto()
    GAME_OVER = auto()
    PAUSED = auto()


###
# Events
###


@dataclass(frozen=True)
class Next(EmptyEvent):
    ...


@dataclass(frozen=True)
class Roll(Event[int]):
    ...


@dataclass(frozen=True)
class Pause(EmptyEvent):
    ...


# This event has an associated transition, but is never sent. When the state machine
# receives an event it should check if this transition should be followed before
# moving on to the next transition in the list.
@dataclass(frozen=True)
class UncommonEvent(EmptyEvent):
    ...


# This event is sent to the state machine, but has no associated transition. Such
# events should be ignored.
@dataclass(frozen=True)
class UnmodeledEvent(EmptyEvent):
    ...


@pytest.fixture(name="machine")
def fixture_state_machine() -> Iterable[StateMachine[State, GameContext]]:
    T = TypeVar("T")

    @dataclass(frozen=True)
    class GameTransition(Transition[State, GameContext, T]):
        ...

    machine = StateMachine(
        State,
        GameContext(),
        initial=State.TURN_START,
        final=[State.GAME_OVER],
    )

    machine.add_entry_action(State.TURN_START, incr_turn)
    machine.add_transition(
        GameTransition[int](
            Roll,
            TransitionType.FIRE,
            State.TURN_START,
            State.COMPUTE_SCORE,
            action=roll_die,
        ),
    )
    machine.add_transition(
        GameTransition[None](
            Pause, TransitionType.PUSH, State.TURN_START, State.PAUSED
        ),
    )

    machine.add_transition(
        GameTransition[None](
            UncommonEvent, TransitionType.FIRE, State.COMPUTE_SCORE, State.GAME_OVER
        ),
    )
    machine.add_transition(
        GameTransition[None](
            Next,
            TransitionType.FIRE,
            State.COMPUTE_SCORE,
            State.GAME_OVER,
            guard=is_game_over,
        )
    )
    machine.add_transition(
        GameTransition[None](
            Next, TransitionType.FIRE, State.COMPUTE_SCORE, State.TURN_START
        ),
    )
    machine.add_transition(
        GameTransition[None](
            Pause, TransitionType.PUSH, State.COMPUTE_SCORE, State.PAUSED
        ),
    )

    machine.add_exit_action(State.PAUSED, incr_pause)
    machine.add_transition(
        GameTransition[None](Pause, TransitionType.POP, State.PAUSED)
    )

    yield machine


def test_cannot_construct_non_parameterized_transition(
    machine: StateMachine[State, GameContext]
) -> None:
    with pytest.raises(ValueError):
        machine.add_transition(Transition(Next, TransitionType.FIRE, State.TURN_START))


@pytest.mark.parametrize(
    "transition_type", [t for t in TransitionType if t is not TransitionType.POP]
)
def test_cannot_construct_invalid_transition(
    machine: StateMachine[State, GameContext], transition_type: TransitionType
) -> None:
    with pytest.raises(ValueError):
        T = TypeVar("T")

        @dataclass(frozen=True)
        class GameTransition(Transition[State, GameContext, T]):
            ...

        machine.add_transition(GameTransition(Next, transition_type, State.TURN_START))


def test_only_sent_event_causes_transition(
    machine: StateMachine[State, GameContext]
) -> None:
    listener = machine.start()
    listener.send(Roll(3))
    listener.send(Next())
    assert machine.current_state() is State.TURN_START


def test_unmodeled_events_are_ignored(
    machine: StateMachine[State, GameContext]
) -> None:
    listener = machine.start()
    listener.send(UnmodeledEvent())
    assert machine.current_state() is State.TURN_START


def test_exit_actions_fire(machine: StateMachine[State, GameContext]) -> None:
    listener = machine.start()
    listener.send(Pause())
    assert machine.context.pause_count == 0
    listener.send(Pause())
    assert machine.context.pause_count == 1


def test_hierarchical_state(machine: StateMachine[State, GameContext]) -> None:
    listener = machine.start()
    assert machine.current_state() is State.TURN_START
    listener.send(Pause())
    assert machine.current_state() is State.PAUSED
    listener.send(Pause())
    assert machine.current_state() is State.TURN_START
    listener.send(Roll(3))
    assert machine.current_state() is State.COMPUTE_SCORE
    listener.send(Pause())
    assert machine.current_state() is State.PAUSED
    listener.send(Pause())
    assert machine.current_state() is State.COMPUTE_SCORE


def test_e2e(machine: StateMachine[State, GameContext]) -> None:
    listener = machine.start()

    while True:
        try:
            listener.send(Roll(3))
            listener.send(Next())
        except StopIteration:
            break

    assert machine.current_state() is State.GAME_OVER
    assert machine.context.score == 21
    assert machine.context.turn == 7
