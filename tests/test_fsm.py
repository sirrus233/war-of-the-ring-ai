from dataclasses import dataclass
from enum import Enum, auto

from war_of_the_ring_ai.fsm import Event, StateMachine, TransitionType


def test_fsm() -> None:
    @dataclass
    class GameContext:
        turn: int = 1
        score: int = 0

    class GameState(Enum):
        TURN_START = auto()
        COMPUTE_SCORE = auto()
        GAME_OVER = auto()

    class GameEvent(Enum):
        NEXT = auto()
        ROLL_DIE = auto()

    def roll_die(state: GameState, context: GameContext, payload: int) -> None:
        context.score += payload

    def next_turn(state: GameState, context: GameContext, payload: None) -> None:
        context.turn += 1

    def report_final_score(
        state: GameState, context: GameContext, payload: None
    ) -> None:
        print(f"Game ended with score {context.score} on turn {context.turn}")

    def is_game_over(state: GameState, context: GameContext, payload: None) -> bool:
        return context.score > 20

    context = GameContext()

    sm = StateMachine[GameState, GameEvent, GameContext](
        initial=GameState.TURN_START,
        final=[GameState.GAME_OVER],
        context=context,
    )
    sm.add_transition(
        GameState.TURN_START,
        GameEvent.ROLL_DIE,
        TransitionType.FIRE,
        GameState.COMPUTE_SCORE,
        action=roll_die,
    )
    sm.add_transition(
        GameState.COMPUTE_SCORE,
        GameEvent.NEXT,
        TransitionType.FIRE,
        GameState.GAME_OVER,
        guard=is_game_over,
        action=report_final_score,
    )
    sm.add_transition(
        GameState.COMPUTE_SCORE,
        GameEvent.NEXT,
        TransitionType.FIRE,
        GameState.TURN_START,
        action=next_turn,
    )
    gen = sm.start()
    next(gen)
    while True:
        try:
            gen.send(Event(GameEvent.ROLL_DIE, "wom"))
            gen.send(Event(GameEvent.NEXT))
        except StopIteration:
            break

    assert context.score == 21
    assert context.turn == 7
