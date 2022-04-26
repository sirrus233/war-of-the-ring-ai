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
class GameState(Enum):
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
def fixture_state_machine() -> Iterable[StateMachine[GameState, GameContext]]:
    T = TypeVar("T")

    @dataclass(frozen=True)
    class GameTransition(Transition[GameState, GameContext, T]):
        ...

    machine = StateMachine(
        GameState,
        GameContext(),
        initial=GameState.TURN_START,
        final=[GameState.GAME_OVER],
    )

    machine.add_entry_action(GameState.TURN_START, incr_turn)
    machine.add_transition(
        GameState.TURN_START,
        GameTransition[int](
            Roll, TransitionType.FIRE, GameState.COMPUTE_SCORE, action=roll_die
        ),
    )
    machine.add_transition(
        GameState.TURN_START,
        GameTransition[None](Pause, TransitionType.PUSH, GameState.PAUSED),
    )

    machine.add_transition(
        GameState.COMPUTE_SCORE,
        GameTransition[None](UncommonEvent, TransitionType.FIRE, GameState.GAME_OVER),
    )
    machine.add_transition(
        GameState.COMPUTE_SCORE,
        GameTransition[None](
            Next, TransitionType.FIRE, GameState.GAME_OVER, guard=is_game_over
        ),
    )
    machine.add_transition(
        GameState.COMPUTE_SCORE,
        GameTransition[None](Next, TransitionType.FIRE, GameState.TURN_START),
    )
    machine.add_transition(
        GameState.COMPUTE_SCORE,
        GameTransition[None](Pause, TransitionType.PUSH, GameState.PAUSED),
    )

    machine.add_exit_action(GameState.PAUSED, incr_pause)
    machine.add_transition(
        GameState.PAUSED, GameTransition[None](Pause, TransitionType.POP)
    )

    yield machine


@pytest.mark.parametrize(
    "transition_type", [t for t in TransitionType if t is not TransitionType.POP]
)
def test_cannot_construct_invalid_transition(
    machine: StateMachine[GameState, GameContext], transition_type: TransitionType
) -> None:
    with pytest.raises(ValueError):
        machine.add_transition(GameState.TURN_START, Transition(Next, transition_type))


def test_only_sent_event_causes_transition(
    machine: StateMachine[GameState, GameContext]
) -> None:
    listener = machine.start()
    listener.send(Roll(3))
    listener.send(Next())
    assert machine.current_state() is GameState.TURN_START


def test_unmodeled_events_are_ignored(
    machine: StateMachine[GameState, GameContext]
) -> None:
    listener = machine.start()
    listener.send(UnmodeledEvent())
    assert machine.current_state() is GameState.TURN_START


def test_exit_actions_fire(machine: StateMachine[GameState, GameContext]) -> None:
    listener = machine.start()
    listener.send(Pause())
    assert machine.context.pause_count == 0
    listener.send(Pause())
    assert machine.context.pause_count == 1


def test_hierarchical_state(machine: StateMachine[GameState, GameContext]) -> None:
    listener = machine.start()
    assert machine.current_state() is GameState.TURN_START
    listener.send(Pause())
    assert machine.current_state() is GameState.PAUSED
    listener.send(Pause())
    assert machine.current_state() is GameState.TURN_START
    listener.send(Roll(3))
    assert machine.current_state() is GameState.COMPUTE_SCORE
    listener.send(Pause())
    assert machine.current_state() is GameState.PAUSED
    listener.send(Pause())
    assert machine.current_state() is GameState.COMPUTE_SCORE


def test_e2e(machine: StateMachine[GameState, GameContext]) -> None:
    listener = machine.start()

    while True:
        try:
            listener.send(Roll(3))
            listener.send(Next())
        except StopIteration:
            break

    assert machine.current_state() is GameState.GAME_OVER
    assert machine.context.score == 21
    assert machine.context.turn == 7
