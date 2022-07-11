from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Generic, Optional, Sequence, Type, TypeAlias, TypeVar

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
    ALLOCATE_EYES = auto()
    VICTORY_PHASE = auto()
    GAME_OVER = auto()


class Event(Enum):
    CONFIRM = auto()
    UNDO = auto()
    FREE_DISCARD = auto()
    SHADOW_DISCARD = auto()
    DECLARE_FELLOWSHIP = auto()
    ENTER_MORDOR = auto()
    CHANGE_GUIDE = auto()
    ALLOCATE_EYES = auto()


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

    def valid_transitions(self) -> Sequence[E]:
        return [event for event in self.transitions if self.transitions[event].guard()]

    def handle(self, event: E, payload: Any) -> Optional[S]:
        if (
            event in self.valid_transitions()
            and payload in self.transitions[event].payloads()
        ):
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


class FellowshipPhaseDeclare(WOTRStateConfig):
    class DeclareFellowship(WOTREventConfig[None]):
        def guard(self) -> bool:
            return not self.context.game.fellowship.is_revealed

        def handle(self, payload: None) -> Optional[State]:
            return State.DETERMINE_FELLOWSHIP

    def on_enter(self) -> Optional[State]:
        if Event.DECLARE_FELLOWSHIP not in self.valid_transitions():
            return State.FELLOWSHIP_PHASE_MORDOR

    def on_exit(self) -> Optional[State]:
        if fellowship_can_heal(self.context.game):
            corruption = self.context.game.fellowship.corruption
            self.context.game.fellowship.corruption = max(0, corruption - 1)

    def __init__(self, state: State, context: GameContext) -> None:
        super().__init__(state, context)
        self.add_event(
            FellowshipPhaseDeclare.DeclareFellowship(
                Event.DECLARE_FELLOWSHIP, self.context
            )
        )


class FellowshipPhaseMordor(WOTRStateConfig):
    class EnterMordor(WOTREventConfig[None]):
        def guard(self) -> bool:
            return self.context.game.fellowship.location in MORDOR_ENTRANCES

        def handle(self, payload: None) -> Optional[State]:
            self.context.game.fellowship.location = MORDOR
            self.context.game.fellowship.progress = 0

    def on_enter(self) -> Optional[State]:
        if Event.ENTER_MORDOR not in self.valid_transitions():
            return State.FELLOWSHIP_PHASE_GUIDE

    def __init__(self, state: State, context: GameContext) -> None:
        super().__init__(state, context)
        self.add_event(
            FellowshipPhaseMordor.EnterMordor(Event.ENTER_MORDOR, self.context)
        )


class FellowshipPhaseGuide(WOTRStateConfig):
    class ChangeGuide(WOTREventConfig[Character]):
        def payloads(self) -> Sequence[Character]:
            return valid_guides(self.context.game)

        def handle(self, payload: Character) -> Optional[State]:
            self.context.game.fellowship.guide = payload
            return State.ALLOCATE_EYES

    def __init__(self, state: State, context: GameContext) -> None:
        super().__init__(state, context)
        self.add_event(
            FellowshipPhaseGuide.ChangeGuide(Event.CHANGE_GUIDE, self.context)
        )


class AllocateEyes(WOTRStateConfig):
    class AllocateEyes(WOTREventConfig[int]):
        def payloads(self) -> Sequence[int]:
            game = self.context.game
            return list(range(minimum_hunt_dice(game), maximum_hunt_dice(game) + 1))

        def handle(self, payload: int) -> Optional[State]:
            self.context.game.hunt_box.eyes = payload
            return State.VICTORY_PHASE

    def __init__(self, state: State, context: GameContext) -> None:
        super().__init__(state, context)
        self.add_event(AllocateEyes.AllocateEyes(Event.ALLOCATE_EYES, self.context))


class VictoryPhase(WOTRStateConfig):
    def on_enter(self) -> Optional[State]:
        if self.context.players[Side.SHADOW].public.victory_points >= SHADOW_VP_GOAL:
            return State.GAME_OVER
        if self.context.players[Side.FREE].public.victory_points >= FREE_VP_GOAL:
            return State.GAME_OVER
        return State.DRAW_PHASE

    def __init__(self, state: State, context: GameContext) -> None:
        super().__init__(state, context)


###################################################################################

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


class StateMachine(Generic[S, E, C]):
    def __init__(self, initial_state: S, final_states: Sequence[S], context: C) -> None:
        self.states: dict[S, StateConfig[S, E, C]] = {}
        self.current_state = None
        self.final_states = final_states
        self.context = context

    def add_state(self, state: S, config: StateConfig[S, E, C]) -> None:
        self.states[state] = config

    def transition(self, next_state: S) -> None:
        self.current_state.on_exit()
        self.current_state = next_state(self, self._game, self._players)
        self.current_state.on_enter()

    def start(self) -> None:
        if self.current_state is None:

        while self.current_state not in self.final_states:

        self.current_state.on_enter()
