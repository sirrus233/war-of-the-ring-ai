from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Generic, Optional, Sequence, Type, TypeAlias, TypeVar

from war_of_the_ring_ai.activities import discard, draw, is_hand_size_legal
from war_of_the_ring_ai.constants import (
    MAX_HAND_SIZE,
    MORDOR_ENTRANCES,
    CharacterID,
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

S = TypeVar("S", bound=Enum)
E = TypeVar("E", bound=Enum)
C = TypeVar("C")
P = TypeVar("P")


@dataclass(frozen=True)
class GameContext:
    game: GameData
    players: dict[Side, PlayerData]


class State(Enum):
    DRAW_PHASE = auto()
    FELLOWSHIP_PHASE_DECLARE = auto()
    FELLOWSHIP_PHASE_MORDOR = auto()
    FELLOWSHIP_PHASE_GUIDE = auto()
    DETERMINE_FELLOWSHIP = auto()


class Event(Enum):
    CONFIRM = auto()
    UNDO = auto()
    FREE_DISCARD = auto()
    SHADOW_DISCARD = auto()
    DECLARE_FELLOWSHIP = auto()
    ENTER_MORDOR = auto()
    CHANGE_GUIDE = auto()


class EventConfig(Generic[S, E, C, P], ABC):
    def __init__(self, event: E, context: C) -> None:
        self.event = event
        self.context = context

    def guard(self) -> bool:
        return True

    def payloads(self) -> Sequence[P]:
        return []

    @abstractmethod
    def handle(self, payload: P) -> Optional[S]:
        ...


class StateConfig(Generic[S, E, C], ABC):
    def __init__(self, state: S, context: C) -> None:
        self.state = state
        self.context = context
        self.transitions: dict[E, EventConfig[S, E, C, Any]] = {}

    def on_enter(self) -> Optional[S]:
        return None

    def on_exit(self) -> Optional[S]:
        return None

    def add_event(self, event: EventConfig[S, E, C, Any]) -> None:
        self.transitions[event.event] = event

    def handle(self, event: E, payload: Any) -> Optional[S]:
        if event in self.transitions and payload in self.transitions[event].payloads():
            if self.transitions[event].guard():
                return self.transitions[event].handle(payload)


WOTRStateConfig: TypeAlias = StateConfig[State, Event, GameContext]
WOTREventConfig: TypeAlias = EventConfig[State, Event, GameContext, P]


class DrawPhase(WOTRStateConfig):
    class Discard(WOTREventConfig[Card]):
        def __init__(self, event: Event, context: GameContext, side: Side) -> None:
            super().__init__(event, context)
            self.player = self.context.players[side]

        def guard(self) -> bool:
            return len(self.player.private.hand) > MAX_HAND_SIZE

        def payloads(self) -> Sequence[Card]:
            return self.player.private.hand

        def handle(self, payload: Card) -> Optional[State]:
            discard(self.player, payload)
            if all(
                is_hand_size_legal(player) for player in self.context.players.values()
            ):
                return State.FELLOWSHIP_PHASE_DECLARE
            return None

    def __init__(self, state: State, context: GameContext) -> None:
        super().__init__(state, context)
        self.add_event(DrawPhase.Discard(Event.FREE_DISCARD, self.context, Side.FREE))
        self.add_event(
            DrawPhase.Discard(Event.SHADOW_DISCARD, self.context, Side.SHADOW)
        )

    def on_enter(self) -> Optional[State]:
        for player in self.context.players.values():
            draw(player, DeckType.CHARACTER)
            draw(player, DeckType.STRATEGY)

        if all(is_hand_size_legal(player) for player in self.context.players.values()):
            return State.FELLOWSHIP_PHASE_DECLARE

        return None


class FellowshipPhaseDeclare(WOTRStateConfig):
    class DeclareFellowship(WOTREventConfig[None]):
        def guard(self) -> bool:
            return not self.context.game.fellowship.is_revealed

        def handle(self, payload: None) -> Optional[State]:
            return State.DETERMINE_FELLOWSHIP

    def __init__(self, state: State, context: GameContext) -> None:
        super().__init__(state, context)


class FellowshipPhaseMordor(WOTRStateConfig):
    class EnterMordor(WOTREventConfig[None]):
        def guard(self) -> bool:
            return self.context.game.fellowship.location in MORDOR_ENTRANCES

        def handle(self, payload: None) -> Optional[State]:
            self.context.game.fellowship.location = MORDOR
            self.context.game.fellowship.progress = 0
            return None

    def __init__(self, state: State, context: GameContext) -> None:
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

class StateMachine:
    def __init__(self, initial_state: Type[State]) -> None:
        self._game = GameData()
        self._players = {
            Side.FREE: PlayerData(
                public=init_public_player_data(Side.FREE),
                private=init_private_player_data(Side.FREE),
            ),
            Side.SHADOW: PlayerData(
                public=init_public_player_data(Side.SHADOW),
                private=init_private_player_data(Side.SHADOW),
            ),
        }
        self.current_state = initial_state(self, self._game, self._players)

    def transition(self, next_state: Type[State]) -> None:
        self.current_state.on_exit()
        self.current_state = next_state(self, self._game, self._players)
        self.current_state.on_enter()

    def start(self) -> None:
        self.current_state.on_enter()
"""
