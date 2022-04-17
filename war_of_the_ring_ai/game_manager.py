from war_of_the_ring_ai.agent import human_agent, random_agent
from war_of_the_ring_ai.constants import Side
from war_of_the_ring_ai.game_data import (
    GameData,
    PlayerData,
    init_private_player_data,
    init_public_player_data,
)
from war_of_the_ring_ai.game_states import DrawPhase, GameContext, state_machine


def main() -> None:
    free_player = PlayerData(
        public=init_public_player_data(Side.FREE),
        private=init_private_player_data(Side.FREE),
    )

    shadow_player = PlayerData(
        public=init_public_player_data(Side.SHADOW),
        private=init_private_player_data(Side.SHADOW),
    )

    game = GameData(free=free_player.public, shadow=shadow_player.public)

    context = GameContext(
        game,
        players={Side.FREE: free_player, Side.SHADOW: shadow_player},
        agents={Side.FREE: human_agent, Side.SHADOW: random_agent},
    )

    state_machine(context, initial=DrawPhase)


if __name__ == "__main__":
    main()
