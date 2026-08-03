from pathlib import Path
import json
import pandas as pd
import numpy as np
from IPython.display import display, HTML

def parse_events_with_labels(file_path):
    """
    Parses a JSON file containing event and being nodes and returns a dictionary
    mapping being labels to event labels and their associated utility values.
    Args:
    file_path (str): The path to the JSON file.
    Returns:
    dict: A dictionary with being labels as keys and dictionaries of event labels
          and their utility values as values.
    """
    with open(file_path, 'r') as f:
        lines = f.readlines()

    nodes = [json.loads(line.strip()) for line in lines if line.strip()]

    being_nodes = [n for n in nodes if n.get('node', {}).get('kind') == 'being']
    if not being_nodes:
        return {}

    being_labels = {n['node']['label'] for n in being_nodes}

    event_nodes = [n for n in nodes if n.get('node', {}).get('kind') == 'event']

    # Build b-link lookup from being nodes that actually have links
    # { being_label: { event_label: b_link_value } }
    b_links = {}
    for being_node in being_nodes:
        being_label = being_node['node']['label']
        for link in being_node.get('links', []):
            to_node = link.get('to_node')
            value = link.get('link', {}).get('value')
            if to_node and value:
                b_links.setdefault(being_label, {})[to_node] = value

    # Build results from event nodes outward
    results = {label: {} for label in being_labels}

    # Find the v-link value (deontic rating), which lives on the action_choice node's links,
    # not as its own top-level node -- there is always exactly one per file
    for node in nodes:
        for link in node.get('links', []):
            if link.get('link', {}).get('kind') == 'v-link':
                results['deontic'] = link.get('link', {}).get('value')
                break

    for event_node in event_nodes:
        event_label = event_node['node']['label']
        for link in event_node.get('links', []):
            if link.get('link', {}).get('kind') == 'utility':
                being_label = link.get('to_node')
                utility_value = link.get('link', {}).get('value')
                if being_label in being_labels:
                    b_link_value = b_links.get(being_label, {}).get(event_label)
                    entry = []
                    if b_link_value:
                        entry.append(b_link_value)
                    entry.append(utility_value)
                    results[being_label][event_label] = entry

    return results

def read_scenario_input_output(inputs_json, outputs_json):
    """
    Reads a scenario input and output file and returns a df with the events and their labels for both choices.
    Args:
    inputs_json: The path to the scenario input json file
    outputs_json: The path to the scenario output json file
    Returns:
    pd.DataFrame: A DataFrame with columns "SID", "option", "event", "C", "I", "K", "utility", and a column for all other keys in the json
    """
    # print ("current directory:", Path.cwd())

    # parse id by looking at outputs_json file name and splitting by underscore and looking for the first number in the split that is a digit and converting it to an int
    id = None
    for part in outputs_json.split("/")[-1].split("_"):
        if part.isdigit():
            id = int(part)
            # print(f"Parsed id {id} from outputs_json file name: {outputs_json}")
            break
    if id is None:
        raise ValueError(f"Could not parse id from outputs_json file name: {outputs_json}")

    # read the inputs file json and get all the keys and values for the scenario with the given id and add them to the df as columns
    with open(inputs_json, 'r') as f:
        inputs_data = json.load(f)
    # find the scenario with the given id and get its data
    scenario_data = None
    for scenario in inputs_data:
        if scenario.get("id") == id:
            scenario_data = scenario
            break
    if not scenario_data:
        raise ValueError(f"Scenario with id {id} not found in {inputs_json}")
    else:
        scenario_inputs = {k: v for k, v in scenario_data.items()}

    results = parse_events_with_labels(outputs_json)
    # pull the deontic value out before iterating results as {being: {event: labels}} below
    deontic_value = results.pop('deontic', None)

    scenario_df = []

    # Restructure: event -> { being -> labels }
    events_by_event = {}
    for being, events in results.items():
        for event, labels in events.items():
            events_by_event.setdefault(event, {})[being] = labels

    for event, being_labels in events_by_event.items():
        try:
            # Get C/I/K from "i" being
            i_labels = being_labels.get("i", [])
            cik = i_labels[0] if i_labels and len(i_labels) > 1 else None

            # Build utility dict: each being -> their utility value
            utility = {
                being: labels[-1]  # utility is always last in the list
                for being, labels in being_labels.items()
            }

            row = {
                "SID": id,
                "option": f"1: {scenario_inputs['options']['1']}" if outputs_json.split("/")[-1].endswith("1.json") else f"2: {scenario_inputs['options']['2']}",
                "event": event,
                "being": "i",
                "C": cik[1] if cik else None,
                "I": cik[3] if cik else None,
                "K": cik[5] if cik else None,
                "utility": utility,
                "deontic": deontic_value
            }
        except Exception as e:
            print(f"Error processing event '{event}' in file {outputs_json}: {e}")
            continue
        # add all the other keys and values from the scenario inputs to the row -- the value could be anything (str, int, list, dict) so we will just add it as is and not try to parse it
        for key, value in scenario_inputs.items():
            if key not in row and key not in ["options", "text", "id"]: # we don't need to add the options or text or id to the row since we already have the option and id in the row and text makes the df too long
                row[key] = value
        scenario_df.append(row)

    return pd.DataFrame(scenario_df)


def read_all_scenarios(inputs_json, outputs_dir):
    """
    Reads all scenarios from a given dataset and returns a df with the events and their labels for both choices.
    Args:
    inputs_json: The path to the scenario input json file
    outputs_dir: The directory where the scenario output json files are located
    Returns:
    pd.DataFrame: A DataFrame with columns "SID", "option", "event", "C", "I", "K", "utility", and a column for all other keys in the json
    """
    all_scenarios_df = pd.DataFrame()
    json_filename_stem = inputs_json.split("/")[-1].split(".")[0]
    for output_file in Path(outputs_dir).glob("*.json"):
        # print(f"Processing output file: {output_file}")
        if json_filename_stem in str(output_file).split("/") or json_filename_stem in str(output_file).split("/")[-1]:
            scenario_df = read_scenario_input_output(inputs_json, str(output_file))
            all_scenarios_df = pd.concat([all_scenarios_df, scenario_df], ignore_index=True)
    return all_scenarios_df


def utility_df_maker(scenario_df):
    """
    Takes in a scenario df from the output of read_all_scenarios and returns a df with the average utility for each being in the utility column across all events per scenario. The utility column contains a dictionary with the being as the key and the utility value as the value. Do not use the "being" column in the original df since that only tells us which being the C/I/K labels are for, and the utility column is where we can get the utility values for all beings.
    
    The utility scenarios are divided by "SID" column for nie dataset, by "scenario_title" then by "SID" for cheung dataset, and by "intensity" then by "causal_condition" then by "SID" for franken dataset. We can identify what dataset it is because only cheung dfs will have a "scenario_title" column and only franken will have an "intensity" column, and nie has neither. 
    
    The resulting df has columns "SID", "option", "being", and "average_utility" and the columns that we used to group the data.

    Args:
    scenario_df: A DataFrame with columns "SID", "option", "event", "C", "I", "K", "utility", and a column for all other keys in the json
    Returns:
    pd.DataFrame: A DataFrame with columns "SID", "option", "being", and "average_utility"
    """

    if "scenario_title" in scenario_df.columns and "intensity" not in scenario_df.columns:
        group_cols = ["scenario_title", "SID", "option"]
    elif "intensity" in scenario_df.columns:
        group_cols = ["intensity", "causal_condition", "SID", "option"]
    else:
        group_cols = ["SID", "option"]

    utility_rows = []
    for _, group in scenario_df.groupby(group_cols):
        sid = group["SID"].iloc[0]
        option = group["option"].iloc[0]
        being_utilities = {}
        for utility_dict in group["utility"]:
            if isinstance(utility_dict, dict):
                for being, utility_value in utility_dict.items():
                    being_utilities.setdefault(being, []).append(int(utility_value))
        
        for being, utilities in being_utilities.items():
            average_utility = np.mean(utilities)
            row = {
                "SID": sid,
                "option": option,
                "being": being,
                "average_utility": average_utility
            }
            for col in group_cols:
                if col not in row:
                    row[col] = group[col].iloc[0]
            utility_rows.append(row)
    return pd.DataFrame(utility_rows)