# pylint: disable=useless-return

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Generic,
    Mapping,
    Optional,
    Type,
    TypeAlias,
    TypeVar,
    Union,
)

from war_of_the_ring_ai.constants import MAX_HAND_SIZE, DeckType, Side
from war_of_the_ring_ai.game_data import GameData, PlayerData, PrivatePlayerData
from war_of_the_ring_ai.game_objects import Card, Region

T = TypeVar("T")
NextState: TypeAlias = Type["State[Any]"]
StateParams: TypeAlias = dict[str, Any]
Transition = Union[None, NextState, tuple[NextState, StateParams]]
Agent: TypeAlias = Callable[["State[T]", GameData, PrivatePlayerData, list[T]], T]


class State(Generic[T], ABC):
    def __init__(self, context: GameContext) -> None:
        self.context = context

    @abstractmethod
    def request(self) -> list[T]:
        ...

    @abstractmethod
    def transition(self, response: T) -> Transition:
        ...

    @property
    def active_player(self) -> PlayerData:
        return self.context.players[self.context.game.active_side]


class SimpleState(State[None], ABC):
    def request(self) -> list[None]:
        raise NotImplementedError("Simple states do not request a player's input.")

    @abstractmethod
    def transition(self, response: None) -> Transition:
        ...


class BinaryChoice(State[bool], ABC):
    def request(self) -> list[bool]:
        return [True, False]

    @abstractmethod
    def transition(self, response: bool) -> Transition:
        ...


@dataclass
class GameContext:
    game: GameData
    players: Mapping[Side, PlayerData]
    agents: Mapping[Side, Agent[Any]]


def state_machine(
    context: GameContext, initial: NextState, params: Optional[StateParams] = None
) -> None:
    state = initial(context, **params) if params else initial(context)
    running = True

    while running:
        player = context.players[context.game.active_side]
        agent = context.agents[context.game.active_side]

        if isinstance(state, SimpleState):
            response = None
        else:
            request = state.request()
            if not request:
                raise ValueError(f"Reached state {state} with no options.")
            response = agent(state, context.game, player.private, request)

        transition = state.transition(response)

        # TODO Uncomment after fix for https://github.com/python/mypy/issues/12533
        # match transition:
        #     case None:
        #         running = False
        #     case next_state, params:
        #         state = next_state(context, **params)
        #     case next_state:
        #         state = next_state(context)
        if transition is None:
            running = False
        elif isinstance(transition, tuple):
            next_state, params = transition
            state = next_state(**params)
        else:
            state = transition(context)


class DrawPhase(SimpleState):
    def transition(self, response: None) -> Transition:
        self.context.game.turn += 1
        self.context.game.active_side = Side.SHADOW
        state_machine(self.context, Draw, {"character_draws": 1, "strategy_draws": 1})
        self.context.game.active_side = Side.FREE
        state_machine(self.context, Draw, {"character_draws": 1, "strategy_draws": 1})

        return FellowshipPhase


class Draw(SimpleState):
    def __init__(
        self, context: GameContext, character_draws: int = 0, strategy_draws: int = 0
    ) -> None:
        super().__init__(context)
        self.character_draws = character_draws
        self.strategy_draws = strategy_draws

    def transition(self, response: None) -> Transition:
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

        if len(self.active_player.private.hand) > MAX_HAND_SIZE:
            return Discard
        return None


class Discard(State[Card]):
    def request(self) -> list[Card]:
        return self.active_player.private.hand

    def transition(self, response: Card) -> Transition:
        card = response
        deck = DeckType.CHARACTER if card.type.CHARACTER else DeckType.STRATEGY

        self.active_player.private.hand.remove(card)
        self.active_player.private.decks[deck].discarded.append(card)

        self.active_player.public.hand.remove(deck)
        self.active_player.public.decks[deck].discarded -= 1

        if len(self.active_player.private.hand) > MAX_HAND_SIZE:
            return Discard
        return None


class FellowshipPhase(SimpleState):
    def transition(self, response: None) -> Transition:
        state_machine(self.context, DeclareFellowship)
        return HuntAllocationPhase


class DeclareFellowship(BinaryChoice):
    def transition(self, response: bool) -> Transition:
        # TODO Handle ChangeGuide
        yes = response
        if yes:
            return UpdateFellowshipLocation
        return None


class UpdateFellowshipLocation(State[Region]):
    def request(self) -> list[Region]:
        fellowship = self.context.game.fellowship
        reachable = self.context.game.regions.reachable_regions(
            fellowship.location, fellowship.progress
        )
        if fellowship.is_revealed:
            # TODO Prevent declaring in enemy controlled locations
            valid = [region for region in reachable if region]
        else:
            valid = reachable
        return valid

    def transition(self, response: Region) -> Transition:
        self.context.game.fellowship.location = response
        self.context.game.fellowship.progress = 0
        return None


class HuntAllocationPhase(SimpleState):
    def transition(self, response: None) -> Transition:
        return RollPhase


class RollPhase(SimpleState):
    def transition(self, response: None) -> Transition:
        return ActionPhase


class ActionPhase(SimpleState):
    def transition(self, response: None) -> Transition:
        return VictoryCheckPhase


class VictoryCheckPhase(SimpleState):
    def transition(self, response: None) -> Transition:
        return DrawPhase
