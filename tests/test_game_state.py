from typing import Iterable

import pytest

from war_of_the_ring_ai.constants import Side, UnitRank
from war_of_the_ring_ai.game_objects import Nation
from war_of_the_ring_ai.game_state import (
    GameState,
    PrivatePlayerState,
    init_private_player_state,
)


@pytest.fixture(name="state")
def fixture_state() -> Iterable[GameState]:
    yield GameState()


@pytest.fixture(name="private_free_state")
def fixture_private_free_state() -> Iterable[PrivatePlayerState]:
    yield init_private_player_state(Side.FREE)


@pytest.fixture(name="private_shadow_state")
def fixture_private_shadow_state() -> Iterable[PrivatePlayerState]:
    yield init_private_player_state(Side.SHADOW)


def test_deck_sizes(state: GameState) -> None:
    for player in (state.free_player, state.shadow_player):
        assert player.character_deck_size == 24
        assert player.strategy_deck_size == 24


def test_all_cards_exist_in_decks(
    private_free_state: PrivatePlayerState, private_shadow_state: PrivatePlayerState
) -> None:
    all_cards: set[str] = set()
    all_decks = [
        private_free_state.character_deck,
        private_free_state.strategy_deck,
        private_shadow_state.character_deck,
        private_shadow_state.strategy_deck,
    ]
    for deck in all_decks:
        for card in deck:
            all_cards.add(card.event_name)
    assert len(all_cards) == 96


@pytest.mark.parametrize(
    "region_str, expected_regulars, expected_elites, expected_leaders",
    [("Westemnet", 0, 0, 0), ("Lorien", 1, 2, 1), ("Osgiliath", 2, 0, 0)],
)
def test_initial_army_count(
    state: GameState,
    region_str: str,
    expected_regulars: int,
    expected_elites: int,
    expected_leaders: int,
) -> None:
    region = state.regions.get_region(region_str)
    army = [unit for unit in state.armies if unit.location == region]
    regulars = sum(1 for unit in army if unit.rank == UnitRank.REGULAR)
    elites = sum(1 for unit in army if unit.rank == UnitRank.ELITE)
    leaders = sum(1 for unit in army if unit.rank == UnitRank.LEADER)
    assert regulars == expected_regulars
    assert elites == expected_elites
    assert leaders == expected_leaders


@pytest.mark.parametrize(
    "region_str, expected_nation",
    [
        ("Westemnet", Nation.ROHAN),
        ("Lorien", Nation.ELVES),
        ("Osgiliath", Nation.GONDOR),
    ],
)
def test_initial_army_nation(
    state: GameState,
    region_str: str,
    expected_nation: Nation,
) -> None:
    region = state.regions.get_region(region_str)
    army = [unit for unit in state.armies if unit.location == region]
    assert all(unit.nation == expected_nation for unit in army)


def test_region_search(state: GameState) -> None:
    distance = 2
    start_region = state.regions.get_region("Grey Havens")
    expected_regions = {
        state.regions.get_region(region)
        for region in (
            "Grey Havens",
            "Forlindon",
            "Harlindon",
            "Tower Hills",
            "Ered Luin",
            "North Ered Luin",
            "South Ered Luin",
            "Evendim",
            "The Shire",
        )
    }
    actual_regions = state.regions.reachable_regions(start_region, distance)
    assert expected_regions == actual_regions
