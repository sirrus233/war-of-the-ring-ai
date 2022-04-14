from war_of_the_ring_ai.agent import human_agent
from war_of_the_ring_ai.constants import Side
from war_of_the_ring_ai.game_data import GameData, init_private_player_state
from war_of_the_ring_ai.game_states import DrawCards, StateMachine


def main() -> None:
    game = GameData()
    players = {
        Side.FREE: (init_private_player_state(Side.FREE), human_agent),
        Side.SHADOW: (init_private_player_state(Side.SHADOW), human_agent),
    }
    machine = StateMachine(game_context=(game, players), initial=DrawCards)
    machine.start()


if __name__ == "__main__":
    main()
