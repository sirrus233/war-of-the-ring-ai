import random

from war_of_the_ring_ai.constants import DeckType
from war_of_the_ring_ai.game_data import PlayerData
from war_of_the_ring_ai.game_objects import Card


def draw(player: PlayerData, deck: DeckType) -> None:
    if player.private.decks[deck].cards:
        card = random.choice(player.private.decks[deck].cards)
        player.private.decks[deck].cards.remove(card)
        player.private.hand.append(card)

        player.public.decks[deck].size -= 1
        player.public.hand.append(deck)


def discard(player: PlayerData, card: Card) -> None:
    deck = DeckType.CHARACTER if card.type.CHARACTER else DeckType.STRATEGY

    player.private.hand.remove(card)
    player.private.decks[deck].discarded.append(card)

    player.public.hand.remove(deck)
    player.public.decks[deck].discarded -= 1
