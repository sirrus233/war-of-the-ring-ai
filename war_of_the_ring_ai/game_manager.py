from typing import Optional

from war_of_the_ring_ai.action_checks import can_do_action
from war_of_the_ring_ai.action_flows import do_action, draw_flow
from war_of_the_ring_ai.activities import (
    action_dice_remaining,
    can_pass,
    fellowship_can_activate_nation,
    fellowship_can_heal,
    maximum_hunt_dice,
    minimum_hunt_dice,
    roll_dice,
    use_elven_ring,
    valid_elven_ring_changes,
    valid_guides,
)
from war_of_the_ring_ai.agent import HumanAgent, RandomAgent
from war_of_the_ring_ai.constants import (
    ACTIONS,
    FREE_VP_GOAL,
    MORDOR_ENTRANCES,
    SHADOW_VP_GOAL,
    Action,
    DeckType,
    DieResult,
    Side,
    Victory,
)
from war_of_the_ring_ai.context import GameContext
from war_of_the_ring_ai.game_data import (
    GameData,
    PlayerData,
    init_private_player_data,
    init_public_player_data,
)
from war_of_the_ring_ai.game_objects import MORDOR


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
    declare_fellowship_flow(context)
    heal_fellowship_flow(context)
    enter_mordor_flow(context)
    change_guide_flow(context)


def hunt_allocation_phase(context: GameContext) -> None:
    agent = context.agents[Side.SHADOW]
    minimum = minimum_hunt_dice(context.game)
    maximum = maximum_hunt_dice(context.game)
    eyes = agent.ask("AllocateEyes", list(range(minimum, maximum + 1)))
    context.game.hunt_box.character = 0
    context.game.hunt_box.eyes = eyes
    context.game.fellowship.moved = False


def roll_phase(context: GameContext) -> None:
    roll_dice(context.players[Side.FREE], context.game)
    roll_dice(context.players[Side.SHADOW], context.game)


def action_phase(context: GameContext) -> Optional[Victory]:
    context.game.active_side = Side.FREE

    while action_dice_remaining(context.players.values()):
        elven_ring_flow(context)
        if pass_flow(context):
            continue
        action = choose_action_flow(context)
        if victory := do_action_flow(context, action):
            return victory
        end_action_flow(context)

    return None


def victory_check_phase(context: GameContext) -> Optional[Victory]:
    if context.players[Side.SHADOW].public.victory_points >= SHADOW_VP_GOAL:
        return Victory.SPMV
    if context.players[Side.FREE].public.victory_points >= FREE_VP_GOAL:
        return Victory.FPMV
    return None


def declare_fellowship_flow(context: GameContext) -> None:
    fellowship = context.game.fellowship
    agent = context.agents[Side.FREE]

    if not fellowship.is_revealed and agent.agree("AskDeclareFellowship"):
        regions = context.game.regions
        reachable = regions.reachable_regions(fellowship.location, fellowship.progress)
        context.game.fellowship.location = agent.ask("DeclareFellowship", reachable)
        context.game.fellowship.progress = 0

        if fellowship_can_activate_nation(fellowship.location):
            assert fellowship.location.nation is not None
            context.game.politics[fellowship.location.nation].active = True


def heal_fellowship_flow(context: GameContext) -> None:
    fellowship = context.game.fellowship

    if fellowship_can_heal(context.game):
        fellowship.corruption = max(0, fellowship.corruption - 1)


def enter_mordor_flow(context: GameContext) -> None:
    fellowship = context.game.fellowship
    agent = context.agents[Side.FREE]

    if fellowship.location.name in MORDOR_ENTRANCES and agent.agree("EnterMordor"):
        fellowship.progress = 0
        fellowship.location = MORDOR


def change_guide_flow(context: GameContext) -> None:
    agent = context.agents[Side.FREE]
    guide = agent.ask("ChangeGuide", valid_guides(context.game))
    context.game.fellowship.guide = guide


def elven_ring_flow(context: GameContext) -> None:
    agent = context.active_agent
    active_player = context.active_player
    active_side = active_player.public.side
    inactive_player = context.inactive_player

    if active_player.public.elven_rings > 0 and agent.agree("UseElvenRing"):
        use_elven_ring(active_player, inactive_player)
        old_die = agent.ask("ElvenDie", active_player.public.dice)
        new_die = agent.ask(
            "ElvenDieChange", valid_elven_ring_changes(active_side, old_die)
        )
        active_player.public.dice.remove(old_die)
        if new_die is DieResult.EYE:
            context.game.hunt_box.eyes += 1
        else:
            active_player.public.dice.append(new_die)


def pass_flow(context: GameContext) -> bool:
    agent = context.active_agent

    if can_pass(context.active_player, context.inactive_player) and agent.agree("Pass"):
        context.game.active_side = context.game.inactive_side
        return True
    return False


def choose_action_flow(context: GameContext) -> Action:
    die = context.active_agent.ask("ChooseActionDie", context.active_player.public.dice)
    context.active_player.public.dice.remove(die)
    valid_actions = [
        action
        for action in ACTIONS[die]
        if can_do_action(action, context.active_player, context.game)
    ]
    return context.active_agent.ask("ChooseAction", valid_actions)


def do_action_flow(context: GameContext, action: Action) -> Optional[Victory]:
    return do_action(action, context)


def end_action_flow(context: GameContext) -> None:
    if context.inactive_player.public.dice:
        context.game.active_side = context.game.inactive_side


if __name__ == "__main__":
    main()
