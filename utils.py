import json
import requests

from dotenv import dotenv_values
from dotenv import load_dotenv

# set some environment and global variables
load_dotenv() 
global config
config = dotenv_values(".env")


# function to query GPT via openai API
def promptGPT(prompt_message_list, gpt_temperature=0, debug=False):
    gpt_url = "https://api.openai.com/v1/chat/completions"
    gpt_headers = {
        "Content-Type": "application/json",
        "Authorization": config['OPENAI_API_KEY']
    }
    gpt_data = {
            # "model": "gpt-3.5-turbo-1106", 
            "model": "gpt-4.1",
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


    