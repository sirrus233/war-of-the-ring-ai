from war_of_the_ring_ai.fsm import StateMachine, TransitionType


def start_turn(payload: tuple[int, int]) -> tuple[int, int]:
    return (payload[0] + 1, payload[1])


def roll_die(payload: tuple[int, int]) -> tuple[int, int]:
    result = 2
    print(f"rolled {result}")
    return (payload[0], payload[1] + result)


def report_score(payload: tuple[int, int]) -> int:
    print(f"Game ended on turn {payload[0]} with score {payload[1]}")
    return payload[1]


def end_game(payload: int) -> int:
    return payload


def is_game_over(payload: tuple[int, int]) -> bool:
    return payload[1] >= 20


def isnt_game_over(payload: tuple[int, int]) -> bool:
    return payload[1] < 20


def test_fsm():
    sm = StateMachine(initial=start_turn, initial_payload=(0, 0), final=end_game)
    sm.add_transition(TransitionType.FIRE, start_turn, roll_die)
    sm.add_transition(TransitionType.FIRE, roll_die, start_turn, isnt_game_over)
    sm.add_transition(TransitionType.FIRE, roll_die, report_score, is_game_over)
    sm.add_transition(TransitionType.FIRE, report_score, end_game)
    sm.start()
