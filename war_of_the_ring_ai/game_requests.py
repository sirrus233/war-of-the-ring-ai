from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from war_of_the_ring_ai.game_objects import (
    NATION_SIDE,
    Action,
    Card,
    CardCategory,
    CharacterID,
    Companion,
    DieResult,
    Fellowship,
    Nation,
    PoliticalStatus,
    Region,
    RegionMap,
    Side,
)

if TYPE_CHECKING:
    from war_of_the_ring_ai.game_state import PlayerState


@dataclass
class Request:
    options: list[Any] = field(init=False)


@dataclass
class Discard(Request):
    hand: list[Card]

    def __post_init__(self) -> None:
        self.options: list[Card] = self.hand


@dataclass
class ChangeGuide(Request):
    companions: list[Companion]

    def __post_init__(self) -> None:
        max_level = max(companion.level for companion in self.companions)
        self.options: list[Companion] = [
            companion for companion in self.companions if companion.level == max_level
        ]


@dataclass
class DeclareFellowship(Request):
    def __post_init__(self) -> None:
        self.options: list[bool] = [True, False]


@dataclass
class DeclareFellowshipLocation(Request):
    location: Region
    progress: int

    def __post_init__(self) -> None:
        self.options: list[Region] = list(
            self.location.reachable_regions(self.progress)
        )


@dataclass
class EnterMordor(Request):
    def __post_init__(self) -> None:
        self.options: list[bool] = [True, False]


@dataclass
class HuntAllocation(Request):
    min_allocation: int
    max_dice: int
    companions: int

    def __post_init__(self) -> None:
        max_allocation = min(self.companions, self.max_dice)
        self.options: list[int] = list(range(self.min_allocation, max_allocation + 1))


@dataclass
class PassTurn(Request):
    def __post_init__(self) -> None:
        self.options: list[bool] = [True, False]


@dataclass
class ChooseDie(Request):
    dice: list[DieResult]

    def __post_init__(self) -> None:
        self.options: list[DieResult] = self.dice


@dataclass
class CharacterAction(Request):
    side: Side
    fellowship: Fellowship
    regions: RegionMap

    def __post_init__(self) -> None:
        self.options: list[Action] = [Action.SKIP]

        friendly_armies_with_leadership = [
            region.army
            for region in self.regions.with_army_units(self.side)
            if region.army is not None and region.army.leadership() > 0
        ]

        if any(army.valid_moves() for army in friendly_armies_with_leadership):
            self.options.append(Action.LEADER_MOVE)

        if any(army.valid_attacks() for army in friendly_armies_with_leadership):
            self.options.append(Action.LEADER_ATTACK)

        if self.side == Side.FREE:
            if self.fellowship.revealed:
                self.options.append(Action.HIDE_FELLOWSHIP)
            else:
                self.options.append(Action.MOVE_FELLOWSHIP)

            if self.fellowship.companions:
                self.options.append(Action.SEPARATE_COMPANIONS)

            if self.regions.with_characters(Side.FREE):
                self.options.append(Action.MOVE_COMPANIONS)

        else:
            has_minions = len(self.regions.with_characters(Side.SHADOW)) > 0
            has_nazgul = any(
                region.army is not None and region.army.leaders() > 0
                for region in self.regions.with_army_units(Side.SHADOW)
            )
            if has_minions or has_nazgul:
                self.options.append(Action.MOVE_MINIONS)


@dataclass
class ArmyAction(Request):
    side: Side
    regions: RegionMap

    def __post_init__(self) -> None:
        self.options: list[Action] = [Action.SKIP]

        friendly_armies = [
            region.army
            for region in self.regions.with_army_units(self.side)
            if region.army is not None
        ]

        if any(army.valid_moves() for army in friendly_armies):
            self.options.append(Action.MOVE_ARMIES)

        if any(army.valid_attacks() for army in friendly_armies):
            self.options.append(Action.ATTACK)


@dataclass
class MusterAction(Request):
    side: Side
    regions: RegionMap
    politics: dict[Nation, PoliticalStatus]
    reinforcements: dict[Nation, list[int]]
    characters_mustered: set[CharacterID]
    fellowship: Fellowship

    def __post_init__(self) -> None:
        self.options: list[Action] = [Action.SKIP]

        if self.can_politic():
            self.options.append(Action.DIPLOMACY)

        if self.can_muster()[0]:
            self.options.append(Action.MUSTER_REGULAR_REGULAR)
        if self.can_muster()[1]:
            self.options.append(Action.MUSTER_ELITE)
        if self.can_muster()[2]:
            self.options.append(Action.MUSTER_LEADER_LEADER)
        if self.can_muster()[0] and self.can_muster()[2]:
            self.options.append(Action.MUSTER_REGULAR_LEADER)

        if self.can_muster_saruman():
            self.options.append(Action.MUSTER_SARUMAN)
        if self.can_muster_witch_king():
            self.options.append(Action.MUSTER_WITCH_KING)
        if self.can_muster_mouth_of_sauron():
            self.options.append(Action.MUSTER_MOUTH_OF_SAURON)

    def can_politic(self) -> bool:
        return any(
            self.politics[nation].can_advance() for nation in NATION_SIDE[self.side]
        )

    def can_muster(self) -> tuple[bool, bool, bool]:
        available_regulars = 0
        available_elites = 0
        available_leaders = 0
        for nation in NATION_SIDE[self.side]:
            # Mustering is legal if a nation is at war, has units in reinforcements, and
            # has an unconquered settlement to muster in.
            if self.politics[nation].is_at_war() and any(
                region.is_free(self.side) for region in self.regions.with_nation(nation)
            ):
                available_regulars += self.reinforcements[nation][0]
                available_elites += self.reinforcements[nation][1]
                available_leaders += self.reinforcements[nation][2]
        return available_regulars > 0, available_elites > 0, available_leaders > 0

    def can_muster_saruman(self) -> bool:
        if CharacterID.SARUMAN in self.characters_mustered:
            return False
        return self.politics[Nation.ISENGARD].is_at_war()

    def can_muster_witch_king(self) -> bool:
        if CharacterID.WITCH_KING in self.characters_mustered:
            return False
        return any(
            self.politics[nation].is_at_war()
            for nation in Nation
            if nation in NATION_SIDE[Side.FREE]
        )

    def can_muster_mouth_of_sauron(self) -> bool:
        if CharacterID.MOUTH_OF_SAURON in self.characters_mustered:
            return False
        return self.fellowship.in_mordor() or all(
            self.politics[nation].is_at_war() for nation in Nation
        )


@dataclass
class HybridAction(Request):
    army_action_request: ArmyAction
    muster_action_request: MusterAction

    def __post_init__(self) -> None:
        self.options: list[Action] = [Action.SKIP]
        self.options.extend(self.army_action_request.options)
        self.options.extend(self.muster_action_request.options)


@dataclass
class PalantirAction(Request):
    player: "PlayerState"

    def __post_init__(self) -> None:
        self.options: list[Action] = [Action.SKIP]

        if self.player.character_deck:
            self.options.append(Action.DRAW_CHARACTER_EVENT)
        if self.player.strategy_deck:
            self.options.append(Action.DRAW_STRATEGY_EVENT)
        if any(card.category == CardCategory.CHARACTER for card in self.player.hand):
            self.options.append(Action.PLAY_CHARACTER_EVENT)
        if any(card.category == CardCategory.ARMY for card in self.player.hand):
            self.options.append(Action.PLAY_ARMY_EVENT)
        if any(card.category == CardCategory.MUSTER for card in self.player.hand):
            self.options.append(Action.PLAY_MUSTER_EVENT)


@dataclass
class WillAction(Request):
    characters_mustered: set[CharacterID]
    companions: dict[CharacterID, Companion]
    regions: RegionMap

    character_action_request: CharacterAction
    hybrid_action_request: HybridAction
    palantir_action_request: PalantirAction

    def __post_init__(self) -> None:
        self.options: list[Action] = [Action.SKIP]

        self.options.extend(self.character_action_request.options)
        self.options.extend(self.hybrid_action_request.options)
        self.options.extend(self.palantir_action_request.options)

        if self.can_muster_gandalf():
            self.options.append(Action.MUSTER_GANDALF)

        if self.can_muster_aragorn():
            self.options.append(Action.MUSTER_ARAGORN)

    def can_muster_gandalf(self) -> bool:
        gandalf = CharacterID.GANDALF_GREY
        minions = (
            CharacterID.SARUMAN,
            CharacterID.WITCH_KING,
            CharacterID.MOUTH_OF_SAURON,
        )
        minion_mustered = any(minion in self.characters_mustered for minion in minions)
        return (
            minion_mustered
            and gandalf not in self.characters_mustered
            and gandalf not in self.companions
        )

    def can_muster_aragorn(self) -> bool:
        aragorn_regions = {
            self.regions.with_name("Dol Amroth"),
            self.regions.with_name("Pelargir"),
            self.regions.with_name("Minas Tirith"),
        }
        return any(
            region.army.has_character(CharacterID.STRIDER)
            for region in aragorn_regions
            if region.army
        )
