import pandas as pd
import json    
import src.prompts
from functools import reduce

## FUNCTIONS TO READ IN SCENARIO JSONS

def parse_filename_cheung(filename):
    """parse the read in filenames to get the condition and id
    assuming filename is of the form "%s_%d_choice_1.json"""

    parts = filename.stem.split("_")
    narrative = parts[0]
    id = int(parts[1])
    return narrative, id

def parse_filename_nie(filename):

    # parse id by looking at outputs_json file name and splitting by underscore and looking for the first number in the split that is a digit and converting it to an int
    id = None
    for part in filename.split("/")[-1].split("_"):
        if part.isdigit():
            id = int(part)
            # print(f"Parsed id {id} from outputs_json file name: {outputs_json}")
            break
    if id is None:
        raise ValueError(f"Could not parse id from outputs_json file name: {filename}")
    return id

def read_input_scenario(scenario_json_filename, id):
    """ returns the scenario data for the given id from the given json file """

    with open(scenario_json_filename, 'r') as f:
        inputs_data = json.load(f)

    # find the scenario with the given id and get its data
    scenario_data = None
    for scenario in inputs_data:
        if scenario.get("id") == id:
            scenario_data = scenario
            break
    if not scenario_data:
        raise ValueError(f"Scenario with id {id} not found in {scenario_json_filename}")
    else:
        scenario_inputs = {k: v for k, v in scenario_data.items()}

    return scenario_inputs


### FUNCTIONS TO READ IN ANNOTATIONS

def read_annotation(file_path):
    """ Takes an annotated json file path and returns all the nodes as a list of dicts. """

    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    nodes = [json.loads(line.strip()) for line in lines if line.strip()]

    return nodes


## FUNCTIONS TO PARSE READ IN ANNOTATION NODES

def extract_beings(nodes):

    try:
        being_nodes = [n for n in nodes if n.get('node', {}).get('kind') == 'being']
    except KeyError:
        return {}

    being_labels = {n['node']['label'] for n in being_nodes}

    return being_labels

def extract_action(nodes):
    
    value = None

    for node in nodes:
        n = node.get('node',{})
        if n.get('kind') == 'action_choice':
            # print(n.get('label'))
            label = n.get('label')
    
    

    return label

def extract_outcomes(nodes):

    event_nodes = [n for n in nodes if n.get('node', {}).get('kind') == 'event']

    events_I = []
    events_Ziv = []

    for event_node in event_nodes:
        event_label = event_node['node']['label']
        events_I.append(event_label)
        events_Ziv.append(prompts.convert_I_Ziv(event_label))

    return events_Ziv, events_I

def events_to_utility_df(nodes):
  
    util_dfs = []

    for node in nodes:
        n = node.get('node',{})
        if n.get('kind') == 'event':
            links = node.get('links')
            data = {}
            for link in links:
                to_node = link.get('to_node')
                value = link.get('link', {}).get('value')
                data[to_node] = value
                label = n.get('label')
                df = pd.DataFrame([data], index=[label])
            util_dfs.append(df)

    df = pd.concat(util_dfs, ignore_index=False)
    df = df.apply(pd.to_numeric)
    
    return df


def extract_deontology(nodes):
    
    value = None

    for node in nodes:
        n = node.get('node',{})
        if n.get('kind') == 'action_choice':
            # print(n.get('label'))
            links = node.get('links')
            # print(links)
            for link in links:
                    # print(link)
                    if link.get('link', {}).get('kind')=='v-link':
                        value = link.get('link', {}).get('value')
    

    return value




def get_mean_utilities(nodes):

    util_df =  events_to_utility_df(nodes)


    # For each being (column), calculate product of positive and negative utilities across outcomes
    utility_products = {}
    for col in util_df.columns:
        positive_utils = util_df[col][util_df[col] > 0]
        negative_utils = util_df[col][util_df[col] < 0]
        pos_product = reduce(lambda x, y: x * y, positive_utils, 1) if not positive_utils.empty else 0
        neg_product = reduce(lambda x, y: x * y, negative_utils, 1) if not negative_utils.empty else 0
        utility_products[col] = {"positive_product": pos_product, "negative_product": neg_product, "difference": pos_product - neg_product}

        util_mean_df = pd.DataFrame({'mean_utility': util_df.mean()})
    
    return util_mean_df

def parse_cik(cik_str):
    return {
        letter: (cik_str[cik_str.find(letter) + 1] if cik_str.find(letter) != -1 and cik_str.find(letter) + 1 < len(cik_str) else None)
        for letter in ["C", "I", "K"]
    }

def get_cik_links(nodes):
    
    cik_df  = pd.DataFrame()

    #get the annotation node referring to being I
    being_i_node = next(
    (
        node for node in nodes
        if node.get("node", {}).get("kind") == "being"
        and node.get("node", {}).get("label") == "i" or node.get("node", {}).get("label") == "I"
    ),
    None
    )

    if not being_i_node:
        raise ValueError("No being node with label 'i' or 'I' found in the nodes.")
    
    else:
        #loop through each link from I to events, and get the CIK values, returning a df
        for link in being_i_node.get("links", []):
            sub_link = link.get("link", {})
            if sub_link.get("kind") == "b_link": 
                CIK =  sub_link.get("value")
                cik_dict = parse_cik(CIK)

                event = link.get("to_node")       

                row = {
                    "event": event,
                    "C": cik_dict.get("C"),
                    "I": cik_dict.get("I"),
                    "K": cik_dict.get("K"),
                }
                cik_df = pd.concat([cik_df, pd.DataFrame([row])], ignore_index=True)

    return cik_df



## DEPRECATED ARCHIVE
#below could be improved by having named fields for utility and C/I/K instead of relying on order in the list, but this is fine for now since we are consistent in how we generate the annotations
def parse_annotation(file_path):
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