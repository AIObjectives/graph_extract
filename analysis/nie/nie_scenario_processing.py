# Processing TXT files from MoCa dataset
from pathlib import Path
import sys
import json
import src.utils as utils

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

# Keep track of skipped scenarios
to_skip = []
try:
    with open(scenarios_output_path / "skipped_scenarios.json", "r") as skip_file:
        to_skip = json.load(skip_file)
        if not isinstance(to_skip, list):
            to_skip = []
except Exception as e:
    print(e)
    to_skip = []

processed_ids = {str(p.get("id")) for p in already_processed}
skip_ids = {str(p.get("id")) for p in to_skip}
processed_ids = processed_ids.union(skip_ids)
big_list = already_processed[:]

# Defining a function for scenario ID extraction
def extract_id_from_name(name: str) -> int:
    digits = ''.join(filter(str.isdigit, name))
    if digits:
        return int(digits)
    return name

# Defining a function to change the scenario to 1st-person perspective
def change_to_first_perspective(scenario_text: str) -> dict:
    system_prompt_content = """"You are an expert in English grammar. Rewrite the following text so that it is written in the first person perspective instead of in the second person or third person perspectives (the text will originally be written in one of the two perspectives), replacing each reference of any second person pronouns or the text's main protagonist with the correct first-person pronoun (I, me, my, our, we, etc.) depending on the text's original perspective. Return a json called 'converted sentence' with the converted text only."""
    user_prompt_content = scenario_text
    GPT_response = utils.get_response_dict(system_prompt_content, user_prompt_content)
    return GPT_response["converted sentence"]

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

        # Reading in scenario text
        for line in my_file:
            stripped_line = line.strip()
            if stripped_line != "":
                scenario_info["text"] += (" " + stripped_line)
                continue
            break

        temp_text = change_to_first_perspective(scenario_info["text"])
        
        print("\n---")
        print("File:", scenario_file.name)
        print("ID:", scenario_info["id"])
        print("Text:", scenario_info["text"].strip(), "\n")
        print("1st-Person Text:", temp_text)
        print("---")

        keep_text = input("Replace original text with edited 1st-person text? (Y/N): ").upper()
        if keep_text == "Y":
            scenario_info["text"] = temp_text
            print("Updated to 1st-person perspective.")
        else:
            print("Kept original text.")
        
        option1 = input("Enter option 1 here: ")
        option2 = input("Enter option 2 here: ")

        if option1.lower() == 'q' or option2.lower() == 'q':
            print("Quitting and saving progress...")
            break
        elif option1.lower() == 'rm' or option2.lower() == 'rm':
            print("Skipping scenario...")
            to_skip.append(scenario_info)  # No options included
            processed_ids.add(str(scenario_info["id"]))
            try:
                tmp_path = scenarios_output_path / "skipped_scenarios.tmp"
                with open(tmp_path, 'w', encoding='utf-8') as output_file:
                    json.dump(to_skip, output_file)
                tmp_path.replace(scenarios_output_path / "skipped_scenarios.json")  # Atomic replacement
            except Exception as e:
                print("Failed to save progress:", e)
            continue

        scenario_info["options"] = {"1": option1, "2": option2}

        # Reading in factor labels
        scenario_info["factors"] = {"1": {}, "2": {}}
        read_factor = False
        for line in my_file:
            stripped_line = line.strip()
            if stripped_line.startswith("Factors:"):
                read_factor = True
            elif stripped_line.startswith("Annotated"):
                read_factor = False
                break
            elif read_factor == True and stripped_line != "":
                factor_info = stripped_line.split(": ")
                scenario_info["factors"]["1"][factor_info[0]] = factor_info[1]
    
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
    
    user_continue = input("Continue processing scenarios? (Y/N): ").upper()
    if user_continue == "N":
        break

print("Scenario processing complete.")
