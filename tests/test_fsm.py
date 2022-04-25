from dataclasses import dataclass
from typing import Iterable

import pytest

from war_of_the_ring_ai.fsm import (
    EmptyEvent,
    Event,
    State,
    StateMachine,
    Transition,
    TransitionType,
)


@dataclass
class GameContext:
    turn: int = 1
    score: int = 0


###
# Action and Guard functions
###
def next_turn(context: GameContext) -> None:
    context.turn += 1


def roll_die(context: GameContext, roll: int) -> None:
    context.score += roll


def is_game_over(context: GameContext, _param: None) -> bool:
    return context.score > 20


###
# States
###
TURN_START = State[GameContext](on_enter=next_turn)
COMPUTE_SCORE = State[GameContext]()
GAME_OVER = State[GameContext]()
PAUSED = State[GameContext]()

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


###
# Transitions
###
TURN_START.add_transition(
    Transition(Roll, TransitionType.FIRE, COMPUTE_SCORE, action=roll_die)
)
TURN_START.add_transition(Transition(Pause, TransitionType.PUSH, PAUSED))

COMPUTE_SCORE.add_transition(Transition(UncommonEvent, TransitionType.FIRE, GAME_OVER))
COMPUTE_SCORE.add_transition(
    Transition(Next, TransitionType.FIRE, GAME_OVER, guard=is_game_over)
)
COMPUTE_SCORE.add_transition(Transition(Next, TransitionType.FIRE, TURN_START))
COMPUTE_SCORE.add_transition(Transition(Pause, TransitionType.PUSH, PAUSED))

PAUSED.add_transition(Transition(Pause, TransitionType.POP))


@pytest.fixture(name="machine")
def fixture_state_machine() -> Iterable[StateMachine[GameContext]]:
    yield StateMachine(GameContext(), initial=TURN_START, final=[GAME_OVER])


@pytest.mark.parametrize(
    "transition_type", [t for t in TransitionType if t is not TransitionType.POP]
)
def test_cannot_construct_invalid_transition(transition_type: TransitionType) -> None:
    with pytest.raises(ValueError):
        Transition(Next, transition_type)


def test_only_sent_event_causes_transition(machine: StateMachine[GameContext]) -> None:
    listener = machine.start()
    listener.send(Roll(3))
    listener.send(Next())
    assert machine.current_state is TURN_START


def test_unmodeled_events_are_ignored(machine: StateMachine[GameContext]) -> None:
    listener = machine.start()
    listener.send(UnmodeledEvent())
    assert machine.current_state is TURN_START


def test_hierarchical_state(machine: StateMachine[GameContext]) -> None:
    listener = machine.start()
    assert machine.current_state is TURN_START
    listener.send(Pause())
    assert machine.current_state is PAUSED
    listener.send(Pause())
    assert machine.current_state is TURN_START
    listener.send(Roll(3))
    assert machine.current_state is COMPUTE_SCORE
    listener.send(Pause())
    assert machine.current_state is PAUSED
    listener.send(Pause())
    assert machine.current_state is COMPUTE_SCORE


def test_e2e(machine: StateMachine[GameContext]) -> None:
    listener = machine.start()

    while True:
        try:
            listener.send(Roll(3))
            listener.send(Next())
        except StopIteration:
            break

    assert machine.current_state is GAME_OVER
    assert machine.context.score == 21
    assert machine.context.turn == 7
