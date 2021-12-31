import random
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from war_of_the_ring_ai.game_requests import Request

Strategy = Callable[["Request"], Any]


def random_strategy(request: "Request") -> Any:
    return random.choice(request.options)


def human_strategy(request: "Request") -> Any:
    print(f"{type(request).__name__}")
    for i, choice in enumerate(request.options):
        print(f"{i}: {choice}")
    selection = int(input())
    return request.options[selection]


class Agent:  # pylint: disable=too-few-public-methods
    def __init__(self, name: str, strategy: Strategy) -> None:
        self.name: str = name
        self.strategy: Strategy = strategy

    def response(self, request: "Request") -> Any:
        request_name = type(request).__name__
        if len(request.options) == 0:
            raise ValueError(
                f"Request {request_name} yielded no valid response options."
            )
        response = self.strategy(request)
        print(f"<{self.name}> {request_name}: {response}")
        return response
