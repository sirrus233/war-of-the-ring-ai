import csv
from dataclasses import dataclass

from war_of_the_ring_ai.utils.data_entry import DELIMITER, OUTFILE, REGIONS

REGION_COUNT_BY_NATION = {
    "Elves": 4,
    "Dwarves": 4,
    "North": 8,
    "Rohan": 6,
    "Gondor": 8,
    "Sauron": 11,
    "Isengard": 4,
    "Southron": 7,
}

SETTLEMENT_COUNT_BY_NATION = {
    "Elves": (0, 0, 4),
    "Dwarves": (2, 0, 1),
    "North": (2, 2, 0),
    "Rohan": (2, 1, 1),
    "Gondor": (2, 1, 2),
    "Sauron": (1, 1, 6),
    "Isengard": (2, 0, 1),
    "Southron": (3, 1, 1),
}


@dataclass
class MapData:
    def __init__(self, data_row: list[str]):
        self.name: str = data_row[0]
        self.neighbors: list[str] = data_row[1].split(",")
        self.nation: str = data_row[2]
        self.settlement: str = data_row[3]
        self.regulars: int = int(data_row[4])
        self.elites: int = int(data_row[5])
        self.leaders: int = int(data_row[6])

    def __hash__(self) -> int:
        return hash(self.name)


with open(OUTFILE, "r", encoding="utf8", newline="") as csvfile:
    reader = csv.reader(csvfile, delimiter=DELIMITER)
    MAP_DATA = {MapData(line) for line in reader}


def test_all_regions_exist() -> None:
    expected_regions = REGIONS
    actual_regions = {data.name for data in MAP_DATA}
    assert expected_regions == actual_regions


def test_graph_is_undirected() -> None:
    lookup = {data.name: data for data in MAP_DATA}
    for data in MAP_DATA:
        for neighbor in data.neighbors:
            # Neighboring region exists
            assert neighbor in lookup
            # Neighboring region also has this region as a neighbor
            assert data.name in lookup[neighbor].neighbors


def test_nations_have_expected_regions() -> None:
    for nation, expected_regions in REGION_COUNT_BY_NATION.items():
        actual_regions = sum(1 for data in MAP_DATA if data.nation == nation)
        assert expected_regions == actual_regions


def test_nations_have_expected_settlements() -> None:
    for nation, expected_settlements in SETTLEMENT_COUNT_BY_NATION.items():
        expected_towns, expected_cities, expected_strongholds = expected_settlements
        actual_towns = sum(
            1
            for data in MAP_DATA
            if data.nation == nation and data.settlement == "Town"
        )
        actual_cities = sum(
            1
            for data in MAP_DATA
            if data.nation == nation and data.settlement == "City"
        )
        actual_strongholds = sum(
            1
            for data in MAP_DATA
            if data.nation == nation and data.settlement == "Stronghold"
        )
        assert expected_towns == actual_towns
        assert expected_cities == actual_cities
        assert expected_strongholds == actual_strongholds


def test_fortifications_exist() -> None:
    expected_fortifications = {"Osgiliath", "Fords of Isen"}
    actual_fortifications = {
        data.name for data in MAP_DATA if data.settlement == "Fortification"
    }
    assert expected_fortifications == actual_fortifications
