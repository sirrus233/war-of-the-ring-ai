import random
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from war_of_the_ring_ai.game_requests import Request

Strategy = Callable[[list[Any]], Any]


def random_strategy(choices: list[Any]) -> Any:
    return random.choice(choices)


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
        response = self.strategy(request.options)
        print(f"<{self.name}> {request_name}: {response}")
        return response
