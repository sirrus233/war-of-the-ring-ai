import random
from typing import Optional

from war_of_the_ring_ai.game_objects import DIE, Side
from war_of_the_ring_ai.game_requests import (
    ChangeGuide,
    DeclareFellowship,
    DeclareFellowshipLocation,
    Discard,
    EnterMordor,
    HuntAllocation,
)
from war_of_the_ring_ai.game_state import GameState


class GameManager:
    def __init__(self, state: GameState) -> None:
        self.state: GameState = state

    def play(self) -> Side:
        while True:
            self.recover_and_draw_phase()
            self.fellowship_phase()
            self.hunt_allocation_phase()
            self.action_roll_phase()
            if winner := self.action_resolution_phase():
                return winner  # Ring victory
            if winner := self.victory_check_phase():
                return winner  # Military victory

    def recover_and_draw_phase(self) -> None:
        for player in self.state.players.values():
            if player.character_deck:
                player.hand.append(player.character_deck.pop())
            if player.strategy_deck:
                player.hand.append(player.strategy_deck.pop())
            while len(player.hand) > 6:
                player.hand.remove(player.agent.response(Discard(player.hand)))
            player.dice_count = player.dice_max

    def fellowship_phase(self) -> None:
        fellowship = self.state.fellowship
        agent = self.state.players[Side.FREE].agent

        # Change guide
        fellowship.guide = agent.response(ChangeGuide(fellowship.companions))

        # Declare fellowship
        if fellowship.location and not fellowship.revealed:
            if agent.response(DeclareFellowship()):
                declared_region = agent.response(
                    DeclareFellowshipLocation(fellowship.location, fellowship.progress)
                )
                if declared_region.can_heal_fellowship():
                    fellowship.corruption = max(0, fellowship.corruption - 1)
                fellowship.location = declared_region
                fellowship.progress = 0

        # Enter Mordor
        if fellowship.location and fellowship.location.can_enter_mordor():
            if agent.response(EnterMordor()):
                fellowship.location = None
                fellowship.progress = 0

    def hunt_allocation_phase(self) -> None:
        allocated_eyes = self.state.players[Side.SHADOW].agent.response(
            HuntAllocation(
                min_allocation=0 if self.state.hunt_box_character == 0 else 1,
                unused_dice=self.state.players[Side.SHADOW].dice_count,
                companions=len(self.state.fellowship.companions),
            )
        )
        self.state.hunt_box_character = 0
        self.state.hunt_box_eyes = allocated_eyes
        self.state.players[Side.SHADOW].dice_count -= allocated_eyes

    def action_roll_phase(self) -> None:
        for player in self.state.players.values():
            player.dice = [
                random.choice(DIE[player.side]) for _ in range(player.dice_count)
            ]

    def action_resolution_phase(self) -> Optional[Side]:
        pass

    def victory_check_phase(self) -> Optional[Side]:
        if self.state.players[Side.SHADOW].victory_points >= 10:
            return Side.SHADOW

        if self.state.players[Side.FREE].victory_points >= 4:
            return Side.FREE

        return None


if __name__ != "__main__()":
    game = GameManager(GameState())
    game.play()
