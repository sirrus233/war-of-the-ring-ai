from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Generic, Mapping, Optional, Type, TypeAlias, TypeVar

from war_of_the_ring_ai.activities import discard, draw
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


class StateMachine:
    def __init__(self, context: GameContext, initial: Type[State[Any]]) -> None:
        self.context = context
        self.state = initial(context)
        self.running = False

    def start(self) -> None:
        self.running = True

        while self.running:
            player = self.context.players[self.context.game.active_side]
            agent = self.context.agents[self.context.game.active_side]

            if isinstance(self.state, SimpleState):
                choice = None
            else:
                request = self.state.request()
                if not request:
                    raise ValueError(f"Reached state {self.state} with no options.")
                choice = agent(self.state, self.context.game, player.private, request)

            self.state.mutate(choice)

            next_state = self.state.next()
            if next_state is not None:
                self.state = next_state
            else:
                self.stop()

    def stop(self) -> None:
        self.running = False


class TurnStart(SimpleState):
    def mutate(self, response: None) -> None:
        self.context.game.turn += 1
        for side in Side:
            player = self.context.players[side]
            for deck_type in (DeckType.CHARACTER, DeckType.STRATEGY):
                draw(player, deck_type)

    def next(self) -> Optional[State[Any]]:
        for side in Side:
            player = self.context.players[side]
            if len(player.private.hand) > MAX_HAND_SIZE:
                self.context.game.active_side = side
                StateMachine(self.context, Discard).start()

        return self


class Discard(State[Card]):
    def request(self) -> list[Card]:
        return self.active_player.private.hand

    def mutate(self, response: Card) -> None:
        discard(self.active_player, response)

    def next(self) -> Optional[State[Any]]:
        if len(self.active_player.private.hand) > MAX_HAND_SIZE:
            return self
        return None
