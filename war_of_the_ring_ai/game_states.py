from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Generic, Mapping, Optional, TypeAlias, TypeVar

from war_of_the_ring_ai.constants import MAX_HAND_SIZE, DeckType, Side
from war_of_the_ring_ai.game_data import GameData, PlayerData, PrivatePlayerData
from war_of_the_ring_ai.game_objects import Card

T = TypeVar("T")


class State(Generic[T], ABC):
    def __init__(self, context: GameContext) -> None:
        self.context = context

    @abstractmethod
    def request(self) -> list[T]:
        ...

    @abstractmethod
    def mutate(self, response: T) -> None:
        ...

    @abstractmethod
    def next(self) -> Optional[State[Any]]:
        ...

    @property
    def active_player(self) -> PlayerData:
        return self.context.players[self.context.game.active_side]


class SimpleState(State[None], ABC):
    def request(self) -> list[None]:
        raise NotImplementedError("Simple states do not request a player's input.")

    @abstractmethod
    def mutate(self, response: None) -> None:
        ...


class BinaryChoice(State[bool], ABC):
    def request(self) -> list[bool]:
        return [True, False]

    @abstractmethod
    def mutate(self, response: bool) -> None:
        ...


Agent: TypeAlias = Callable[[State[T], GameData, PrivatePlayerData, list[T]], T]


@dataclass
class GameContext:
    game: GameData
    players: Mapping[Side, PlayerData]
    agents: Mapping[Side, Agent[Any]]


def state_machine(context: GameContext, initial: State[Any]) -> None:
    state = initial
    running = True

    while running:
        player = context.players[context.game.active_side]
        agent = context.agents[context.game.active_side]

        if isinstance(state, SimpleState):
            choice = None
        else:
            request = state.request()
            if not request:
                raise ValueError(f"Reached state {state} with no options.")
            choice = agent(state, context.game, player.private, request)

        state.mutate(choice)

        next_state = state.next()
        if next_state is not None:
            state = next_state
        else:
            running = False


class DrawPhase(SimpleState):
    def mutate(self, response: None) -> None:
        self.context.game.turn += 1
        self.context.game.active_side = Side.SHADOW
        state_machine(self.context, Draw(self.context, 1, 1))
        self.context.game.active_side = Side.FREE
        state_machine(self.context, Draw(self.context, 1, 1))

    def next(self) -> Optional[State[Any]]:
        return self


class Draw(SimpleState):
    def __init__(
        self, context: GameContext, character_draws: int = 0, strategy_draws: int = 0
    ) -> None:
        super().__init__(context)
        self.character_draws = character_draws
        self.strategy_draws = strategy_draws

    def mutate(self, response: None) -> None:
        def draw(player: PlayerData, deck: DeckType) -> None:
            if player.private.decks[deck].cards:
                card = random.choice(player.private.decks[deck].cards)
                player.private.decks[deck].cards.remove(card)
                player.private.hand.append(card)

                player.public.decks[deck].size -= 1
                player.public.hand.append(deck)

        for _ in range(self.character_draws):
            draw(self.active_player, DeckType.CHARACTER)

        for _ in range(self.strategy_draws):
            draw(self.active_player, DeckType.STRATEGY)

    def next(self) -> Optional[State[Any]]:
        if len(self.active_player.private.hand) > MAX_HAND_SIZE:
            return Discard(self.context)
        return None


class Discard(State[Card]):
    def request(self) -> list[Card]:
        return self.active_player.private.hand

    def mutate(self, response: Card) -> None:
        card = response
        deck = DeckType.CHARACTER if card.type.CHARACTER else DeckType.STRATEGY

        self.active_player.private.hand.remove(card)
        self.active_player.private.decks[deck].discarded.append(card)

        self.active_player.public.hand.remove(deck)
        self.active_player.public.decks[deck].discarded -= 1

    def next(self) -> Optional[State[Any]]:
        if len(self.active_player.private.hand) > MAX_HAND_SIZE:
            return self
        return None
