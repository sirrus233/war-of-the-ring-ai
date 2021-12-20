import random
from collections import Counter
from typing import Optional, cast

from war_of_the_ring_ai.game_objects import (
    DIE,
    NATION_SIDE,
    Action,
    Army,
    CharacterID,
    DieResult,
    Settlement,
    Side,
)
from war_of_the_ring_ai.game_requests import (
    ArmyAction,
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
from war_of_the_ring_ai.game_state import ALL_COMPANIONS, ALL_MINIONS, GameState


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
        fellowship.guide = player.agent.response(
            ChangeGuide(list(fellowship.companions.values()))
        )

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
        return TurnManager(self.state).start_turn()

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

    def do_action(self, action: Action) -> None:
        # TODO Refactor this, probably into its own class, or several classes
        player = self.active_player

        if action == Action.SKIP:
            pass

        if action == Action.DRAW_CHARACTER_EVENT:
            player.hand.append(player.character_deck.pop())
            while len(player.hand) > 6:
                player.hand.remove(player.agent.response(Discard(player.hand)))

        if action == Action.DRAW_STRATEGY_EVENT:
            player.hand.append(player.strategy_deck.pop())
            while len(player.hand) > 6:
                player.hand.remove(player.agent.response(Discard(player.hand)))

        if action == Action.PLAY_CHARACTER_EVENT:
            card = player.agent.response(PlayCharacterEvent(player.hand))
            player.hand.remove(card)
            if self.state.fellowship.guide.name == CharacterID.GANDALF_GREY:
                if player.character_deck:
                    player.hand.append(player.character_deck.pop())
                    while len(player.hand) > 6:
                        player.hand.remove(player.agent.response(Discard(player.hand)))

        if action == Action.PLAY_ARMY_EVENT:
            card = player.agent.response(PlayArmyEvent(player.hand))
            player.hand.remove(card)
            if self.state.fellowship.guide.name == CharacterID.GANDALF_GREY:
                if player.strategy_deck:
                    player.hand.append(player.strategy_deck.pop())
                    while len(player.hand) > 6:
                        player.hand.remove(player.agent.response(Discard(player.hand)))

        if action == Action.PLAY_MUSTER_EVENT:
            card = player.agent.response(PlayMusterEvent(player.hand))
            player.hand.remove(card)
            if self.state.fellowship.guide.name == CharacterID.GANDALF_GREY:
                if player.strategy_deck:
                    player.hand.append(player.strategy_deck.pop())
                    while len(player.hand) > 6:
                        player.hand.remove(player.agent.response(Discard(player.hand)))

        if action == Action.DIPLOMACY:
            nation = player.agent.response(Diplomacy(player.side, self.state.politics))
            self.state.politics[nation].disposition -= 1

        if action == Action.MUSTER_ELITE:
            pass

        if action == Action.MUSTER_REGULAR_REGULAR:
            pass

        if action == Action.MUSTER_REGULAR_LEADER:
            pass

        if action == Action.MUSTER_LEADER_LEADER:
            pass

        if action == Action.MUSTER_SARUMAN:
            saruman = ALL_MINIONS[CharacterID.SARUMAN]
            self.state.characters_mustered.add(saruman.name)
            orthanc = self.state.regions.with_name("Orthanc")
            if orthanc.army is not None:
                orthanc.army.characters.append(saruman)
            else:
                orthanc.army = Army(Side.SHADOW, orthanc, characters=[saruman])

        if action == Action.MUSTER_WITCH_KING:
            witch_king = ALL_MINIONS[CharacterID.WITCH_KING]
            self.state.characters_mustered.add(witch_king.name)
            army = player.agent.response(MusterWitchKingArmy(self.state.regions))
            army.characters.append(witch_king)

        if action == Action.MUSTER_MOUTH_OF_SAURON:
            mouth = ALL_MINIONS[CharacterID.MOUTH_OF_SAURON]
            self.state.characters_mustered.add(mouth.name)
            region = player.agent.response(MusterWitchKingArmy(self.state.regions))
            if region.army is not None:
                region.army.characters.append(mouth)
            else:
                region.army = Army(Side.SHADOW, region, characters=[mouth])

        if action == Action.MOVE_ARMIES:
            pass

        if action == Action.ATTACK:
            pass

        if action == Action.LEADER_MOVE:
            pass

        if action == Action.LEADER_ATTACK:
            pass

        if action == Action.MOVE_FELLOWSHIP:
            self.state.fellowship.progress += 1

            if self.state.fellowship.in_mordor():
                tile = self.state.hunt_pool.draw()

                if tile.is_eye():
                    corruption = (
                        self.state.hunt_box_eyes + self.state.hunt_box_character
                    )
                elif tile.is_shelob():
                    corruption = random.randint(1, 6)
                else:
                    corruption = tile.corruption
                self.state.fellowship.corruption += corruption

                if tile.side == Side.SHADOW:
                    self.state.fellowship.progress -= 1

                if tile.reveal:
                    self.state.fellowship.revealed = True

            else:
                assert (location := self.state.fellowship.location) is not None
                hunt_roll = [
                    random.randint(1, 6) for _ in range(self.state.hunt_box_eyes)
                ]
                hits = sum(
                    1 for i in hunt_roll if i >= 6 - self.state.hunt_box_character
                )
                misses = len(hunt_roll) - hits
                reroll_count = 0
                if location.army is not None:
                    if location.army.leaders() > 0:
                        reroll_count += 1
                    if location.army.regulars() + location.army.elites() > 0:
                        reroll_count += 1
                if (
                    location.nation in NATION_SIDE[Side.SHADOW]
                    and location.settlement == Settlement.STRONGHOLD
                    and not location.is_conquered
                ):
                    reroll_count += 1
                reroll = [
                    random.randint(1, 6) for _ in range(min(misses, reroll_count))
                ]
                hits += sum(1 for i in reroll if i >= 6 - self.state.hunt_box_character)

                tile = self.state.hunt_pool.draw()

                if tile.is_eye():
                    corruption = hits
                    self.state.hunt_pool.reserve.append(tile)
                else:
                    corruption = tile.corruption
                self.state.fellowship.corruption += corruption

                if tile.reveal:
                    self.state.fellowship.revealed = True

        if action == Action.HIDE_FELLOWSHIP:
            self.state.fellowship.revealed = False

        if action == Action.SEPARATE_COMPANIONS:
            pass

        if action == Action.MOVE_COMPANIONS:
            pass

        if action == Action.MOVE_MINIONS:
            pass

        if action == Action.MUSTER_GANDALF:
            gandalf = ALL_COMPANIONS[CharacterID.GANDALF_WHITE]
            self.state.characters_mustered.add(gandalf.name)
            region = player.agent.response(MusterGandalfWhiteRegion(self.state.regions))
            if region.army is not None:
                region.army.characters.append(gandalf)
            else:
                region.army = Army(Side.FREE, region, characters=[gandalf])

        if action == Action.MUSTER_ARAGORN:
            aragorn = ALL_COMPANIONS[CharacterID.ARAGORN]
            self.state.characters_mustered.add(aragorn.name)
            region = self.state.regions.with_character(CharacterID.STRIDER)
            region.army.characters.remove(ALL_COMPANIONS[CharacterID.STRIDER])
            region.army.characters.append(aragorn)

    def start_turn(self) -> Optional[Side]:
        while not self.is_turn_over():
            # TODO Elven ring option (CAN pass or use different die after using ring)

            if self.choose_pass_if_able():
                self.end_action()
            else:
                action_die = self.choose_action_die()
                action = self.choose_action(action_die)
                self.do_action(action)
                self.end_action()

            if (winner := self.is_ring_victory()) is not None:
                return winner

        return None


if __name__ != "__main__()":
    game = GameManager(GameState())
    game.play()
