"""Interactive workflow script to perform data entry for the region map."""
import csv

OUTFILE = "data/worldmap.csv"
DELIMITER = "|"

with open("data/alphabetical.txt", encoding="utf8") as f:
    REGIONS = {region.strip() for region in f.readlines()}

NATIONS = {
    0: "Elves",
    1: "Dwarves",
    2: "North",
    3: "Rohan",
    4: "Gondor",
    5: "Sauron",
    6: "Isengard",
    7: "S&E",
}

SETTLEMENTS = {
    0: "Fortification",
    1: "Town",
    2: "City",
    3: "Stronghold",
}


def get_region() -> str:
    """Query the name of the region."""
    region = input("New Region: ")

    if region not in REGIONS:
        print("Invalid region.")
        return get_region()

    return region


def get_neighbors() -> str:
    """Query names of all regions adjacent to the current region."""
    neighbor_list = []

    while neighbor := input("Neighbor: "):
        if neighbor not in REGIONS or neighbor in neighbor_list:
            print("Invalid region.")
            continue
        neighbor_list.append(neighbor)

    if not neighbor_list:
        print("All regions must have neighbors.")
        return get_neighbors()

    return ",".join(neighbor_list)


def get_nation() -> str:
    """Query the nation this region belongs to, if any."""
    for i, nation in NATIONS.items():
        print(f"[{i}] {nation}")

    if choice := input("Nation: "):
        if not choice.isdigit() or int(choice) not in NATIONS:
            print("Invalid selection.")
            return get_nation()
        return NATIONS[int(choice)]

    return "None"


def get_settlement() -> str:
    """Query the type of settlement in this region, if any."""
    for i, settlement in SETTLEMENTS.items():
        print(f"[{i}] {settlement}")

    if choice := input("Settlement: "):
        if not choice.isdigit() or int(choice) not in SETTLEMENTS:
            print("Invalid selection.")
            return get_settlement()
        return SETTLEMENTS[int(choice)]

    return "None"


def get_army() -> list[str]:
    """Query what army units should start in this region, if any."""
    if input("Armies (Default: no): "):
        regulars = input("Regulars: ")
        elites = input("Elites: ")
        leaders = input("Leaders: ")
        if not (regulars.isdigit() and elites.isdigit() and leaders.isdigit()):
            print("Invalid non-numeric input.")
            return get_army()
        return [regulars, elites, leaders]

    return ["0", "0", "0"]


def write_output_flow() -> None:
    """Top-level workflow. Ask for region details in a loop until finished. Work can
    be performed iteratively across multiple invocations of the script.
    """
    startup = True
    with open(OUTFILE, "a", newline="", encoding="utf8") as csvfile:
        writer = csv.writer(csvfile, delimiter=DELIMITER)
        while startup or not input("Continue (Default: yes): "):
            startup = False
            row = [
                get_region(),
                get_neighbors(),
                get_nation(),
                get_settlement(),
            ] + get_army()
            print(row)
            writer.writerow(row)


if __name__ == "__main__":
    write_output_flow()
