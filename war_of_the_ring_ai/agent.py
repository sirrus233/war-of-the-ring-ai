import random
from typing import Any, Callable

from war_of_the_ring_ai.game_requests import Request

Strategy = Callable[[list[Any]], Any]


def random_strategy(choices: list[Any]) -> Any:
    return random.choice(choices)


class Agent:  # pylint: disable=too-few-public-methods
    def __init__(self, name: str, strategy: Strategy) -> None:
        self.name: str = name
        self.strategy: Strategy = strategy

    def response(self, request: Request) -> Any:
        response = self.strategy(request.options)
        print(f"<{self.name}> {type(request).__name__}: {response}")
        return response
