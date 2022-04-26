from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import TypeVar

from war_of_the_ring_ai.game_data import GameData, PrivatePlayerData

T = TypeVar("T")


class Agent(ABC):
    def __init__(self, game: GameData, player: PrivatePlayerData):
        self.game = game
        self.player = player

    def agree(self, state: str) -> bool:
        return self.ask(state, [True, False])

    @abstractmethod
    def ask(self, state: str, options: list[T]) -> T:
        ...


class RandomAgent(Agent):
    def ask(self, state: str, options: list[T]) -> T:
        print(state)
        choice = random.choice(options)
        print(f"Choice: {choice}")
        return choice


class HumanAgent(Agent):
    def ask(self, state: str, options: list[T]) -> T:
        print(state)

        for i, option in enumerate(options):
            print(f"{i}: {option}")

        print("> ", end="")
        choice = input()
        while True:
            match choice:
                case "hand":
                    for card in self.player.hand:
                        print(card)
                case choice if choice.isdigit() and 0 <= int(choice) < len(options):
                    return options[int(choice)]
                case _:
                    print("Invalid")

            print("> ", end="")
            choice = input()
