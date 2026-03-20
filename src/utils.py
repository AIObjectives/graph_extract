import os
import sys
import json
import requests
import textwrap
from dotenv import dotenv_values
from dotenv import load_dotenv
from pathlib import Path  # For Windows

# Set some environment and global variables
NOTEBOOK_DIR = Path().resolve()
ROOT_DIR = NOTEBOOK_DIR.parent
load_dotenv(ROOT_DIR / ".env")
api_key = os.getenv("OPENAI_API_KEY")

def open_scenario(SCENARIO_DIR, FILENAME, SCENARIO_ID, ACT_ID):
    """
    Opens a scenario file and returns its content.
    """
    scenario_path = os.path.join(SCENARIO_DIR, FILENAME)
    with open(scenario_path, 'r') as file:
        all_scenarios = json.load(file)
        
    # error handling for assumptions about json entries
    try:
        scenario_json = {}
        for scenario in all_scenarios:
            if scenario["id"] == SCENARIO_ID:
                scenario_json = scenario
                break
    except:
        # print("Check scenario filename or scenario id")
        scenario_json = {}
        raise IndexError('Check scenario id exists in json file!')
    
    #make sure action id is in the scenario
    if ACT_ID not in scenario_json['options']:
        raise ValueError(f"Action ID {ACT_ID} not found in scenario options.")


    # display the scnenario text read in 
    this_scenario_text = scenario_json["text"]    
    print('Scenario Text: \n\n')
    print(textwrap.fill(this_scenario_text, width = 100), '\n\n')


    return scenario_json

# function to reformat impacts_df so that it can be incorporated into util_data. create a new columns in util_data for new_scores and enter the scores according to entity and outcome.
def reformat_impacts(impacts_df, util_data):
    for impact in impacts_df:
        outcome = impact[0]
        entities_list = impact[1]
        scores_list = impact[2]
        assert len(entities_list) == len(scores_list)    
        for entity, score in zip(entities_list, scores_list):
            util_data.loc[(util_data['entity'] == entity) & (util_data['outcome'] == outcome), 'new_scores'] = score
    return util_data


# function to query GPT via openai API
def promptGPT(prompt_message_list, gpt_temperature=0, debug=False):
    gpt_url = "https://api.openai.com/v1/chat/completions"
    gpt_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"  # Previously: config['OPENAI_API_KEY']
    }
    gpt_data = {
            # "model": "gpt-3.5-turbo-1106", 
            "model": "gpt-4.1-mini",
            #  "model": "o3-2025-04-16",
            "response_format": {"type": "json_object"}, # only works on 3.5-turbo-1106, 4 and above
            "temperature": gpt_temperature,
            "messages": prompt_message_list,
    }
    response = requests.post(gpt_url, headers=gpt_headers, json=gpt_data)    
    if(debug==True):
        output = response.json()
        print(response)
    else:
        output = response.json()['choices'][0]['message']['content']

    return output


def get_response_dict(system_prompt_content, user_prompt_content):
    system_prompt= {
            "role": "system",
            "content": system_prompt_content
        }

    user_prompt = {
        "role": "user",
        "content": user_prompt_content,
    }
    # print([system_prompt,user_prompt])
    try:
        response_dict = json.loads(promptGPT([system_prompt,user_prompt],0,False))
    except:
        debug_resp = promptGPT([system_prompt,user_prompt],0,True)
        print(debug_resp)
        response_dict = {}
    return response_dict



def write_jsonlines(fname,jlist):
    jsonl_file =  open(fname, 'w')  
    for dictionary in jlist:
        jsonl_file.write(json.dumps(dictionary) + '\n')

    jsonl_file.close()


def write_json(fname,dictionary):
    json_file =  open(fname, 'w')     
    json_file.write(json.dumps(dictionary))
    json_file.close()


    