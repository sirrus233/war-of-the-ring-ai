import builtins
from dataclasses import dataclass
from tempfile import NamedTemporaryFile
from typing import Iterable, Optional
from unittest.mock import MagicMock, patch

import pytest

from war_of_the_ring_ai.utils.data_entry import write_output_flow


@dataclass
class InputEntry:
    name: str
    neighbors: list[str]
    nation: Optional[int] = None
    settlement: Optional[int] = None
    army: Optional[tuple[int, int, int]] = None


def format_test_input(input_entries: list[InputEntry]) -> list[str]:
    test_input: list[str] = []

    for i, entry in enumerate(input_entries):
        test_input.append(entry.name)
        test_input.extend(entry.neighbors)
        test_input.append("")
        test_input.append(str(entry.nation) if entry.nation is not None else "")
        test_input.append(str(entry.settlement) if entry.settlement is not None else "")

        if entry.army:
            test_input.append("Y")
            test_input.extend(str(n) for n in entry.army)
        else:
            test_input.append("")

        if i < len(input_entries) - 1:
            test_input.append("")
        else:
            test_input.append("N")

    return test_input


def execute_test(expected: str) -> None:
    with NamedTemporaryFile() as tempfile:
        with patch("war_of_the_ring_ai.utils.data_entry.OUTFILE", new=tempfile.name):
            write_output_flow()
            tempfile.seek(0)
            assert tempfile.read().decode("utf8") == expected


@pytest.fixture(name="mock_input")
def fixture_mock_input() -> Iterable[MagicMock]:
    with patch.object(builtins, "input") as mock:
        yield mock


def test_write_simple_entry(mock_input: MagicMock) -> None:
    mock_input.side_effect = format_test_input(
        [InputEntry(name="Forlindon", neighbors=["Harlindon"])]
    )
    execute_test("Forlindon|Harlindon|None|None|0|0|0\n")


def test_write_entry_with_nation(mock_input: MagicMock) -> None:
    mock_input.side_effect = format_test_input(
        [InputEntry(name="Forlindon", neighbors=["Harlindon"], nation=0)]
    )
    execute_test("Forlindon|Harlindon|Elves|None|0|0|0\n")


def test_write_entry_with_settlement(mock_input: MagicMock) -> None:
    mock_input.side_effect = format_test_input(
        [InputEntry(name="Forlindon", neighbors=["Harlindon"], settlement=1)]
    )
    execute_test("Forlindon|Harlindon|None|Town|0|0|0\n")


def test_write_entry_with_army(mock_input: MagicMock) -> None:
    mock_input.side_effect = format_test_input(
        [InputEntry(name="Forlindon", neighbors=["Harlindon"], army=(1, 2, 3))]
    )
    execute_test("Forlindon|Harlindon|None|None|1|2|3\n")


def test_write_entry_with_multiple_neighbors(mock_input: MagicMock) -> None:
    mock_input.side_effect = format_test_input(
        [InputEntry(name="Forlindon", neighbors=["Harlindon", "The Shire", "Dagorlad"])]
    )
    execute_test("Forlindon|Harlindon,The Shire,Dagorlad|None|None|0|0|0\n")


def test_write_entry_with_all_attributes(mock_input: MagicMock) -> None:
    mock_input.side_effect = format_test_input(
        [
            InputEntry(
                name="Forlindon",
                neighbors=["Harlindon", "Dagorlad"],
                nation=1,
                settlement=1,
                army=(1, 2, 3),
            )
        ]
    )
    execute_test("Forlindon|Harlindon,Dagorlad|Dwarves|Town|1|2|3\n")


def test_write_multiple_entries(mock_input: MagicMock) -> None:
    mock_input.side_effect = format_test_input(
        [
            InputEntry(
                name="Forlindon",
                neighbors=["Harlindon", "Dagorlad"],
                nation=1,
                settlement=1,
                army=(1, 2, 3),
            ),
            InputEntry(
                name="The Shire",
                neighbors=["Moria", "Grey Havens"],
                nation=3,
                settlement=3,
            ),
        ]
    )
    execute_test(
        "Forlindon|Harlindon,Dagorlad|Dwarves|Town|1|2|3\n"
        "The Shire|Moria,Grey Havens|Rohan|Stronghold|0|0|0\n"
    )


def test_invalid_name(mock_input: MagicMock) -> None:
    mock_input.side_effect = ["fake-region"] + format_test_input(
        [InputEntry(name="Forlindon", neighbors=["Harlindon"])]
    )
    execute_test("Forlindon|Harlindon|None|None|0|0|0\n")


def test_missing_neighbors(mock_input: MagicMock) -> None:
    mock_input.side_effect = format_test_input(
        [InputEntry(name="Forlindon", neighbors=["", "Harlindon"])]
    )
    execute_test("Forlindon|Harlindon|None|None|0|0|0\n")


def test_invalid_neighbors(mock_input: MagicMock) -> None:
    mock_input.side_effect = format_test_input(
        [InputEntry(name="Forlindon", neighbors=["fake-region", "Harlindon"])]
    )
    execute_test("Forlindon|Harlindon|None|None|0|0|0\n")


def test_invalid_nation(mock_input: MagicMock) -> None:
    test_input = format_test_input(
        [InputEntry(name="Forlindon", neighbors=["Harlindon"], nation=4)]
    )
    test_input.insert(3, "100")
    mock_input.side_effect = test_input
    execute_test("Forlindon|Harlindon|Gondor|None|0|0|0\n")


def test_invalid_settlement(mock_input: MagicMock) -> None:
    test_input = format_test_input(
        [InputEntry(name="Forlindon", neighbors=["Harlindon"], settlement=3)]
    )
    test_input.insert(4, "4")
    mock_input.side_effect = test_input
    execute_test("Forlindon|Harlindon|None|Stronghold|0|0|0\n")


def test_invalid_army(mock_input: MagicMock) -> None:
    test_input = format_test_input(
        [InputEntry(name="Forlindon", neighbors=["Harlindon"], army=(2, 3, 3))]
    )
    test_input.insert(6, "1")
    test_input.insert(7, "not-a-number")
    test_input.insert(8, "4")
    test_input.insert(9, "Y")
    mock_input.side_effect = test_input
    execute_test("Forlindon|Harlindon|None|None|2|3|3\n")
