import random
from collections import Counter
from typing import Optional, cast

from war_of_the_ring_ai.game_objects import (
    DIE,
    NATION_SIDE,
    Action,
    Army,
    Casualty,
    CharacterID,
    Companion,
    DieResult,
    Settlement,
    Side,
)
from war_of_the_ring_ai.game_requests import (
    ArmyAction,
    CasualtyStrategy,
    ChangeGuide,
    CharacterAction,
    ChooseDie,
    DeclareFellowship,
    DeclareFellowshipLocation,
    Diplomacy,
    Discard,
    EnterMordor,
    HuntAllocation,
    HybridAction,
    MusterAction,
    MusterGandalfWhiteRegion,
    MusterWitchKingArmy,
    PalantirAction,
    PassTurn,
    PlayArmyEvent,
    PlayCharacterEvent,
    PlayMusterEvent,
    WillAction,
)
from war_of_the_ring_ai.game_state import (
    ALL_COMPANIONS,
    ALL_MINIONS,
    GameState,
    PlayerState,
)


class GameManager:
    def __init__(self, state: GameState) -> None:
        self.state: GameState = state

    def play(self) -> Side:
        while True:
            self.draw_phase()
            self.fellowship_phase()
            self.hunt_allocation_phase()
            self.action_roll_phase()
            if winner := self.action_resolution_phase():
                return winner  # Ring victory
            if winner := self.victory_check_phase():
                return winner  # Military victory

    def draw_phase(self) -> None:
        for player in self.state.players:
            if player.character_deck:
                player.hand.append(player.character_deck.pop())
            if player.strategy_deck:
                player.hand.append(player.strategy_deck.pop())
            while len(player.hand) > 6:
                player.hand.remove(player.agent.response(Discard(player.hand)))

    def fellowship_phase(self) -> None:
        player = self.state.free_player
        fellowship = self.state.fellowship

        # Change guide
        fellowship.guide = player.agent.response(ChangeGuide(fellowship.companions))

        # Declare fellowship
        if not fellowship.in_mordor() and not fellowship.revealed:
            assert fellowship.location
            if player.agent.response(DeclareFellowship()):
                declared_region = player.agent.response(
                    DeclareFellowshipLocation(fellowship.location, fellowship.progress)
                )
                if declared_region.can_heal_fellowship():
                    fellowship.corruption = max(0, fellowship.corruption - 1)
                fellowship.location = declared_region
                fellowship.progress = 0

        # Enter Mordor
        if not fellowship.in_mordor():
            assert fellowship.location
            if fellowship.location.can_enter_mordor():
                if player.agent.response(EnterMordor()):
                    fellowship.location = None
                    fellowship.progress = 0
                    self.state.hunt_pool.enter_mordor()

    def hunt_allocation_phase(self) -> None:
        player = self.state.shadow_player
        allocated_eyes = player.agent.response(
            HuntAllocation(
                min_allocation=0 if self.state.hunt_box_character == 0 else 1,
                max_dice=player.max_dice,
                companions=len(self.state.fellowship.companions),
            )
        )
        self.state.hunt_box_character = 0
        self.state.hunt_box_eyes = allocated_eyes

    def action_roll_phase(self) -> None:
        # Roll dice for both players
        for player in self.state.players:
            rollable = {
                Side.FREE: player.max_dice,
                Side.SHADOW: player.max_dice - self.state.hunt_box_eyes,
            }
            player.dice = Counter(
                random.choice(DIE[player.side]) for _ in range(rollable[player.side])
            )

        # Add rolled eyes to the hunt box
        self.state.hunt_box_eyes += self.state.shadow_player.dice[DieResult.EYE]
        self.state.shadow_player.dice[DieResult.EYE] = 0

    def action_resolution_phase(self) -> Optional[Side]:
        return TurnManager(self.state).play_turn()

    def victory_check_phase(self) -> Optional[Side]:
        if self.state.shadow_player.victory_points >= 10:
            return Side.SHADOW

        if self.state.free_player.victory_points >= 4:
            return Side.FREE

        return None


class TurnManager:
    def __init__(self, state: GameState) -> None:
        self.state = state
        self.active_player = state.free_player
        self.inactive_player = state.shadow_player

    def is_turn_over(self) -> bool:
        return (
            self.active_player.dice_count() == 0
            and self.inactive_player.dice_count() == 0
        )

    def end_action(self) -> None:
        if self.inactive_player.dice_count() > 0:
            self.active_player, self.inactive_player = (
                self.inactive_player,
                self.active_player,
            )

    def choose_pass_if_able(self) -> bool:
        if self.active_player.dice_count() < self.inactive_player.dice_count():
            return cast(bool, self.active_player.agent.response(PassTurn()))
        return False

    def choose_action_die(self) -> DieResult:
        action_die = cast(
            DieResult,
            self.active_player.agent.response(
                ChooseDie(
                    [die for die, count in self.active_player.dice.items() if count > 0]
                )
            ),
        )
        self.active_player.dice[action_die] -= 1
        return action_die

    def choose_action(self, action_die: DieResult) -> Action:
        # TODO This can be a match statement when mypy supports python 3.10
        if action_die == DieResult.CHARACTER:
            return cast(
                Action,
                self.active_player.agent.response(
                    CharacterAction(
                        self.active_player.side,
                        self.state.fellowship,
                        self.state.regions,
                    )
                ),
            )
        if action_die == DieResult.ARMY:
            return cast(
                Action,
                self.active_player.agent.response(
                    ArmyAction(self.active_player.side, self.state.regions)
                ),
            )
        if action_die == DieResult.MUSTER:
            return cast(
                Action,
                self.active_player.agent.response(
                    MusterAction(
                        self.active_player.side,
                        self.state.regions,
                        self.state.politics,
                        self.state.reinforcements,
                        self.state.characters_mustered,
                        self.state.fellowship,
                    )
                ),
            )
        if action_die == DieResult.PALANTIR:
            return cast(
                Action,
                self.active_player.agent.response(PalantirAction(self.active_player)),
            )
        if action_die == DieResult.HYBRID:
            return cast(
                Action,
                self.active_player.agent.response(
                    HybridAction(
                        ArmyAction(self.active_player.side, self.state.regions),
                        MusterAction(
                            self.active_player.side,
                            self.state.regions,
                            self.state.politics,
                            self.state.reinforcements,
                            self.state.characters_mustered,
                            self.state.fellowship,
                        ),
                    )
                ),
            )
        if action_die == DieResult.WILL:
            return cast(
                Action,
                self.active_player.agent.response(
                    WillAction(
                        self.state.characters_mustered,
                        self.state.fellowship.companions,
                        self.state.regions,
                        CharacterAction(
                            self.active_player.side,
                            self.state.fellowship,
                            self.state.regions,
                        ),
                        HybridAction(
                            ArmyAction(self.active_player.side, self.state.regions),
                            MusterAction(
                                self.active_player.side,
                                self.state.regions,
                                self.state.politics,
                                self.state.reinforcements,
                                self.state.characters_mustered,
                                self.state.fellowship,
                            ),
                        ),
                        PalantirAction(self.active_player),
                    )
                ),
            )
        raise ValueError(f"Unknown action die: {action_die}")

    def is_ring_victory(self) -> Optional[Side]:
        if self.state.fellowship.corruption >= 12:
            return Side.SHADOW
        if self.state.fellowship.in_mordor() and self.state.fellowship.progress == 5:
            return Side.FREE
        return None

    def play_turn(self) -> Optional[Side]:
        while not self.is_turn_over():
            # TODO Elven ring option (CAN pass or use different die after using ring)
            # TODO Auto-corruption from Mordor

            if self.choose_pass_if_able():
                self.end_action()
            else:
                action_die = self.choose_action_die()
                action = self.choose_action(action_die)
                ActionManager(self.state, self.active_player).do_action(action)
                self.end_action()

            if (winner := self.is_ring_victory()) is not None:
                return winner

        return None


class ActionManager:  # pylint: disable=too-many-public-methods
    def __init__(self, state: GameState, active_player: PlayerState) -> None:
        self.state = state
        self.player = active_player

    def do_action(self, action: Action) -> None:
        getattr(self, action.name.lower())()

    def skip(self) -> None:  # pylint: disable=no-self-use
        return

    def draw_character_event(self) -> None:
        self.player.hand.append(self.player.character_deck.pop())
        while len(self.player.hand) > 6:
            discarded_card = self.player.agent.response(Discard(self.player.hand))
            self.player.hand.remove(discarded_card)

    def draw_strategy_event(self) -> None:
        self.player.hand.append(self.player.strategy_deck.pop())
        while len(self.player.hand) > 6:
            discarded_card = self.player.agent.response(Discard(self.player.hand))
            self.player.hand.remove(discarded_card)

    def play_character_event(self) -> None:
        card = self.player.agent.response(PlayCharacterEvent(self.player.hand))
        self.player.hand.remove(card)

        if self.state.fellowship.guide.name == CharacterID.GANDALF_GREY:
            if self.player.character_deck:
                self.player.hand.append(self.player.character_deck.pop())
                while len(self.player.hand) > 6:
                    self.player.hand.remove(
                        self.player.agent.response(Discard(self.player.hand))
                    )

    def play_army_event(self) -> None:
        card = self.player.agent.response(PlayArmyEvent(self.player.hand))
        self.player.hand.remove(card)
        if self.state.fellowship.guide.name == CharacterID.GANDALF_GREY:
            if self.player.strategy_deck:
                self.player.hand.append(self.player.strategy_deck.pop())
                while len(self.player.hand) > 6:
                    self.player.hand.remove(
                        self.player.agent.response(Discard(self.player.hand))
                    )

    def play_muster_event(self) -> None:
        card = self.player.agent.response(PlayMusterEvent(self.player.hand))
        self.player.hand.remove(card)
        if self.state.fellowship.guide.name == CharacterID.GANDALF_GREY:
            if self.player.strategy_deck:
                self.player.hand.append(self.player.strategy_deck.pop())
                while len(self.player.hand) > 6:
                    self.player.hand.remove(
                        self.player.agent.response(Discard(self.player.hand))
                    )

    def diplomacy(self) -> None:
        nation = self.player.agent.response(
            Diplomacy(self.player.side, self.state.politics)
        )
        self.state.politics[nation].disposition -= 1

    def muster_elite(self) -> None:
        raise NotImplementedError()

    def muster_regular_regular(self) -> None:
        raise NotImplementedError()

    def muster_regular_leader(self) -> None:
        raise NotImplementedError()

    def muster_leader_leader(self) -> None:
        raise NotImplementedError()

    def muster_saruman(self) -> None:
        saruman = ALL_MINIONS[CharacterID.SARUMAN]
        self.state.characters_mustered.add(saruman)
        orthanc = self.state.regions.with_name("Orthanc")
        if orthanc.army is not None:
            orthanc.army.characters.append(saruman)
        else:
            orthanc.army = Army(Side.SHADOW, orthanc, characters=[saruman])

    def muster_witch_king(self) -> None:
        witch_king = ALL_MINIONS[CharacterID.WITCH_KING]
        self.state.characters_mustered.add(witch_king)
        army = self.player.agent.response(MusterWitchKingArmy(self.state.regions))
        army.characters.append(witch_king)

    def muster_mouth_of_sauron(self) -> None:
        mouth = ALL_MINIONS[CharacterID.MOUTH_OF_SAURON]
        self.state.characters_mustered.add(mouth)
        region = self.player.agent.response(MusterWitchKingArmy(self.state.regions))
        if region.army is not None:
            region.army.characters.append(mouth)
        else:
            region.army = Army(Side.SHADOW, region, characters=[mouth])

    def move_armies(self) -> None:
        raise NotImplementedError()

    def attack(self) -> None:
        raise NotImplementedError()

    def leader_move(self) -> None:
        raise NotImplementedError()

    def leader_attack(self) -> None:
        raise NotImplementedError()

    def move_fellowship(self) -> None:
        self.state.fellowship.progress += 1
        HuntManager(self.state).hunt()
        # TODO connect with hunt manager
        # TODO Add character die to hunt box

    def hide_fellowship(self) -> None:
        # TODO Strider's Guide ability (should allow this action from any die)
        self.state.fellowship.revealed = False

    def separate_companions(self) -> None:
        raise NotImplementedError()

    def move_companions(self) -> None:
        raise NotImplementedError()

    def move_minions(self) -> None:
        raise NotImplementedError()

    def muster_gandalf(self) -> None:
        gandalf = ALL_COMPANIONS[CharacterID.GANDALF_WHITE]
        self.state.characters_mustered.add(gandalf)
        region = self.player.agent.response(
            MusterGandalfWhiteRegion(self.state.regions)
        )
        if region.army is not None:
            region.army.characters.append(gandalf)
        else:
            region.army = Army(Side.FREE, region, characters=[gandalf])

    def muster_aragorn(self) -> None:
        aragorn = ALL_COMPANIONS[CharacterID.ARAGORN]
        self.state.characters_mustered.add(aragorn)
        region = self.state.regions.with_character(CharacterID.STRIDER)
        if region.army is not None:
            region.army.characters.remove(ALL_COMPANIONS[CharacterID.STRIDER])
            region.army.characters.append(aragorn)


class HuntManager:
    def __init__(self, state: GameState) -> None:
        # TODO Move when revealed
        self.state = state

    def get_reroll_count(self) -> int:
        reroll_count = 0

        location = self.state.fellowship.location
        if location is None:
            raise ValueError("Cannot determine reroll count when Fellowship in Mordor.")

        has_nazgul = False
        has_enemy_units = False
        if location.army is not None:
            has_enemy_army = location.army.side == Side.SHADOW
            has_nazgul = has_enemy_army and location.army.leaders() > 0
            has_enemy_units = (
                has_enemy_army and location.army.regulars() + location.army.elites() > 0
            )
        has_enemy_stronghold = (
            location.nation in NATION_SIDE[Side.SHADOW]
            and location.settlement == Settlement.STRONGHOLD
            and not location.is_conquered
        )

        for reroll_grant in [has_nazgul, has_enemy_units, has_enemy_stronghold]:
            if reroll_grant:
                reroll_count += 1

        return reroll_count

    def hunt_roll(self) -> int:
        hit_result = 6 - self.state.hunt_box_character
        hunt_roll_results = [
            random.randint(1, 6) for _ in range(self.state.hunt_box_eyes)
        ]
        hits = sum(1 for i in hunt_roll_results if i >= hit_result)
        misses = len(hunt_roll_results) - hits
        max_rerolls = self.get_reroll_count()
        reroll_results = [random.randint(1, 6) for _ in range(min(misses, max_rerolls))]
        hits += sum(1 for i in reroll_results if i >= hit_result)
        return hits

    def eye_corruption(self, hits: int = 0) -> int:
        if self.state.fellowship.in_mordor():
            return self.state.hunt_box_eyes + self.state.hunt_box_character
        return hits

    def draw_tile(self, hits: int = 0) -> int:
        tile = self.state.hunt_pool.draw()

        if tile.side == Side.SHADOW:
            self.state.fellowship.progress -= 1

        if tile.reveal:
            self.state.fellowship.revealed = True

        if tile.is_eye():
            corruption = self.eye_corruption(hits)
            self.state.hunt_pool.reserve.append(tile)
        elif tile.is_shelob():
            corruption = random.randint(1, 6)
        else:
            corruption = tile.corruption

        return corruption

    def choose_casualty(self) -> Optional[Companion]:
        guide = self.state.fellowship.guide
        strategy = self.state.free_player.agent.response(CasualtyStrategy(guide))
        if strategy == Casualty.GUIDE:
            return self.state.fellowship.guide
        if strategy == Casualty.RANDOM:
            return random.choice(self.state.fellowship.companions)
        return None

    def hunt(self) -> None:
        if self.state.fellowship.in_mordor():
            corruption = self.draw_tile()
        elif (hits := self.hunt_roll()) > 0:
            corruption = self.draw_tile(hits)
        else:
            corruption = 0

        # TODO Merry/Pippin guide ability

        if corruption > 0:
            casualty = self.choose_casualty()
            if casualty is not None:
                guide = self.state.free_player.agent.response(
                    ChangeGuide(self.state.fellowship.companions, casualty)
                )
                self.state.fellowship.guide = guide
                self.state.fellowship.companions.remove(casualty)

        self.state.fellowship.corruption += corruption


if __name__ != "__main__()":
    game = GameManager(GameState())
    game.play()
