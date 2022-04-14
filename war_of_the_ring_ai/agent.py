from __future__ import annotations

import random
from typing import TypeVar

from war_of_the_ring_ai.game_data import GameData, PrivatePlayerData
from war_of_the_ring_ai.game_states import State

T = TypeVar("T")


def random_agent(
    state: State[T], _gd: GameData, _pd: PrivatePlayerData, options: list[T]
) -> T:
    print(type(state).__name__)
    return random.choice(options)


def human_agent(
    state: State[T], _gd: GameData, player: PrivatePlayerData, options: list[T]
) -> T:
    print(type(state).__name__)

    for i, option in enumerate(options):
        print(f"{i}: {option}")

    print("> ", end="")
    choice = input()
    while True:
        match choice:
            case "hand":
                print(player.hand)
            case choice if choice.isdigit() and 0 <= int(choice) < len(options):
                return options[int(choice)]
            case _:
                print("Invalid")

        print("> ", end="")
        choice = input()
