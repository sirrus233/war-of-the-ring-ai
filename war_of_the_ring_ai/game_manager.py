from dataclasses import dataclass
from typing import Iterable, Mapping, Optional

from war_of_the_ring_ai.activities import (
    draw,
    fellowship_can_heal,
    maximum_hunt_dice,
    minimum_hunt_dice,
    roll_dice,
    valid_guides,
)
from war_of_the_ring_ai.agent import Agent, HumanAgent, RandomAgent
from war_of_the_ring_ai.constants import (
    FREE_VP_GOAL,
    MAX_HAND_SIZE,
    SHADOW_VP_GOAL,
    DeckType,
    Side,
    Victory,
)
from war_of_the_ring_ai.game_data import (
    GameData,
    PlayerData,
    init_private_player_data,
    init_public_player_data,
)


@dataclass
class GameContext:
    game: GameData
    players: Mapping[Side, PlayerData]
    agents: Mapping[Side, Agent]


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
        agents={
            Side.FREE: HumanAgent(game, free_player.private),
            Side.SHADOW: RandomAgent(game, shadow_player.private),
        },
    )

    game_loop(context)


def game_loop(context: GameContext) -> Victory:
    while True:
        draw_phase(context)
        fellowship_phase(context)
        hunt_allocation_phase(context)
        roll_phase(context)
        if victory := action_phase(context):
            break
        if victory := victory_check_phase(context):
            break

    return victory


def draw_phase(context: GameContext) -> None:
    draw_flow(context, Side.FREE, (DeckType.CHARACTER, DeckType.STRATEGY))
    draw_flow(context, Side.SHADOW, (DeckType.CHARACTER, DeckType.STRATEGY))


def fellowship_phase(context: GameContext) -> None:
    fellowship = context.game.fellowship
    agent = context.agents[Side.FREE]

    if fellowship.progress > 0 and agent.agree("AskDeclareFellowship"):
        regions = context.game.regions
        reachable = regions.reachable_regions(fellowship.location, fellowship.progress)
        context.game.fellowship.location = agent.ask("DeclareFellowship", reachable)
        context.game.fellowship.progress = 0

    if fellowship_can_heal(context.game):
        fellowship.corruption = max(0, fellowship.corruption - 1)

    guide = agent.ask("ChangeGuide", valid_guides(context.game))
    fellowship.guide = guide


def hunt_allocation_phase(context: GameContext) -> None:
    agent = context.agents[Side.SHADOW]
    minimum = minimum_hunt_dice(context.game)
    maximum = maximum_hunt_dice(context.game)
    eyes = agent.ask("AllocateEyes", list(range(minimum, maximum + 1)))
    context.game.hunt_box.character = 0
    context.game.hunt_box.eyes = eyes


def roll_phase(context: GameContext) -> None:
    roll_dice(context.players[Side.FREE], context.game)
    roll_dice(context.players[Side.SHADOW], context.game)


def action_phase(_context: GameContext) -> Optional[Victory]:
    pass


def victory_check_phase(context: GameContext) -> Optional[Victory]:
    if context.players[Side.SHADOW].public.victory_points >= SHADOW_VP_GOAL:
        return Victory.SPMV
    if context.players[Side.FREE].public.victory_points >= FREE_VP_GOAL:
        return Victory.FPMV
    return None


def draw_flow(context: GameContext, side: Side, draws: Iterable[DeckType]) -> None:
    player = context.players[side]
    agent = context.agents[side]

    for deck in draws:
        draw(player, deck)

    while len(player.private.hand) > MAX_HAND_SIZE:
        agent.ask("Discarding", player.private.hand)


if __name__ == "__main__":
    main()
