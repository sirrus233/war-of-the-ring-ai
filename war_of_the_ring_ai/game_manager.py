import random

from war_of_the_ring_ai.game_objects import DIE, Card, Side
from war_of_the_ring_ai.game_state import GameState


class GameManager:
    def __init__(self) -> None:
        self.state: GameState = GameState()
        self.free_hand: list[Card] = []
        self.shadow_hand: list[Card] = []

    def turn_flow(self) -> None:
        self.recover_and_draw_phase()
        self.fellowship_phase()
        self.hunt_allocation_phase()
        self.action_roll_phase()
        self.action_resolution_phase()
        self.victory_check_phase()

    def recover_and_draw_phase(self) -> None:
        self.free_hand.append(self.state.free_character_deck.pop())
        self.free_hand.append(self.state.free_strategy_deck.pop())

        self.shadow_hand.append(self.state.shadow_character_deck.pop())
        self.shadow_hand.append(self.state.shadow_strategy_deck.pop())

        self.state.free_dice_count = self.state.free_dice_max
        self.state.shadow_dice_count = self.state.shadow_dice_max

    def fellowship_phase(self) -> None:
        pass

    def hunt_allocation_phase(self) -> None:
        if self.state.hunt_box_character == 0:
            self.state.hunt_box_eyes = 0
        else:
            self.state.shadow_dice_count -= 1
            self.state.hunt_box_eyes = 1

        self.state.hunt_box_character = 0

        # TODO Allow eye allocation <= # of Fellowship Companions

    def action_roll_phase(self) -> None:
        for _ in range(self.state.free_dice_count):
            self.state.free_dice.append(random.choice(DIE[Side.FREE]))

        for _ in range(self.state.shadow_dice_count):
            self.state.shadow_dice.append(random.choice(DIE[Side.SHADOW]))

    def action_resolution_phase(self) -> None:
        pass

    def victory_check_phase(self) -> None:
        if self.state.shadow_victory_points >= 10:
            print("Shadow wins.")
        elif self.state.free_victory_points >= 4:
            print("Free wins.")
