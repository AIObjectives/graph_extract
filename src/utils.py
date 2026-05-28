import os
from pyexpat import model
import sys
import json
from openai import OpenAI
import requests
import textwrap
from dotenv import dotenv_values
from dotenv import load_dotenv
from pathlib import Path  # For Windows

# Set some environment and global variables
SCRIPT_DIR = Path(__file__).parent
# SCRIPT_DIR = Path(__name__).parent #if running in terminal
ROOT_DIR = SCRIPT_DIR.parent
load_dotenv(ROOT_DIR / ".env")
config = dotenv_values(ROOT_DIR / ".env")
OPENAI_API_KEY= config['OPENAI_API_KEY']

def return_config():
    """Returns all environment variables from .env file."""
    return config

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



def promptGPT(prompt_message_list, gpt_temperature=0, debug=False):


    client = OpenAI()   

    response = client.responses.create(
        model="gpt-5.4",
        input=prompt_message_list,
        reasoning={"effort": "medium"},
        text = { "format": {
            "type": "json_object" }
          },
        store= False,
    )
    
    llm_resp = response.output_text


    try:
        llm_resp_json = json.loads(llm_resp)
        return llm_resp_json
    except:
        print("error parsing LLM response")
        print("Raw LLM response:", llm_resp)
        return None




def get_response_dict(system_prompt_content, user_prompt_content):

    system_prompt= {
            "role": "system",
            "content": system_prompt_content
        }

    user_prompt = {
        "role": "user",
        "content": user_prompt_content,
    }

    try:
        response_dict = (promptGPT([system_prompt,user_prompt],0,False))

    except Exception as e:
        print(f"Error occurred: {e}")  
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

