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


class Event(Protocol):
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
class Transition(Generic[C, E]):
    event: Type[E]
    target: StateId
    guard: Optional[Callable[[C, E], bool]] = None
    action: Optional[Callable[[C, E], None]] = None
    internal: bool = False


@dataclass
class State(Generic[C, E]):
    on: dict[EventId, StateId | Transition[C, E]] = field(default_factory=dict)
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
        self.context = context
        self.current_state = initial_state
        self.final_states = final_states
        self.states: dict[StateId, State[C, E]] = {}

    def add_state(self, stateId: StateId, state: State[C, E]) -> None:
        self.states[stateId] = state

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
        on={
            "ALTR_DISCARD": Transition(
                Discard,
                ".",
                guard=can_discard,
                action=do_discard,
                internal=True,
            ),
            "DISCARD": Transition(
                AltrDiscard,
                ".",
                guard=altr_can_discard,
                action=altr_do_discard,
                internal=True,
            ),
        },
    ),
)

sm.handle(AltrDiscard(5))
