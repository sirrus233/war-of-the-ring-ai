from war_of_the_ring_ai.activities import (
    get_army,
    is_free,
    is_under_siege,
    unit_can_enter,
)
from war_of_the_ring_ai.constants import (
    NATIONS,
    SARUMAN_LOCATION,
    Action,
    CardType,
    CharacterID,
    DeckType,
    Nation,
    Settlement,
    Side,
)
from war_of_the_ring_ai.game_data import GameData, PlayerData
from war_of_the_ring_ai.game_objects import FELLOWSHIP, MORDOR, REINFORCEMENTS, Region


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
        case Action.MUSTER_UNITS:
            result = can_muster_units(player, game)
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


def can_muster_units(player: PlayerData, game: GameData) -> bool:
    at_war_nations = [
        nation
        for nation in NATIONS[player.public.side]
        if game.politics[nation].is_at_war
    ]
    for nation in at_war_nations:
        reinforcement_exists = any(
            game.armies.with_nation(nation).with_location(REINFORCEMENTS)
        )
        location_exists = any(
            is_free(region, player.public.side, game)
            for region in game.regions.all_regions()
            .with_nation(nation)
            .with_any_settlement()
        )
        if reinforcement_exists and location_exists:
            return True
    return False


def can_muster_saruman(player: PlayerData, game: GameData) -> bool:
    saruman = game.characters.with_id(CharacterID.SARUMAN)
    return (
        player.public.side is Side.SHADOW
        and saruman.location is REINFORCEMENTS
        and game.politics[Nation.ISENGARD].is_at_war
        and game.regions.get_region(SARUMAN_LOCATION) not in game.conquered
    )


def can_muster_witch_king(player: PlayerData, game: GameData) -> bool:
    witch_king = game.characters.with_id(CharacterID.WITCH_KING)
    free_nations = NATIONS[Side.FREE]
    free_nation_at_war = any(game.politics[nation].is_at_war for nation in free_nations)
    return (
        player.public.side is Side.SHADOW
        and witch_king.location is REINFORCEMENTS
        and game.politics[Nation.SAURON].is_at_war
        and free_nation_at_war
        and any(game.armies.with_nation(Nation.SAURON).units_only().in_play())
    )


def can_muster_mouth_of_sauron(player: PlayerData, game: GameData) -> bool:
    mouth_of_sauron = game.characters.with_id(CharacterID.MOUTH_OF_SAURON)
    all_nations_at_war = all(status.is_at_war for status in game.politics.values())
    return (
        player.public.side is Side.SHADOW
        and mouth_of_sauron.location is REINFORCEMENTS
        and (all_nations_at_war or game.fellowship.location is MORDOR)
        and any(
            region not in game.conquered
            for region in game.regions.all_regions()
            .with_nation(Nation.SAURON)
            .with_settlement(Settlement.STRONGHOLD)
        )
    )


def can_move_armies(player: PlayerData, game: GameData) -> bool:
    side = player.public.side
    start_regions: list[Region] = []

    for region in game.regions.all_regions():
        army = get_army(region, side, game)
        if army.is_combat_army and not is_under_siege(region, side, game):
            start_regions.append(region)

    for region in start_regions:
        army = get_army(region, side, game)
        for neighbor in game.regions.neighbors(region):
            if any(unit_can_enter(unit, neighbor, game) for unit in army.units):
                return True

    return False


def can_leader_move(player: PlayerData, game: GameData) -> bool:
    side = player.public.side
    start_regions: list[Region] = []

    for region in game.regions.all_regions():
        army = get_army(region, side, game)
        besieged = is_under_siege(region, side, game)
        if army.is_combat_army and army.leadership > 0 and not besieged:
            start_regions.append(region)

    for region in start_regions:
        army = get_army(region, side, game)
        for neighbor in game.regions.neighbors(region):
            moveable_unit = any(
                unit_can_enter(unit, neighbor, game) for unit in army.units
            )
            moveable_leader = any(
                unit_can_enter(leader, neighbor, game) for leader in army.leaders
            )
            moveable_character = any(army.characters.can_move())
            if moveable_unit and (moveable_leader or moveable_character):
                return True

    return False


def can_attack(player: PlayerData, game: GameData) -> bool:
    side = player.public.side
    enemy = Side.SHADOW if side is Side.FREE else Side.FREE

    for region in game.regions.all_regions():
        army = get_army(region, side, game)
        unit_at_war = any(game.politics[unit.nation].is_at_war for unit in army.units)
        besieging = is_under_siege(region, enemy, game)
        target_exists = any(
            not is_under_siege(neighbor, enemy, game)
            and get_army(neighbor, enemy, game).is_combat_army
            for neighbor in game.regions.neighbors(region)
        )

        if army.is_combat_army and unit_at_war and (besieging or target_exists):
            return True

    return False


def can_leader_attack(player: PlayerData, game: GameData) -> bool:
    side = player.public.side
    enemy = Side.SHADOW if side is Side.FREE else Side.FREE

    for region in game.regions.all_regions():
        army = get_army(region, side, game)
        leader_at_war = any(army.characters) or any(
            game.politics[leader.nation].is_at_war for leader in army.leaders
        )
        besieging = is_under_siege(region, enemy, game)
        target_exists = any(
            not is_under_siege(neighbor, enemy, game)
            and get_army(neighbor, enemy, game).is_combat_army
            for neighbor in game.regions.neighbors(region)
        )

        if army.is_combat_army and leader_at_war and (besieging or target_exists):
            return True

    return False


def can_move_fellowship(player: PlayerData, game: GameData) -> bool:
    return player.public.side is Side.FREE and not game.fellowship.is_revealed


def can_hide_fellowship(player: PlayerData, game: GameData) -> bool:
    return player.public.side is Side.FREE and game.fellowship.is_revealed


def can_separate_companions(player: PlayerData, game: GameData) -> bool:
    return player.public.side is Side.FREE and any(
        game.characters.with_location(FELLOWSHIP)
    )


def can_move_companions(player: PlayerData, game: GameData) -> bool:
    if player.public.side is not Side.FREE:
        return False

    companions = game.characters.with_side(Side.FREE).can_move().in_play()
    return any(
        not is_under_siege(companion.location, Side.FREE, game)
        for companion in companions
    )


def can_move_minions(player: PlayerData, game: GameData) -> bool:
    if player.public.side is not Side.SHADOW:
        return False

    if any(game.armies.nazgul().in_play()):
        return True

    if game.characters.with_id(CharacterID.WITCH_KING).in_play:
        return True

    minions = game.characters.with_side(Side.SHADOW).can_move().in_play()
    return any(
        not is_under_siege(minion.location, Side.FREE, game) for minion in minions
    )


def can_muster_gandalf(player: PlayerData, game: GameData) -> bool:
    gandalf_white = game.characters.with_id(CharacterID.GANDALF_WHITE)
    gandalf_grey = game.characters.with_id(CharacterID.GANDALF_GREY)
    minions = game.characters.with_ids(
        CharacterID.SARUMAN, CharacterID.WITCH_KING, CharacterID.MOUTH_OF_SAURON
    )
    return (
        player.public.side is Side.FREE
        and gandalf_white.location is REINFORCEMENTS
        and gandalf_grey.location is not FELLOWSHIP
        and any(minion.location is not REINFORCEMENTS for minion in minions)
    )


def can_muster_aragorn(player: PlayerData, game: GameData) -> bool:
    aragorn = game.characters.with_id(CharacterID.ARAGORN)
    strider = game.characters.with_id(CharacterID.STRIDER)
    muster_locations = (
        game.regions.all_regions()
        .with_nation(Nation.GONDOR)
        .with_settlement(Settlement.CITY, Settlement.STRONGHOLD)
    )

    return (
        player.public.side is Side.FREE
        and aragorn.location is REINFORCEMENTS
        and strider.location in muster_locations
        and strider.location not in game.conquered
    )
