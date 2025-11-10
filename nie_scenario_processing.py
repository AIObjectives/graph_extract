# Processing TXT files from MoCa dataset
from pathlib import Path
import sys
import json

# Establishing paths
NIE_SCENARIO_DIR = Path().resolve() / "scenarios" / "nie_moral_stories"
print(NIE_SCENARIO_DIR)
scenarios_output_path = Path().resolve() / "scenarios"
print(scenarios_output_path)

file_name = input("Enter output file name here: ").strip()
if not file_name:
    print("No output filename provided. Exiting.")
    sys.exit(1)

output_path = scenarios_output_path / file_name

# Retrieving previously processed data
already_processed = []
if output_path.exists():
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            already_processed = json.load(f)
            if not isinstance(already_processed, list):
                print("Existing output file is empty. Overwriting with new content.")
                already_processed = []
    except Exception as e:
        print("Could not read existing output file, starting fresh:", e)
        already_processed = []

processed_ids = {p.get("id") for p in already_processed}
big_list = already_processed[:]

# Defining a function for scenario ID extraction
def extract_id_from_name(name: str):
    digits = ''.join(filter(str.isdigit, name))
    if digits:
        return int(digits)
    return name

# Sorting files before iterating through them
scenario_files = sorted([p for p in NIE_SCENARIO_DIR.iterdir() if p.is_file()])
for scenario_file in scenario_files:
    
    # Grabbing the scenario ID
    sid = extract_id_from_name(scenario_file.name)

    if str(sid) in processed_ids:
        continue

    # Reading scenario from file
    with open(scenario_file, 'r') as my_file:
        scenario_info = {
            "id": sid,
            "text": ""
        }

        for line in my_file:
            stripped_line = line.strip()
            if stripped_line != "":
                scenario_info["text"] += (" " + stripped_line)
                continue
            break
        
        print("\n---")
        print("File:", scenario_file.name)
        print("ID:", scenario_info["id"])
        print("Text:", scenario_info["text"].strip())
        print("---")
        
        option1 = input("Enter option 1 here: ")
        option2 = input("Enter option 2 here: ")

        if option1.lower() == 'q' or option2.lower() == 'q':
            print("Quitting and saving progress...")
            break

        scenario_info["options"] = {"1": option1, "2": option2}
    
    big_list.append(scenario_info)
    processed_ids.add(str(scenario_info["id"]))

    # Saving progress per scenario
    try:
        tmp_path = output_path.parent / (output_path.name + ".tmp")
        with open(tmp_path, 'w', encoding='utf-8') as output_file:
            json.dump(big_list, output_file)
        tmp_path.replace(output_path)  # Atomic replacement
    except Exception as e:
        print("Failed to save progress:", e)

print("Scenario processing complete.")
