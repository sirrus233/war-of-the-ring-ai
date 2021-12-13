import csv
from dataclasses import dataclass, field

from war_of_the_ring_ai.game_objects import (
    CharacterID,
    Companion,
    ElvenRings,
    Fellowship,
    Nation,
    PoliticalStatus,
)

INITIAL_COMPANION_IDS = [
    CharacterID.GANDALF_GREY,
    CharacterID.STRIDER,
    CharacterID.GIMLI,
    CharacterID.LEGOLAS,
    CharacterID.BOROMIR,
    CharacterID.MERRY,
    CharacterID.PIPPIN,
]

INITIAL_GUIDE_ID = CharacterID.GANDALF_GREY


def init_fellowship() -> Fellowship:
    initial_companions = []
    with open("data/characters.csv", newline="", encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter="|")
        for name, level, leadership in reader:
            if CharacterID[name] in INITIAL_COMPANION_IDS:
                companion = Companion(CharacterID[name], int(level), int(leadership))
                initial_companions.append(companion)
    guide = next(c for c in initial_companions if c.name == CharacterID.GANDALF_GREY)
    return Fellowship(initial_companions, guide)


def init_politics() -> dict[Nation, PoliticalStatus]:
    politics = {}
    with open("data/politics.csv", newline="", encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter="|")
        for nation, disposition, active in reader:
            politics[Nation[nation]] = PoliticalStatus(
                int(disposition), active == "active"
            )
    return politics


@dataclass
class GameState:
    fellowship: Fellowship = field(default_factory=init_fellowship)
    elven_rings: ElvenRings = field(default_factory=ElvenRings)
    politics: dict[Nation, PoliticalStatus] = field(default_factory=init_politics)
