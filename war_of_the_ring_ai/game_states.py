# pylint: disable=useless-return

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from collections import Counter
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

from war_of_the_ring_ai.activities import (
    discard,
    draw,
    fellowship_can_heal,
    maximum_hunt_dice,
    minimum_hunt_dice,
    rollable_dice,
    valid_guides,
)
from war_of_the_ring_ai.constants import (
    FREE_ACTION_DIE,
    FREE_VP_GOAL,
    MAX_HAND_SIZE,
    SHADOW_ACTION_DIE,
    SHADOW_VP_GOAL,
    DeckType,
    DieResult,
    Side,
)
from war_of_the_ring_ai.game_data import GameData, PlayerData, PrivatePlayerData
from war_of_the_ring_ai.game_objects import Card, Character, Region

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
        discard(self.active_player, response)

        if len(self.active_player.private.hand) > MAX_HAND_SIZE:
            return Discard
        return None


class FellowshipPhase(SimpleState):
    def transition(self, response: None) -> Transition:
        fellowship = self.context.game.fellowship

        if fellowship.progress > 0:
            state_machine(self.context, AskDeclareFellowship)

        if fellowship_can_heal(self.context.game):
            fellowship.corruption = max(0, fellowship.corruption - 1)

        if len(valid_guides(self.context.game)) > 1:
            state_machine(self.context, AskSelectGuide)

        self.context.game.active_side = Side.SHADOW
        return HuntAllocationPhase


class AskDeclareFellowship(BinaryChoice):
    def transition(self, response: bool) -> Transition:
        if response:
            return DeclareFellowship
        return None


class DeclareFellowship(State[Region]):
    def request(self) -> list[Region]:
        fellowship = self.context.game.fellowship
        reachable = self.context.game.regions.reachable_regions(
            fellowship.location, fellowship.progress
        )
        return reachable

    def transition(self, response: Region) -> Transition:
        self.context.game.fellowship.location = response
        self.context.game.fellowship.progress = 0
        return None


class AskSelectGuide(BinaryChoice):
    def transition(self, response: bool) -> Transition:
        if response:
            return SelectGuide
        return None


class SelectGuide(State[Character]):
    def request(self) -> list[Character]:
        return valid_guides(self.context.game)

    def transition(self, response: Character) -> Transition:
        self.context.game.fellowship.guide = response
        return None


class HuntAllocationPhase(State[int]):
    def request(self) -> list[int]:
        return list(
            range(
                minimum_hunt_dice(self.context.game),
                maximum_hunt_dice(self.context.game) + 1,
            )
        )

    def transition(self, response: int) -> Transition:
        hunt_box = self.context.game.hunt_box
        hunt_box.character = 0
        hunt_box.eyes = response
        return RollPhase


class RollPhase(SimpleState):
    def transition(self, response: None) -> Transition:
        dice = {Side.FREE: FREE_ACTION_DIE, Side.SHADOW: SHADOW_ACTION_DIE}
        for side in Side:
            player = self.context.players[side]
            die = dice[side]
            player.public.dice = Counter(
                random.choice(die)
                for _ in range(rollable_dice(player, self.context.game))
            )

        shadow_player = self.context.players[Side.SHADOW]
        self.context.game.hunt_box.eyes += shadow_player.public.dice[DieResult.EYE]
        shadow_player.public.dice.pop(DieResult.EYE, None)

        return ActionPhase


class ActionPhase(SimpleState):
    def transition(self, response: None) -> Transition:
        # TODO Actions
        print(self.context.players[Side.FREE].public.dice)
        print(self.context.players[Side.SHADOW].public.dice)
        return VictoryCheckPhase


class VictoryCheckPhase(SimpleState):
    def transition(self, response: None) -> Transition:
        # TODO Victory state
        if self.context.players[Side.SHADOW].public.victory_points >= SHADOW_VP_GOAL:
            return None
        if self.context.players[Side.FREE].public.victory_points >= FREE_VP_GOAL:
            return None
        return DrawPhase
