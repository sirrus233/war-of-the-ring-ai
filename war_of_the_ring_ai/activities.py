import random
from typing import Iterable, Sequence

from war_of_the_ring_ai.constants import (
    ACTION_DIE,
    HEROES,
    NATIONS,
    CardType,
    DeckType,
    DieResult,
    Settlement,
    Side,
)
from war_of_the_ring_ai.game_data import GameData, PlayerData
from war_of_the_ring_ai.game_objects import FELLOWSHIP, Army, Card, Character, Region


def draw(player: PlayerData, deck: DeckType) -> None:
    if player.private.decks[deck].cards:
        card = random.choice(player.private.decks[deck].cards)

        player.private.decks[deck].cards.remove(card)
        player.private.hand.append(card)

        player.public.decks[deck].size -= 1
        player.public.hand.append(deck)


def discard(player: PlayerData, card: Card) -> None:
    deck = DeckType.CHARACTER if card.type is CardType.CHARACTER else DeckType.STRATEGY

    player.private.hand.remove(card)
    player.private.decks[deck].discarded.append(card)

    player.public.hand.remove(deck)
    player.public.decks[deck].discarded -= 1


def fellowship_can_heal(game: GameData) -> bool:
    fellowship = game.fellowship
    return (
        fellowship.location.nation in NATIONS[Side.FREE]
        and fellowship.location.settlement in (Settlement.CITY, Settlement.STRONGHOLD)
        and fellowship.location not in game.conquered
    )


def fellowship_can_activate_nation(region: Region) -> bool:
    return region.nation in NATIONS[Side.FREE] and region.settlement in (
        Settlement.CITY,
        Settlement.STRONGHOLD,
    )


def valid_guides(game: GameData) -> list[Character]:
    return list(
        game.characters.with_location(FELLOWSHIP).with_level(
            game.fellowship.guide.level
        )
    )


def minimum_hunt_dice(game: GameData) -> int:
    return 1 if game.fellowship.moved else 0


def maximum_hunt_dice(game: GameData) -> int:
    return sum(1 for _ in game.characters.with_location(FELLOWSHIP))


def rollable_dice(player: PlayerData, game: GameData) -> int:
    hero_dice = sum(
        1 for _ in game.characters.with_ids(*HEROES[player.public.side]).in_play()
    )
    allocated_eyes = game.hunt_box.eyes if player.public.side is Side.SHADOW else 0
    return player.public.starting_dice + hero_dice - allocated_eyes


def roll_dice(player: PlayerData, game: GameData) -> None:
    is_shadow = player.public.side is Side.SHADOW
    count = rollable_dice(player, game)
    player.public.dice = [
        random.choice(ACTION_DIE[player.public.side]) for _ in range(count)
    ]
    if is_shadow:
        game.hunt_box.eyes += player.public.dice.count(DieResult.EYE)
        player.public.dice = [d for d in player.public.dice if d is not DieResult.EYE]


def action_dice_remaining(players: Iterable[PlayerData]) -> bool:
    return any(player.public.dice for player in players)


def use_elven_ring(active_player: PlayerData, inactive_player: PlayerData) -> None:
    active_player.public.elven_rings -= 1
    if active_player.public.side == Side.FREE:
        inactive_player.public.elven_rings += 1


def valid_elven_ring_changes(side: Side, original: DieResult) -> Sequence[DieResult]:
    return list(
        {
            die_result
            for die_result in ACTION_DIE[side]
            if die_result not in (original, DieResult.WILL)
        }
    )


def can_pass(active_player: PlayerData, inactive_player: PlayerData) -> bool:
    return len(active_player.public.dice) < len(inactive_player.public.dice)


def is_under_siege(region: Region, side: Side, game: GameData) -> bool:
    if region.settlement is not Settlement.STRONGHOLD:
        return False

    enemy = Side.SHADOW if side is Side.FREE else Side.FREE
    units_in_region = game.armies.with_location(region).units_only()
    friendly_units = any(units_in_region.with_side(side))
    enemy_units = any(units_in_region.with_side(enemy))
    enemy_controlled = (region.nation in NATIONS[side]) == (region in game.conquered)

    return (
        region.settlement is Settlement.STRONGHOLD
        and friendly_units
        and enemy_units
        and not enemy_controlled
    )


def is_free(region: Region, side: Side, game: GameData) -> bool:
    enemy = Side.SHADOW if side is Side.FREE else Side.FREE
    enemy_units = any(game.armies.with_location(region).with_side(enemy).units_only())
    enemy_controlled_settlement = region.settlement is not None and (
        (region.nation in NATIONS[side]) == (region in game.conquered)
    )
    besieging = is_under_siege(region, enemy, game)
    return besieging or not (enemy_units or enemy_controlled_settlement)


def is_free_for_movement(region: Region, side: Side, game: GameData) -> bool:
    if is_free(region, side, game):
        return True

    enemy = Side.SHADOW if side is Side.FREE else Side.FREE
    enemy_units = any(game.armies.with_location(region).with_side(enemy).units_only())
    enemy_controlled_settlement = region.settlement is not None and (
        (region.nation in NATIONS[side]) == (region in game.conquered)
    )

    return enemy_controlled_settlement and not enemy_units


def get_army(region: Region, side: Side, game: GameData) -> Army:
    return Army(
        units=game.armies.with_side(side).with_location(region),
        characters=game.characters.with_side(side).with_location(region),
    )
