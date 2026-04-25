
from pathlib import Path
import yaml
import sys
import json
import os
import typer
import textwrap 
import importlib

ROOT_DIR = os.getcwd() + '/../'
sys.path.append(ROOT_DIR)

sys.path.append(ROOT_DIR+'src/')
print(ROOT_DIR)

import src.annotate_scenario as annotate_scenario
import src.translate_to_vis as translate_to_vis


def main(config_file: str):


    config_path = Path(ROOT_DIR+"/run_annotation/"+config_file)


    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    print(config)

    SCENARIO_DIR = config["input_path"]
    INPUT_FILE = config["input_file"]
    COMMIT_HASH = config["commit_hash"]
    OUTPUT_PATH = config["output_path"]
    SCENARIO_IDS = config.get("scenario_ids")
    WRITE_QUALTRICS = config.get("write_qualtrics")

    print(f'Reading from {ROOT_DIR + SCENARIO_DIR + INPUT_FILE}')
    print('Writing to output path: ', OUTPUT_PATH)

    with open(ROOT_DIR + SCENARIO_DIR + INPUT_FILE, 'r') as file:
        scenarios=json.load(file)

    # create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)


    for scenario_id in SCENARIO_IDS:

        # error handling for assumptions about json entries 
        scenario_json = None

        try:
            scenario_json = next(s for s in scenarios if s['id'] == scenario_id)
        except:
            # print("Check scenario filename or scenario id")
            raise IndexError('Check scenario id exists in json file!')
    
        if scenario_json:  
            # generate output file name based on input filename
            output_filename = ROOT_DIR + OUTPUT_PATH + INPUT_FILE.split('.json')[0] + '_' + str(scenario_id)

            #run annotation
            # for act_id in scenario_json['options'].keys():         
                # run the annotation process
            act_id = '1'
            json_filename = annotate_scenario.main(scenario_json,output_filename,act_id,COMMIT_HASH,WRITE_QUALTRICS)  
            print(f'Annotation saved to {json_filename}\n\n')

                # run the translation to vis process
            translate_to_vis.main(json_filename)

        
    

if __name__ == "__main__":
    typer.run(main)