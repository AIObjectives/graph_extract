"""
Extract the "id" and the "1" option text from each scenario in nie_scenarios.json
and write them out to a CSV file.
"""
import csv
import json
from pathlib import Path

INPUT_PATH = Path(__file__).parent / "nie_scenarios.json"
OUTPUT_PATH = Path(__file__).parent / "nie_scenarios_option1.csv"


def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        scenarios = json.load(f)

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "option_1"])
        for scenario in scenarios:
            scenario_id = scenario.get("id")
            option_1 = scenario.get("options", {}).get("1")
            writer.writerow([scenario_id, option_1])

    print(f"Wrote {len(scenarios)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
