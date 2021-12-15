import pytest

from war_of_the_ring_ai.game_objects import Nation, UnitType
from war_of_the_ring_ai.game_state import GameState


def test_deck_sizes():
    state = GameState()
    assert len(state.free_character_deck) == 24
    assert len(state.free_strategy_deck) == 24
    assert len(state.shadow_character_deck) == 24
    assert len(state.shadow_strategy_deck) == 24


def test_all_cards_exist_in_decks():
    state = GameState()
    all_cards = set()
    all_decks = [
        state.free_character_deck,
        state.free_strategy_deck,
        state.shadow_character_deck,
        state.shadow_strategy_deck,
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
    region, expected_nation, expected_regulars, expected_elites, expected_leaders
):
    state = GameState()
    army = state.army_map[region]
    regulars = sum(1 for unit in army if unit.type == UnitType.REGULAR)
    elites = sum(1 for unit in army if unit.type == UnitType.ELITE)
    leaders = sum(1 for unit in army if unit.type == UnitType.LEADER)
    assert all(unit.nation == expected_nation for unit in army)
    assert regulars == expected_regulars
    assert elites == expected_elites
    assert leaders == expected_leaders
