
from pathlib import Path
import yaml
import json
import os
import typer
import textwrap 
import src.annotate_scenario as annotate_scenario
import src.translate_to_vis as translate_to_vis
import importlib
importlib.reload(annotate_scenario)
importlib.reload(translate_to_vis)


def main(config_file):


    config_path = Path("run_annotation/"+config_file)

    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    SCENARIO_DIR = config["input_path"]
    INPUT_FILE = config["input_file"]
    COMMIT_HASH = config["commit_hash"]
    OUTPUT_PATH = config["output_path"]
    SCENARIO_IDS = config.get("scenario_ids")
    WRITE_QUALTRICS = config.get("write_qualtrics")

    with open(SCENARIO_DIR+INPUT_FILE, 'r') as file:
        scenarios=json.load(file)

    # error handling for assumptions about json entries
    try:
        scenario_json = scenarios[scenario_id]
    except:
        # print("Check scenario filename or scenario id")
        raise IndexError('Check scenario id exists in json file!')

    assert isinstance(scenario_json['id'],int)
    assert scenario_json['text']
    assert scenario_json['options']

    # display the scnenario text read in 
    this_scenario_text = scenario_json["text"]    
    print('Scenario Text: \n\n')
    print(textwrap.fill(this_scenario_text, width = 100), '\n\n')

    # generate output file name based on input filename
    output_filepath = OUTPUT_PATH+INPUT_FILE.split('.json')[0]+'/'

    # create output directory if it doesn't exist
    if not os.path.exists(output_filepath):
        os.makedirs(output_filepath)


    for scenario_id in SCENARIO_IDS:
        
        output_filename = output_filepath+str(scenario_id)

        for act_id in scenario_json['options'].keys():         
        
            # run the annotation process
            json_filename = annotate_scenario.main(scenario_json,output_filename,act_id,COMMIT_HASH,WRITE_QUALTRICS)  
            print(f'Annotation saved to {json_filename}\n\n')

            # run the translation to vis process
            translate_to_vis.main(json_filename)

    

if __name__ == "__main__":
    typer.run(main)