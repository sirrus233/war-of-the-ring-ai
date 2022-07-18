from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Callable,
    Generic,
    Optional,
    Protocol,
    Sequence,
    Type,
    TypeAlias,
    TypeVar,
)

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
EventId: TypeAlias = str

C = TypeVar("C")
E = TypeVar("E", bound="Event")


class Event(Protocol):
    event: EventId


@dataclass(frozen=True, kw_only=True)
class Transition(Generic[C]):
    target: StateId
    internal: bool = False


@dataclass(frozen=True, kw_only=True)
class EventlessTransition(Generic[C], Transition[C]):
    guard: Callable[[C], bool] = lambda ctx: True
    action: Callable[[C], None] = lambda ctx: None


@dataclass(frozen=True, kw_only=True)
class EventTransition(Generic[C, E], Transition[C]):
    event: Type[E]
    guard: Callable[[C, E], bool] = lambda ctx, event: True
    action: Callable[[C, E], None] = lambda ctx, event: None


@dataclass(frozen=True)
class State(Generic[C, E]):
    on: list[EventTransition[C, E] | EventlessTransition[C]] = field(
        default_factory=list
    )
    entry: list[Callable[[C], None]] = field(default_factory=list)
    exit: list[Callable[[C], None]] = field(default_factory=list)
    always: list[EventlessTransition[C]] = field(default_factory=list)


class StateMachine(Generic[C, E]):
    def __init__(
        self,
        context: C,
        initial_state: StateId,
        final_states: Optional[Sequence[StateId]] = None,
    ) -> None:
        if final_states is None:
            final_states = []

        self._context = context
        self._current_state = self._normalize_state_id(initial_state)
        self._final_states = [self._normalize_state_id(state) for state in final_states]
        self._states: dict[str, State[C, E]] = {}

    def _normalize_state_id(self, state_id: StateId) -> str:
        return state_id if isinstance(state_id, str) else state_id.name

    def _normalize_event_id(self, event_id: EventId) -> str:
        return event_id

    def add_state(self, stateId: StateId, state: State[C, E]) -> None:
        self._states[self._normalize_state_id(stateId)] = state

    def add_states(self, states: dict[StateId, State[C, E]]) -> None:
        for state_id, state in states.items():
            self.add_state(state_id, state)

    def start(self) -> None:
        if self._current_state not in self._states:
            raise RuntimeError(
                f"No configuration for initial state: {self._current_state}."
            )

    def handle(self, event: E) -> None:
        try:
            transition = self.states[self.current_state].on[event.event]
        except KeyError:
            return

        if isinstance(transition, Transition):
            if transition.guard is not None and transition.guard(self.context, event):
                if transition.action is not None:
                    transition.action(self.context, event)
                self.current_state = transition.target
        else:
            self.current_state = transition


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


@dataclass
class Discard(Event):
    side: Side
    card: Card
    event: EventId = "DISCARD"


@dataclass
class AltrDiscard(Event):
    x: int
    event: EventId = "ALTR_DISCARD"


events = [Discard, AltrDiscard]
TEvents = TypeVar("TEvents", Discard, AltrDiscard)

sm = StateMachine[GameContext, TEvents](wotr_context, WOTRState.DRAW_PHASE)


def both_players_draw(ctx: GameContext) -> None:
    for player in ctx.players.values():
        draw(player, DeckType.CHARACTER)
        draw(player, DeckType.STRATEGY)


def valid_hand_sizes(ctx: GameContext) -> bool:
    return all(is_hand_size_legal(player) for player in ctx.players.values())


def can_discard(ctx: GameContext, event: Discard) -> bool:
    return event.card in ctx.players[event.side].private.hand


def do_discard(ctx: GameContext, event: Discard) -> None:
    discard(ctx.players[event.side], event.card)


def altr_can_discard(ctx: GameContext, event: AltrDiscard) -> bool:
    return event.x == 1


def altr_do_discard(ctx: GameContext, event: AltrDiscard) -> None:
    print(event.x)


sm.add_state(
    WOTRState.DRAW_PHASE,
    State(
        entry=[both_players_draw],
        always=[
            EventlessTransition(
                target=WOTRState.FELLOWSHIP_PHASE, guard=valid_hand_sizes
            )
        ],
        on=[
            EventTransition(
                event=Discard,
                target=".",
                guard=can_discard,
                action=do_discard,
                internal=True,
            ),
            EventTransition(
                event=AltrDiscard,
                target=".",
                guard=altr_can_discard,
                action=altr_do_discard,
                internal=True,
            ),
        ],
    ),
)

sm.handle(AltrDiscard(5))
