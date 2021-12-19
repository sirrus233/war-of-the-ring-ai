import random
from collections import Counter
from typing import Optional

from war_of_the_ring_ai.game_objects import DIE, DieResult, Side
from war_of_the_ring_ai.game_requests import (
    ChangeGuide,
    DeclareFellowship,
    DeclareFellowshipLocation,
    Discard,
    EnterMordor,
    HuntAllocation,
    PassTurn,
)
from war_of_the_ring_ai.game_state import GameState


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
        active_player = self.state.free_player
        inactive_player = self.state.shadow_player

        while True:
            # End the phase when both players have used all dice
            active_dice_count = sum(active_player.dice.values())
            inactive_dice_count = sum(inactive_player.dice.values())
            if active_dice_count == 0 and inactive_dice_count == 0:
                break

            # Active player may pass, if able
            if active_dice_count < inactive_dice_count:
                if active_player.agent.response(PassTurn()):
                    active_player, inactive_player = inactive_player, active_player
                    continue

            # Select action die
            # Take action

            # Check for ring victory
            fellowship = self.state.fellowship
            if fellowship.corruption >= 12:
                return Side.SHADOW
            if fellowship.in_mordor() and fellowship.progress == 5:
                return Side.FREE

        return None

    def victory_check_phase(self) -> Optional[Side]:
        if self.state.shadow_player.victory_points >= 10:
            return Side.SHADOW

        if self.state.free_player.victory_points >= 4:
            return Side.FREE

        return None


if __name__ != "__main__()":
    game = GameManager(GameState())
    game.play()
