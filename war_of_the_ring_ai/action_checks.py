from war_of_the_ring_ai.constants import (
    ARAGORN_LOCATIONS,
    NATIONS,
    Action,
    CardType,
    CharacterID,
    DeckType,
    Side,
    UnitRank,
)
from war_of_the_ring_ai.game_data import (
    FELLOWSHIP,
    MORDOR,
    REINFORCEMENTS,
    GameData,
    PlayerData,
)


def can_do_action(action: Action, player: PlayerData, game: GameData) -> bool:
    match action:
        case Action.SKIP:
            result = can_skip()
        case Action.DRAW_CHARACTER_EVENT:
            result = can_draw_character_event(player)
        case Action.DRAW_STRATEGY_EVENT:
            result = can_draw_strategy_event(player)
        case Action.PLAY_CHARACTER_EVENT:
            result = can_play_character_event(player)
        case Action.PLAY_ARMY_EVENT:
            result = can_play_army_event(player)
        case Action.PLAY_MUSTER_EVENT:
            result = can_play_muster_event(player)
        case Action.DIPLOMACY:
            result = can_diplomacy(player, game)
        case Action.MUSTER_ELITE:
            result = can_muster_elite(player, game)
        case Action.MUSTER_REGULAR_REGULAR:
            result = can_muster_regular_regular(player, game)
        case Action.MUSTER_REGULAR_LEADER:
            result = can_muster_regular_leader(player, game)
        case Action.MUSTER_LEADER_LEADER:
            result = can_muster_leader_leader(player, game)
        case Action.MUSTER_SARUMAN:
            result = can_muster_saruman(player, game)
        case Action.MUSTER_WITCH_KING:
            result = can_muster_witch_king(player, game)
        case Action.MUSTER_MOUTH_OF_SAURON:
            result = can_muster_mouth_of_sauron(player, game)
        case Action.MOVE_ARMIES:
            result = can_move_armies(player, game)
        case Action.ATTACK:
            result = can_attack(player, game)
        case Action.LEADER_MOVE:
            result = can_leader_move(player, game)
        case Action.LEADER_ATTACK:
            result = can_leader_attack(player, game)
        case Action.MOVE_FELLOWSHIP:
            result = can_move_fellowship(player, game)
        case Action.HIDE_FELLOWSHIP:
            result = can_hide_fellowship(player, game)
        case Action.SEPARATE_COMPANIONS:
            result = can_separate_companions(player, game)
        case Action.MOVE_COMPANIONS:
            result = can_move_companions(player, game)
        case Action.MOVE_MINIONS:
            result = can_move_minions(player, game)
        case Action.MUSTER_GANDALF:
            result = can_muster_gandalf(player, game)
        case Action.MUSTER_ARAGORN:
            result = can_muster_aragorn(player, game)

    return result


def can_skip() -> bool:
    return True  # Any die can be thrown away without taking an action


def can_draw_character_event(player: PlayerData) -> bool:
    return player.public.decks[DeckType.CHARACTER].size > 0


def can_draw_strategy_event(player: PlayerData) -> bool:
    return player.public.decks[DeckType.STRATEGY].size > 0


def can_play_character_event(player: PlayerData) -> bool:
    return any(card.type is CardType.CHARACTER for card in player.private.hand)


def can_play_army_event(player: PlayerData) -> bool:
    return any(card.type is CardType.ARMY for card in player.private.hand)


def can_play_muster_event(player: PlayerData) -> bool:
    return any(card.type is CardType.MUSTER for card in player.private.hand)


def can_diplomacy(player: PlayerData, game: GameData) -> bool:
    nations = NATIONS[player.public.side]
    return any(game.politics[nation].can_advance for nation in nations)


def can_muster_elite(player: PlayerData, game: GameData) -> bool:
    at_war_nations = [
        nation
        for nation in NATIONS[player.public.side]
        if game.politics[nation].is_at_war
    ]
    return any(
        game.reinforcements[nation][UnitRank.ELITE] > 0 for nation in at_war_nations
    )


def can_muster_regular_regular(player: PlayerData, game: GameData) -> bool:
    raise NotImplementedError()


def can_muster_regular_leader(player: PlayerData, game: GameData) -> bool:
    raise NotImplementedError()


def can_muster_leader_leader(player: PlayerData, game: GameData) -> bool:
    raise NotImplementedError()


def can_muster_saruman(player: PlayerData, game: GameData) -> bool:
    saruman = game.characters[CharacterID.SARUMAN]
    return player.public.side is Side.SHADOW and saruman.location is REINFORCEMENTS


def can_muster_witch_king(player: PlayerData, game: GameData) -> bool:
    witch_king = game.characters[CharacterID.WITCH_KING]
    free_nations = NATIONS[Side.FREE]
    free_nation_at_war = any(game.politics[nation].is_at_war for nation in free_nations)
    return (
        player.public.side is Side.SHADOW
        and witch_king.location is REINFORCEMENTS
        and free_nation_at_war
    )


def can_muster_mouth_of_sauron(player: PlayerData, game: GameData) -> bool:
    mouth_of_sauron = game.characters[CharacterID.MOUTH_OF_SAURON]
    all_nations_at_war = all(status.is_at_war for status in game.politics.values())
    return (
        player.public.side is Side.SHADOW
        and mouth_of_sauron.location is REINFORCEMENTS
        and (all_nations_at_war or game.fellowship.location is MORDOR)
    )


def can_move_armies(player: PlayerData, game: GameData) -> bool:
    raise NotImplementedError()


def can_attack(player: PlayerData, game: GameData) -> bool:
    raise NotImplementedError()


def can_leader_move(player: PlayerData, game: GameData) -> bool:
    raise NotImplementedError()


def can_leader_attack(player: PlayerData, game: GameData) -> bool:
    raise NotImplementedError()


def can_move_fellowship(player: PlayerData, game: GameData) -> bool:
    return player.public.side is Side.FREE and not game.fellowship.is_revealed


def can_hide_fellowship(player: PlayerData, game: GameData) -> bool:
    return player.public.side is Side.FREE and game.fellowship.is_revealed


def can_separate_companions(player: PlayerData, game: GameData) -> bool:
    return player.public.side is Side.FREE and any(
        character.location is FELLOWSHIP for character in game.characters.values()
    )


def can_move_companions(player: PlayerData, game: GameData) -> bool:
    raise NotImplementedError()


def can_move_minions(player: PlayerData, game: GameData) -> bool:
    raise NotImplementedError()


def can_muster_gandalf(player: PlayerData, game: GameData) -> bool:
    gandalf_white = game.characters[CharacterID.GANDALF_WHITE]
    gandalf_grey = game.characters[CharacterID.GANDALF_GREY]
    minions = [
        game.characters[character_id]
        for character_id in (
            CharacterID.SARUMAN,
            CharacterID.WITCH_KING,
            CharacterID.MOUTH_OF_SAURON,
        )
    ]
    return (
        player.public.side is Side.FREE
        and gandalf_white.location is REINFORCEMENTS
        and gandalf_grey.location is not FELLOWSHIP
        and any(minion.location is not REINFORCEMENTS for minion in minions)
    )


def can_muster_aragorn(player: PlayerData, game: GameData) -> bool:
    aragorn = game.characters[CharacterID.ARAGORN]
    strider = game.characters[CharacterID.STRIDER]
    return (
        player.public.side is Side.FREE
        and aragorn.location is REINFORCEMENTS
        and strider.location.name in ARAGORN_LOCATIONS
    )
