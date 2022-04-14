from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, Mapping, Type, TypeAlias, TypeVar

from war_of_the_ring_ai.constants import Side
from war_of_the_ring_ai.game_data import GameData, PrivatePlayerData

T = TypeVar("T")


class State(Generic[T], ABC):
    def __init__(self, context: StateMachine) -> None:
        self.context = context

    @abstractmethod
    def request(self) -> list[T]:
        ...

    @abstractmethod
    def mutate(self, response: T) -> None:
        ...

    @abstractmethod
    def next(self) -> State[Any]:
        ...


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
Player: TypeAlias = tuple[PrivatePlayerData, Agent[Any]]
GameContext: TypeAlias = tuple[GameData, Mapping[Side, Player]]


class StateMachine:
    def __init__(self, game_context: GameContext, initial: Type[State[Any]]) -> None:
        self.game, self.players = game_context
        self.state = initial(self)
        self._running = False

    def start(self) -> None:
        self._running = True

        while self._running:
            player, agent = self.players[self.game.active_player.side]

            if isinstance(self.state, SimpleState):
                choice = None
            else:
                request = self.state.request()
                if not request:
                    raise ValueError(f"Reached state {self.state} with no options.")
                choice = agent(self.state, self.game, player, request)

            self.state.mutate(choice)
            self.state = self.state.next()

    def stop(self) -> None:
        self._running = False


class DrawCards(SimpleState):
    def mutate(self, response: None) -> None:
        print(response)

    def next(self) -> State[Any]:
        return self
