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


def test_lorien_initial_army():
    state = GameState()
    army = state.army_map["Lorien"]
    regulars = sum(1 for unit in army if unit.type == UnitType.REGULAR)
    elites = sum(1 for unit in army if unit.type == UnitType.ELITE)
    leaders = sum(1 for unit in army if unit.type == UnitType.LEADER)
    assert all(unit.nation == Nation.ELVES for unit in army)
    assert regulars == 1
    assert elites == 2
    assert leaders == 1


def test_osgiliath_initial_army():
    state = GameState()
    army = state.army_map["Osgiliath"]
    regulars = sum(1 for unit in army if unit.type == UnitType.REGULAR)
    elites = sum(1 for unit in army if unit.type == UnitType.ELITE)
    leaders = sum(1 for unit in army if unit.type == UnitType.LEADER)
    assert all(unit.nation == Nation.GONDOR for unit in army)
    assert regulars == 2
    assert elites == 0
    assert leaders == 0
