from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Sequence, TypeAlias, TypeVar

from fsm import Event, EventlessTransition, State, StateMachine, Transition

from war_of_the_ring_ai.activities import (
    discard,
    draw,
    fellowship_can_heal,
    is_hand_size_legal,
    maximum_hunt_dice,
    minimum_hunt_dice,
    valid_guides,
)
from war_of_the_ring_ai.constants import (
    FREE_VP_GOAL,
    MAX_HAND_SIZE,
    MORDOR_ENTRANCES,
    SHADOW_VP_GOAL,
    DeckType,
    Side,
)
from war_of_the_ring_ai.game_data import (
    GameData,
    PlayerData,
    init_private_player_data,
    init_public_player_data,
)
from war_of_the_ring_ai.game_objects import MORDOR, Card, Character


class WOTRState(Enum):
    DRAW_PHASE = auto()
    FELLOWSHIP_PHASE_DECLARE = auto()
    FELLOWSHIP_PHASE_MORDOR = auto()
    FELLOWSHIP_PHASE_GUIDE = auto()
    DETERMINE_FELLOWSHIP = auto()
    ALLOCATE_EYES = auto()
    VICTORY_PHASE = auto()
    GAME_OVER = auto()


class EventId(Enum):
    CONFIRM = auto()
    UNDO = auto()
    FREE_DISCARD = auto()
    SHADOW_DISCARD = auto()
    DECLARE_FELLOWSHIP = auto()
    ENTER_MORDOR = auto()
    CHANGE_GUIDE = auto()
    ALLOCATE_EYES = auto()


@dataclass(frozen=True)
class GameContext:
    game: GameData
    players: dict[Side, PlayerData]


"""
class DrawPhase(WOTRState):
    class Discard(WOTREvent[Card], ABC):
        def __init__(self, context: GameContext) -> None:
            super().__init__(context)
            self.player = self.context.players[Side.FREE]

        def guard(self) -> bool:
            return len(self.player.private.hand) > MAX_HAND_SIZE

        def payloads(self) -> Sequence[Card]:
            return self.player.private.hand

        def handle(self, payload: Card) -> Optional[StateId]:
            discard(self.player, payload)
            if all(
                is_hand_size_legal(player) for player in self.context.players.values()
            ):
                return StateId.FELLOWSHIP_PHASE_DECLARE

    class FreeDiscard(Discard):
        pass

    class ShadowDiscard(Discard):
        pass

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self.add_event(DrawPhase.FreeDiscard(self.context))
        self.add_event(DrawPhase.ShadowDiscard(self.context))

    def on_enter(self) -> Optional[StateId]:
        for player in self.context.players.values():
            draw(player, DeckType.CHARACTER)
            draw(player, DeckType.STRATEGY)

        if all(is_hand_size_legal(player) for player in self.context.players.values()):
            return StateId.FELLOWSHIP_PHASE_DECLARE


class FellowshipPhaseDeclare(WOTRState):
    class DeclareFellowship(WOTREvent[None]):
        def guard(self) -> bool:
            return not self.context.game.fellowship.is_revealed

        def handle(self, payload: None) -> Optional[StateId]:
            return StateId.DETERMINE_FELLOWSHIP

    def on_enter(self) -> Optional[StateId]:
        if EventId.DECLARE_FELLOWSHIP not in self.valid_transitions():
            return StateId.FELLOWSHIP_PHASE_MORDOR

    def on_exit(self) -> Optional[StateId]:
        if fellowship_can_heal(self.context.game):
            corruption = self.context.game.fellowship.corruption
            self.context.game.fellowship.corruption = max(0, corruption - 1)

    def __init__(self, state: StateId, context: GameContext) -> None:
        super().__init__(state, context)
        self.add_event(
            FellowshipPhaseDeclare.DeclareFellowship(
                EventId.DECLARE_FELLOWSHIP, self.context
            )
        )


class FellowshipPhaseMordor(WOTRState):
    class EnterMordor(WOTREvent[None]):
        def guard(self) -> bool:
            return self.context.game.fellowship.location in MORDOR_ENTRANCES

        def handle(self, payload: None) -> Optional[StateId]:
            self.context.game.fellowship.location = MORDOR
            self.context.game.fellowship.progress = 0

    def on_enter(self) -> Optional[StateId]:
        if EventId.ENTER_MORDOR not in self.valid_transitions():
            return StateId.FELLOWSHIP_PHASE_GUIDE

    def __init__(self, state: StateId, context: GameContext) -> None:
        super().__init__(state, context)
        self.add_event(
            FellowshipPhaseMordor.EnterMordor(EventId.ENTER_MORDOR, self.context)
        )


class FellowshipPhaseGuide(WOTRState):
    class ChangeGuide(WOTREvent[Character]):
        def payloads(self) -> Sequence[Character]:
            return valid_guides(self.context.game)

        def handle(self, payload: Character) -> Optional[StateId]:
            self.context.game.fellowship.guide = payload
            return StateId.ALLOCATE_EYES

    def __init__(self, state: StateId, context: GameContext) -> None:
        super().__init__(state, context)
        self.add_event(
            FellowshipPhaseGuide.ChangeGuide(EventId.CHANGE_GUIDE, self.context)
        )


class AllocateEyes(WOTRState):
    class AllocateEyes(WOTREvent[int]):
        def payloads(self) -> Sequence[int]:
            game = self.context.game
            return list(range(minimum_hunt_dice(game), maximum_hunt_dice(game) + 1))

        def handle(self, payload: int) -> Optional[StateId]:
            self.context.game.hunt_box.eyes = payload
            return StateId.VICTORY_PHASE

    def __init__(self, state: StateId, context: GameContext) -> None:
        super().__init__(state, context)
        self.add_event(AllocateEyes.AllocateEyes(EventId.ALLOCATE_EYES, self.context))


class VictoryPhase(WOTRState):
    def on_enter(self) -> Optional[StateId]:
        if self.context.players[Side.SHADOW].public.victory_points >= SHADOW_VP_GOAL:
            return StateId.GAME_OVER
        if self.context.players[Side.FREE].public.victory_points >= FREE_VP_GOAL:
            return StateId.GAME_OVER
        return StateId.FREEDRAW_PHASE

    def __init__(self, state: StateId, context: GameContext) -> None:
        super().__init__(state, context)
"""


context = GameContext(
    GameData(),
    {
        Side.FREE: PlayerData(
            public=init_public_player_data(Side.FREE),
            private=init_private_player_data(Side.FREE),
        ),
        Side.SHADOW: PlayerData(
            public=init_public_player_data(Side.SHADOW),
            private=init_private_player_data(Side.SHADOW),
        ),
    },
)


@dataclass
class Confirm(Event):
    ...


@dataclass
class Undo(Event):
    ...


@dataclass
class Discard(Event):
    side: Side
    card: Card


TEvents = TypeVar("TEvents", Confirm, Undo, Discard)

sm = StateMachine[GameContext, TEvents](context, WOTRState.DRAW_PHASE)


def both_players_draw(ctx: GameContext) -> None:
    for player in ctx.players.values():
        draw(player, DeckType.CHARACTER)
        draw(player, DeckType.STRATEGY)


def print_hands(ctx: GameContext) -> None:
    for player in ctx.players.values():
        print(f"***{player.public.side}***")
        for card in player.private.hand:
            print(card)
    print("--------")


def valid_hand_sizes(ctx: GameContext) -> bool:
    return all(is_hand_size_legal(player) for player in ctx.players.values())


def can_discard(ctx: GameContext, event: Discard) -> bool:
    return event.card in ctx.players[event.side].private.hand


def do_discard(ctx: GameContext, event: Discard) -> None:
    discard(ctx.players[event.side], event.card)


sm.add_state(
    WOTRState.DRAW_PHASE,
    State(
        entry=[both_players_draw, print_hands],
        always=[
            EventlessTransition(target=WOTRState.DRAW_PHASE, guard=valid_hand_sizes)
        ],
        on=[Transition(event=Discard, guard=can_discard, action=do_discard)],
    ),
)

sm.start()
sm.send(Discard(Side.FREE, context.players[Side.FREE].private.hand[0]))
sm.send(Discard(Side.FREE, context.players[Side.FREE].private.hand[0]))
sm.send(Discard(Side.SHADOW, context.players[Side.SHADOW].private.hand[0]))
sm.send(Discard(Side.SHADOW, context.players[Side.SHADOW].private.hand[0]))
