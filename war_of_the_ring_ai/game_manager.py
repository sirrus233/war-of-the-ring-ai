import random

from war_of_the_ring_ai.game_objects import DIE, Side
from war_of_the_ring_ai.game_state import GameState


class GameManager:
    def __init__(self, state: GameState) -> None:
        self.state: GameState = state

    def turn_flow(self) -> None:
        self.recover_and_draw_phase()
        self.fellowship_phase()
        self.hunt_allocation_phase()
        self.action_roll_phase()
        self.action_resolution_phase()
        self.victory_check_phase()

    def recover_and_draw_phase(self) -> None:
        for player in self.state.players.values():
            player.hand.append(player.character_deck.pop())
            player.hand.append(player.strategy_deck.pop())
            player.dice_count = player.dice_max

    def fellowship_phase(self) -> None:
        pass

    def hunt_allocation_phase(self) -> None:
        if self.state.hunt_box_character == 0:
            self.state.hunt_box_eyes = 0
        else:
            self.state.players[Side.SHADOW].dice_count -= 1
            self.state.hunt_box_eyes = 1

        self.state.hunt_box_character = 0

        # TODO Allow eye allocation <= # of Fellowship Companions

    def action_roll_phase(self) -> None:
        for player in self.state.players.values():
            for _ in range(player.dice_count):
                player.dice.append(random.choice(DIE[player.side]))

    def action_resolution_phase(self) -> None:
        pass

    def victory_check_phase(self) -> None:
        if self.state.players[Side.SHADOW].victory_points >= 10:
            print("Shadow wins.")
        elif self.state.players[Side.FREE].victory_points >= 4:
            print("Free wins.")
