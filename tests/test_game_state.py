import pytest

from war_of_the_ring_ai.game_objects import Nation, UnitType
from war_of_the_ring_ai.game_state import GameState


def test_deck_sizes() -> None:
    state = GameState()
    for player in state.players:
        assert len(player.character_deck) == 24
        assert len(player.strategy_deck) == 24


def test_all_cards_exist_in_decks() -> None:
    state = GameState()
    all_cards: set[str] = set()
    all_decks = [
        state.free_player.character_deck,
        state.free_player.strategy_deck,
        state.shadow_player.character_deck,
        state.shadow_player.strategy_deck,
    ]
    for deck in all_decks:
        for card in deck:
            all_cards.add(card.event_name)
    assert len(all_cards) == 96


@pytest.mark.parametrize(
    "region, expected_nation, expected_regulars, expected_elites, expected_leaders",
    [("Lorien", Nation.ELVES, 1, 2, 1), ("Osgiliath", Nation.GONDOR, 2, 0, 0)],
)
def test_initial_army(
    region: str,
    expected_nation: Nation,
    expected_regulars: int,
    expected_elites: int,
    expected_leaders: int,
) -> None:
    state = GameState()
    army = state.regions.with_name(region).army
    assert army is not None
    regulars = sum(1 for unit in army.units if unit.type == UnitType.REGULAR)
    elites = sum(1 for unit in army.units if unit.type == UnitType.ELITE)
    leaders = sum(1 for unit in army.units if unit.type == UnitType.LEADER)
    assert all(unit.nation == expected_nation for unit in army.units)
    assert regulars == expected_regulars
    assert elites == expected_elites
    assert leaders == expected_leaders


def test_region_search() -> None:
    state = GameState()
    region = state.regions.with_name("Grey Havens")
    distance = 2
    expected_region_names = {
        "Grey Havens",
        "Forlindon",
        "Harlindon",
        "Tower Hills",
        "Ered Luin",
        "North Ered Luin",
        "South Ered Luin",
        "Evendim",
        "The Shire",
    }
    actual_region_names = {region.name for region in region.reachable_regions(distance)}
    assert expected_region_names == actual_region_names
