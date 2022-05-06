from dataclasses import dataclass
from typing import Mapping

from war_of_the_ring_ai.agent import Agent
from war_of_the_ring_ai.constants import Side
from war_of_the_ring_ai.game_data import GameData, PlayerData


@dataclass
class GameContext:
    game: GameData
    players: Mapping[Side, PlayerData]
    agents: Mapping[Side, Agent]

    @property
    def active_player(self) -> PlayerData:
        return self.players[self.game.active_side]

    @property
    def active_agent(self) -> Agent:
        return self.agents[self.game.active_side]

    @property
    def inactive_player(self) -> PlayerData:
        return self.players[self.game.inactive_side]
