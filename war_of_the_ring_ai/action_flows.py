from typing import Iterable, Optional

from war_of_the_ring_ai.activities import discard, draw
from war_of_the_ring_ai.constants import (
    GANDALF_LOCATION,
    MAX_HAND_SIZE,
    NATIONS,
    SARUMAN_LOCATION,
    Action,
    CharacterID,
    DeckType,
    Nation,
    Settlement,
    Side,
    Victory,
)
from war_of_the_ring_ai.context import GameContext
from war_of_the_ring_ai.game_objects import CASUALTIES


def do_action(action: Action, context: GameContext) -> Optional[Victory]:
    result = None

    match action:
        case Action.SKIP:
            skip_flow()
        case Action.DRAW_CHARACTER_EVENT:
            draw_character_event_flow(context)
        case Action.DRAW_STRATEGY_EVENT:
            draw_strategy_event_flow(context)
        case Action.PLAY_CHARACTER_EVENT:
            play_character_event_flow(context)
        case Action.PLAY_ARMY_EVENT:
            play_army_event_flow(context)
        case Action.PLAY_MUSTER_EVENT:
            play_muster_event_flow(context)
        case Action.DIPLOMACY:
            diplomacy_flow(context)
        case Action.MUSTER_UNITS:
            muster_units_flow(context)
        case Action.MUSTER_SARUMAN:
            muster_saruman_flow(context)
        case Action.MUSTER_WITCH_KING:
            muster_witch_king_flow(context)
        case Action.MUSTER_MOUTH_OF_SAURON:
            muster_mouth_of_sauron_flow(context)
        case Action.MOVE_ARMIES:
            move_armies_flow(context)
        case Action.ATTACK:
            attack_flow(context)
        case Action.LEADER_MOVE:
            leader_move_flow(context)
        case Action.LEADER_ATTACK:
            leader_attack_flow(context)
        case Action.MOVE_FELLOWSHIP:
            move_fellowship_flow(context)
        case Action.HIDE_FELLOWSHIP:
            hide_fellowship_flow(context)
        case Action.SEPARATE_COMPANIONS:
            separate_companions_flow(context)
        case Action.MOVE_COMPANIONS:
            move_companions_flow(context)
        case Action.MOVE_MINIONS:
            move_minions_flow(context)
        case Action.MUSTER_GANDALF:
            muster_gandalf_flow(context)
        case Action.MUSTER_ARAGORN:
            muster_aragorn_flow(context)

    return result


def skip_flow() -> None:
    return None


def draw_flow(context: GameContext, side: Side, draws: Iterable[DeckType]) -> None:
    player = context.players[side]
    agent = context.agents[side]

    for deck in draws:
        draw(player, deck)

    while len(player.private.hand) > MAX_HAND_SIZE:
        card = agent.ask("Discarding", player.private.hand)
        discard(player, card)


def draw_character_event_flow(context: GameContext) -> None:
    draw_flow(context, context.active_player.public.side, [DeckType.CHARACTER])


def draw_strategy_event_flow(context: GameContext) -> None:
    draw_flow(context, context.active_player.public.side, [DeckType.STRATEGY])


def play_character_event_flow(context: GameContext) -> None:
    raise NotImplementedError()


def play_army_event_flow(context: GameContext) -> None:
    raise NotImplementedError()


def play_muster_event_flow(context: GameContext) -> None:
    raise NotImplementedError()


def diplomacy_flow(context: GameContext) -> None:
    politics = context.game.politics
    options = [
        nation
        for nation in NATIONS[context.active_player.public.side]
        if politics[nation].can_advance
    ]
    nation = context.active_agent.ask("Diplomacy", options)
    politics[nation].disposition -= 1


def muster_units_flow(context: GameContext) -> None:
    raise NotImplementedError()


def muster_saruman_flow(context: GameContext) -> None:
    location = context.game.regions.get_region(SARUMAN_LOCATION)
    context.game.characters.with_id(CharacterID.SARUMAN).location = location


def muster_witch_king_flow(context: GameContext) -> None:
    witch_king = context.game.characters.with_id(CharacterID.WITCH_KING)
    locations = [
        unit.location
        for unit in context.game.armies.with_nation(Nation.SAURON)
        .units_only()
        .in_play()
    ]
    location = context.active_agent.ask("WitchKing", locations)
    witch_king.location = location


def muster_mouth_of_sauron_flow(context: GameContext) -> None:
    mouth_of_sauron = context.game.characters.with_id(CharacterID.MOUTH_OF_SAURON)
    locations = [
        region
        for region in context.game.regions.all_regions()
        .with_nation(Nation.SAURON)
        .with_settlement(Settlement.STRONGHOLD)
        if region not in context.game.conquered
    ]
    location = context.active_agent.ask("MouthSauron", locations)
    mouth_of_sauron.location = location


def move_armies_flow(context: GameContext) -> None:
    raise NotImplementedError()


def leader_move_flow(context: GameContext) -> None:
    raise NotImplementedError()


def attack_flow(context: GameContext) -> None:
    raise NotImplementedError()


def leader_attack_flow(context: GameContext) -> None:
    raise NotImplementedError()


def move_fellowship_flow(context: GameContext) -> None:
    raise NotImplementedError()


def hide_fellowship_flow(context: GameContext) -> None:
    context.game.fellowship.is_revealed = False


def separate_companions_flow(context: GameContext) -> None:
    raise NotImplementedError()


def move_companions_flow(context: GameContext) -> None:
    raise NotImplementedError()


def move_minions_flow(context: GameContext) -> None:
    raise NotImplementedError()


def muster_gandalf_flow(context: GameContext) -> None:
    gandalf_grey = context.game.characters.with_id(CharacterID.GANDALF_GREY)
    gandalf_white = context.game.characters.with_id(CharacterID.GANDALF_WHITE)
    if gandalf_grey.in_play:
        gandalf_white.location = gandalf_grey.location
        gandalf_grey.location = CASUALTIES
    else:
        fangorn = [context.game.regions.get_region(GANDALF_LOCATION)]
        elves = [
            region
            for region in context.game.regions.all_regions()
            .with_nation(Nation.ELVES)
            .with_settlement(Settlement.STRONGHOLD)
            if region not in context.game.conquered
        ]
        location = context.active_agent.ask("GandalfWhite", fangorn + elves)
        gandalf_white.location = location


def muster_aragorn_flow(context: GameContext) -> None:
    strider = context.game.characters.with_id(CharacterID.STRIDER)
    aragorn = context.game.characters.with_id(CharacterID.ARAGORN)
    aragorn.location = strider.location
    strider.location = CASUALTIES
