from typing import Optional

from war_of_the_ring_ai.constants import Action, Victory
from war_of_the_ring_ai.context import GameContext
from war_of_the_ring_ai.game_data import GameData, PlayerData


def do_action(action: Action, context: GameContext) -> Optional[Victory]:
    game = context.game
    player = context.active_player
    result = None

    match action:
        case Action.SKIP:
            skip_flow()
        case Action.DRAW_CHARACTER_EVENT:
            draw_character_event_flow(player)
        case Action.DRAW_STRATEGY_EVENT:
            draw_strategy_event_flow(player)
        case Action.PLAY_CHARACTER_EVENT:
            play_character_event_flow(player)
        case Action.PLAY_ARMY_EVENT:
            play_army_event_flow(player)
        case Action.PLAY_MUSTER_EVENT:
            play_muster_event_flow(player)
        case Action.DIPLOMACY:
            diplomacy_flow(player, game)
        case Action.MUSTER_UNITS:
            muster_units_flow(player, game)
        case Action.MUSTER_SARUMAN:
            muster_saruman_flow(player, game)
        case Action.MUSTER_WITCH_KING:
            muster_witch_king_flow(player, game)
        case Action.MUSTER_MOUTH_OF_SAURON:
            muster_mouth_of_sauron_flow(player, game)
        case Action.MOVE_ARMIES:
            move_armies_flow(player, game)
        case Action.ATTACK:
            attack_flow(player, game)
        case Action.LEADER_MOVE:
            leader_move_flow(player, game)
        case Action.LEADER_ATTACK:
            leader_attack_flow(player, game)
        case Action.MOVE_FELLOWSHIP:
            move_fellowship_flow(player, game)
        case Action.HIDE_FELLOWSHIP:
            hide_fellowship_flow(player, game)
        case Action.SEPARATE_COMPANIONS:
            separate_companions_flow(player, game)
        case Action.MOVE_COMPANIONS:
            move_companions_flow(player, game)
        case Action.MOVE_MINIONS:
            move_minions_flow(player, game)
        case Action.MUSTER_GANDALF:
            muster_gandalf_flow(player, game)
        case Action.MUSTER_ARAGORN:
            muster_aragorn_flow(player, game)

    return result


def skip_flow() -> None:
    return None


def draw_character_event_flow(player: PlayerData) -> None:
    raise NotImplementedError()


def draw_strategy_event_flow(player: PlayerData) -> None:
    raise NotImplementedError()


def play_character_event_flow(player: PlayerData) -> None:
    raise NotImplementedError()


def play_army_event_flow(player: PlayerData) -> None:
    raise NotImplementedError()


def play_muster_event_flow(player: PlayerData) -> None:
    raise NotImplementedError()


def diplomacy_flow(player: PlayerData, game: GameData) -> None:
    raise NotImplementedError()


def muster_units_flow(player: PlayerData, game: GameData) -> None:
    raise NotImplementedError()


def muster_saruman_flow(player: PlayerData, game: GameData) -> None:
    raise NotImplementedError()


def muster_witch_king_flow(player: PlayerData, game: GameData) -> None:
    raise NotImplementedError()


def muster_mouth_of_sauron_flow(player: PlayerData, game: GameData) -> None:
    raise NotImplementedError()


def move_armies_flow(player: PlayerData, game: GameData) -> None:
    raise NotImplementedError()


def leader_move_flow(player: PlayerData, game: GameData) -> None:
    raise NotImplementedError()


def attack_flow(player: PlayerData, game: GameData) -> None:
    raise NotImplementedError()


def leader_attack_flow(player: PlayerData, game: GameData) -> None:
    raise NotImplementedError()


def move_fellowship_flow(player: PlayerData, game: GameData) -> None:
    raise NotImplementedError()


def hide_fellowship_flow(player: PlayerData, game: GameData) -> None:
    raise NotImplementedError()


def separate_companions_flow(player: PlayerData, game: GameData) -> None:
    raise NotImplementedError()


def move_companions_flow(player: PlayerData, game: GameData) -> None:
    raise NotImplementedError()


def move_minions_flow(player: PlayerData, game: GameData) -> None:
    raise NotImplementedError()


def muster_gandalf_flow(player: PlayerData, game: GameData) -> None:
    raise NotImplementedError()


def muster_aragorn_flow(player: PlayerData, game: GameData) -> None:
    raise NotImplementedError()
