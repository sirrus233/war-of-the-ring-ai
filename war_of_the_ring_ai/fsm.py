from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Generic, Optional, Sequence, TypeAlias, TypeVar

from war_of_the_ring_ai.activities import discard, draw, is_hand_size_legal
from war_of_the_ring_ai.constants import DeckType, Side
from war_of_the_ring_ai.game_data import (
    GameData,
    PlayerData,
    init_private_player_data,
    init_public_player_data,
)
from war_of_the_ring_ai.game_objects import Card

StateId: TypeAlias = Enum | str
EventId: TypeAlias = Enum | str


class Event(ABC):
    event: EventId


C = TypeVar("C")
E = TypeVar("E", bound=Event)


@dataclass
class EventlessTransition(Generic[C]):
    target: StateId
    guard: Optional[Callable[[C], bool]] = None
    action: Optional[Callable[[C], None]] = None
    internal: bool = False


@dataclass
class Transition(Generic[C]):
    event: EventId
    target: StateId
    guard: Optional[Callable[[C, Event], bool]] = None
    action: Optional[Callable[[C, Event], None]] = None
    internal: bool = False


@dataclass
class State(Generic[C]):
    state: StateId
    on: list[tuple[Event, StateId] | Transition[C]] = field(default_factory=list)
    entry: list[Callable[[C], None]] = field(default_factory=list)
    exit: list[Callable[[C], None]] = field(default_factory=list)
    always: list[EventlessTransition[C]] = field(default_factory=list)


class StateMachine(Generic[C]):
    def __init__(
        self,
        context: C,
        initial_state: StateId,
        final_states: Optional[Sequence[StateId]] = None,
    ) -> None:
        self.context = context
        self.current_state = initial_state
        self.final_states = final_states
        self.states: dict[StateId, State[C]] = {}

    def add_state(self, state: State[C]) -> None:
        self.states[state.state] = state


########


@dataclass(frozen=True)
class GameContext:
    game: GameData
    players: dict[Side, PlayerData]


wotr_context = GameContext(
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


class WOTRState(Enum):
    DRAW_PHASE = 1
    FELLOWSHIP_PHASE = 2


class WOTREvent(Enum):
    FREE_DISCARD = 1
    SHADOW_DISCARD = 2


sm = StateMachine(wotr_context, "ab")


def both_players_draw(ctx: GameContext) -> None:
    for player in ctx.players.values():
        draw(player, DeckType.CHARACTER)
        draw(player, DeckType.STRATEGY)


def valid_hand_sizes(ctx: GameContext) -> bool:
    return all(is_hand_size_legal(player) for player in ctx.players.values())


def can_discard(ctx: GameContext, event: Event) -> bool:
    if isinstance(event, Discard):
        return event.card in ctx.players[event.side].private.hand
    return False


def do_discard(ctx: GameContext, event: Event) -> None:
    if isinstance(event, Discard):
        discard(ctx.players[event.side], event.card)


class Discard(Event, ABC):
    def __init__(self, event: EventId, side: Side, card: Card) -> None:
        self.event = event
        self.side = side
        self.card = card


class FreeDiscard(Discard):
    def __init__(self, card: Card) -> None:
        super().__init__(WOTREvent.FREE_DISCARD, Side.FREE, card)


class ShadowDiscard(Discard):
    def __init__(self, card: Card) -> None:
        super().__init__(WOTREvent.SHADOW_DISCARD, Side.SHADOW, card)


sm.add_state(
    State(
        WOTRState.DRAW_PHASE,
        entry=[both_players_draw],
        always=[
            EventlessTransition(
                target=WOTRState.FELLOWSHIP_PHASE, guard=valid_hand_sizes
            )
        ],
        on=[
            Transition(
                WOTREvent.FREE_DISCARD, ".", guard=can_discard, action=do_discard
            ),
            Transition(
                WOTREvent.SHADOW_DISCARD, ".", guard=can_discard, action=do_discard
            ),
        ],
    )
)


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
"""


# on: list[tuple[Event, StateId] | Transition[C, Event]] = field(default_factory=list)
