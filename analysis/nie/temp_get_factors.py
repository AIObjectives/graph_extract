from pathlib import Path
import sys
import json
import src.utils as utils

# Establishing paths
scenarios_output_path = Path().resolve() / "scenarios_inputs" / "nie"
print(scenarios_output_path)

with open(scenarios_output_path / "nie_scenarios.json", "r") as f:
    my_scenarios = json.load(f)

for scenario in my_scenarios:
    factor_info = {}
    if "Locus" in scenario["factors"]["1"].keys():
        continue
    elif scenario["factors"]["1"] == {}:
        continue
    else:
        print(f"\nScenario {scenario["id"]}:\n")
        for factor, label in scenario["factors"]["1"].items():
            print(f"\n\t{factor}: {label}")
            user_label = input("Your label: ")
            factor_info[factor] = user_label

        print(f"Confirm accuracy: {factor_info}")
        user_check = input("Keep? (Y/N): ")
        if user_check.lower() == "y":
            scenario["factors"]["2"] = factor_info
            print("Saved.")
        else:
            print("Original kept.")
