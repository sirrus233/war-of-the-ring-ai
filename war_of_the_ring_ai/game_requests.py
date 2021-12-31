from dataclasses import dataclass, field
from itertools import combinations
from typing import Any, Optional

from war_of_the_ring_ai.game_objects import (
    NATION_SIDE,
    Action,
    Army,
    ArmyUnit,
    Card,
    CardCategory,
    Casualty,
    Character,
    CharacterID,
    Companion,
    DieResult,
    Fellowship,
    Nation,
    PoliticalStatus,
    Region,
    RegionMap,
    Settlement,
    Side,
    UnitType,
)
from war_of_the_ring_ai.game_state import ALL_COMPANIONS, ALL_MINIONS, PlayerState


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
    casualty: Optional[Companion] = None

    def __post_init__(self) -> None:
        max_level = max(companion.level for companion in self.companions)
        self.options: list[Companion] = [
            companion for companion in self.companions if companion.level == max_level
        ]
        if self.casualty is not None:
            self.options.remove(self.casualty)
        if len(self.options) == 0:
            self.options.append(ALL_COMPANIONS[CharacterID.GOLLUM])


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
    characters_mustered: set[Character]
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
        regulars = 0
        elites = 0
        leaders = 0
        for nation in NATION_SIDE[self.side]:
            # Mustering is legal if a nation is at war, has units in reinforcements, and
            # has an unconquered settlement to muster in.
            if self.politics[nation].is_at_war() and any(
                region.is_free(self.side) for region in self.regions.with_nation(nation)
            ):
                regulars += self.reinforcements[nation][UnitType.REGULAR.value]
                elites += self.reinforcements[nation][UnitType.ELITE.value]
                leaders += self.reinforcements[nation][UnitType.LEADER.value]
        return regulars > 0, elites > 0, leaders > 0

    def can_muster_saruman(self) -> bool:
        if ALL_MINIONS[CharacterID.SARUMAN] in self.characters_mustered:
            return False
        if self.regions.with_name("Orthanc").is_conquered:
            return False
        return self.politics[Nation.ISENGARD].is_at_war()

    def can_muster_witch_king(self) -> bool:
        if ALL_MINIONS[CharacterID.WITCH_KING] in self.characters_mustered:
            return False
        sauron_army = any(
            region.army
            for region in self.regions.with_army_units(Side.SHADOW)
            if region.army is not None
            and any(unit.nation == Nation.SAURON for unit in region.army.units)
        )
        sauron_at_war = self.politics[Nation.SAURON].is_at_war()
        free_nation_at_war = any(
            self.politics[nation].is_at_war()
            for nation in Nation
            if nation in NATION_SIDE[Side.FREE]
        )
        return sauron_army and sauron_at_war and free_nation_at_war

    def can_muster_mouth_of_sauron(self) -> bool:
        if ALL_MINIONS[CharacterID.MOUTH_OF_SAURON] in self.characters_mustered:
            return False
        if all(
            region.is_conquered for region in self.regions.with_nation(Nation.SAURON)
        ):
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
    player: PlayerState

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
    characters_mustered: set[Character]
    companions: list[Companion]
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
        gandalf = ALL_COMPANIONS[CharacterID.GANDALF_GREY]
        minions = ALL_MINIONS.values()
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


@dataclass
class PlayCharacterEvent(Request):
    hand: list[Card]

    def __post_init__(self) -> None:
        self.options: list[Card] = [
            card for card in self.hand if card.category == CardCategory.CHARACTER
        ]


@dataclass
class PlayArmyEvent(Request):
    hand: list[Card]

    def __post_init__(self) -> None:
        self.options: list[Card] = [
            card for card in self.hand if card.category == CardCategory.ARMY
        ]


@dataclass
class PlayMusterEvent(Request):
    hand: list[Card]

    def __post_init__(self) -> None:
        self.options: list[Card] = [
            card for card in self.hand if card.category == CardCategory.MUSTER
        ]


@dataclass
class Diplomacy(Request):
    side: Side
    politics: dict[Nation, PoliticalStatus]

    def __post_init__(self) -> None:
        self.options: list[Nation] = [
            nation
            for nation in NATION_SIDE[self.side]
            if self.politics[nation].can_advance()
        ]


@dataclass
class MusterWitchKingArmy(Request):
    regions: RegionMap

    def __post_init__(self) -> None:
        shadow_armies = [
            region.army
            for region in self.regions.with_army_units(Side.SHADOW)
            if region.army is not None
        ]
        self.options: list[Army] = [
            army
            for army in shadow_armies
            if any(unit.nation == Nation.SAURON for unit in army.units)
        ]


@dataclass
class MusterMouthRegion(Request):
    regions: RegionMap

    def __post_init__(self) -> None:
        self.options: list[Region] = [
            region
            for region in self.regions.with_nation(Nation.SAURON)
            if region.settlement == Settlement.STRONGHOLD and not region.is_conquered
        ]


@dataclass
class MusterGandalfWhiteRegion(Request):
    regions: RegionMap

    def __post_init__(self) -> None:
        self.options: list[Region] = [
            region
            for region in self.regions.with_nation(Nation.ELVES)
            if region.settlement == Settlement.STRONGHOLD and not region.is_conquered
        ]
        self.options.append(self.regions.with_name("Fangorn"))


@dataclass
class CasualtyStrategy(Request):
    guide: Companion

    def __post_init__(self) -> None:
        self.options: list[Casualty] = [Casualty.NONE]
        if self.guide.name != CharacterID.GOLLUM:
            self.options.append(Casualty.GUIDE)
            self.options.append(Casualty.RANDOM)


@dataclass
class MusterLocation(Request):
    side: Side
    unit_type: UnitType
    politics: dict[Nation, PoliticalStatus]
    regions: RegionMap
    exclude: Optional[Region] = None

    def __post_init__(self) -> None:
        nations_at_war = [
            nation
            for nation, disposition in self.politics.items()
            if nation in NATION_SIDE[self.side] and disposition.is_at_war()
        ]
        settlements = set()
        for nation in nations_at_war:
            settlements |= {
                region
                for region in self.regions.with_nation(nation)
                if region.is_free(self.side)
                and region.settlement is not None
                and (region.army is None or region.army.size() < 10)
            }
        if self.exclude is not None:
            settlements.remove(self.exclude)
        self.options: list[Region] = list(settlements)


@dataclass
class MoveArmy(Request):
    side: Side
    regions: RegionMap
    leader_required: bool

    def __post_init__(self) -> None:
        self.options: list[Army] = [
            region.army
            for region in self.regions.with_army_units(self.side)
            if region.army is not None
            and len(region.army.valid_moves()) > 0
            and (region.army.leaders() > 0 or not self.leader_required)
        ]


@dataclass
class MoveArmyDestination(Request):
    army: Army

    def __post_init__(self) -> None:
        self.options: list[Region] = self.army.valid_moves()


@dataclass
class MoveArmyUnits(Request):
    army: Army
    leader_required: bool

    def __post_init__(self) -> None:
        # TODO This doesn't let you move characters with the army
        self.options: list[list[ArmyUnit]] = [
            list(combination)
            for i in range(1, len(self.army.units))
            for combination in combinations(self.army.units, i)
            if not self.leader_required
            or any(unit.type == UnitType.LEADER for unit in combination)
        ]
