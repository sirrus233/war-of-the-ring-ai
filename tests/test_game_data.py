from typing import Iterable

import pytest

from war_of_the_ring_ai.constants import DeckType, Nation, Side, UnitRank
from war_of_the_ring_ai.game_data import (
    GameData,
    PrivatePlayerData,
    init_private_player_data,
    init_public_player_data,
)


@pytest.fixture(name="game")
def fixture_state() -> Iterable[GameData]:
    yield GameData(
        free=init_public_player_data(Side.FREE),
        shadow=init_public_player_data(Side.SHADOW),
    )


@pytest.fixture(name="free")
def fixture_private_free_state() -> Iterable[PrivatePlayerData]:
    yield init_private_player_data(Side.FREE)


@pytest.fixture(name="shadow")
def fixture_private_shadow_state() -> Iterable[PrivatePlayerData]:
    yield init_private_player_data(Side.SHADOW)


def test_deck_sizes(game: GameData) -> None:
    for player in game.players.values():
        for deck in DeckType:
            assert player.decks[deck].size == 24


def test_all_cards_exist_in_decks(
    free: PrivatePlayerData, shadow: PrivatePlayerData
) -> None:
    all_cards: set[str] = set()
    all_decks = [
        free.decks[DeckType.CHARACTER],
        free.decks[DeckType.STRATEGY],
        shadow.decks[DeckType.CHARACTER],
        shadow.decks[DeckType.STRATEGY],
    ]
    for deck in all_decks:
        for card in deck.cards:
            all_cards.add(card.event_name)
    assert len(all_cards) == 96


@pytest.mark.parametrize(
    "region_str, expected_regulars, expected_elites, expected_leaders",
    [("Westemnet", 0, 0, 0), ("Lorien", 1, 2, 1), ("Osgiliath", 2, 0, 0)],
)
def test_initial_army_count(
    game: GameData,
    region_str: str,
    expected_regulars: int,
    expected_elites: int,
    expected_leaders: int,
) -> None:
    region = game.regions.get_region(region_str)
    army = [unit for unit in game.armies if unit.location == region]
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
    game: GameData,
    region_str: str,
    expected_nation: Nation,
) -> None:
    region = game.regions.get_region(region_str)
    army = [unit for unit in game.armies if unit.location == region]
    assert all(unit.nation == expected_nation for unit in army)


def test_region_search(game: GameData) -> None:
    distance = 2
    start_region = game.regions.get_region("Grey Havens")
    expected_regions = {
        game.regions.get_region(region)
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
    actual_regions = game.regions.reachable_regions(start_region, distance)
    assert expected_regions == set(actual_regions)
