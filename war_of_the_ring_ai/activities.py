import random

from war_of_the_ring_ai.constants import (
    FREE_HEROES,
    FREE_NATIONS,
    SHADOW_HEROES,
    CardType,
    DeckType,
    Settlement,
    Side,
)
from war_of_the_ring_ai.game_data import (
    CASUALTIES,
    FELLOWSHIP,
    REINFORCEMENTS,
    GameData,
    PlayerData,
)
from war_of_the_ring_ai.game_objects import Card, Character


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
        fellowship.location.nation in FREE_NATIONS
        and fellowship.location.settlement in (Settlement.CITY, Settlement.STRONGHOLD)
        and fellowship.location not in game.conquered
    )


def valid_guides(game: GameData) -> list[Character]:
    return [
        character
        for character in game.characters.values()
        if character.location is FELLOWSHIP
        and character.level == game.fellowship.guide.level
    ]


def minimum_hunt_dice(game: GameData) -> int:
    return 1 if game.fellowship.moved else 0


def maximum_hunt_dice(game: GameData) -> int:
    return sum(
        1 for character in game.characters.values() if character.location is FELLOWSHIP
    )


def rollable_dice(player: PlayerData, game: GameData) -> int:
    hero_ids = FREE_HEROES if player.public.side is Side.FREE else SHADOW_HEROES
    heroes = (game.characters[character_id] for character_id in hero_ids)
    hero_dice = sum(
        1 for hero in heroes if hero.location not in (REINFORCEMENTS, CASUALTIES)
    )
    allocated_eyes = game.hunt_box.eyes if player.public.side is Side.SHADOW else 0
    return player.public.starting_dice + hero_dice - allocated_eyes
