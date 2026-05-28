import json
import os
import textwrap 
import typer
import sys

ROOT_DIR = os.getcwd() + '/../'
sys.path.append(ROOT_DIR)

sys.path.append(ROOT_DIR+'src/')

# import annotate_scenario
import src.annotate_scenario as annotate_scenario
# import translate_to_vis
import src.translate_to_vis as translate_to_vis
import importlib
importlib.reload(annotate_scenario)
importlib.reload(translate_to_vis)


CUR_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# SEVERITY = 'conditions_mild_harm_mild_good/'  # adjust as needed
SEVERITY = 'conditions_severe_harm_very_good/'  # adjust as needed
SCENARIO_DIR = CUR_DIR+'/scenarios_inputs/franken/'+SEVERITY
OUTPUT_DIR = CUR_DIR+'/annotated_outputs/franken_05-14-2026/'+SEVERITY

def main():

    filenames = [
        "cc_evitable_action_yes_stories.json",
        "cc_evitable_prevention_no_stories.json",
        "cc_inevitable_action_yes_stories.json",
        "cc_inevitable_prevention_no_stories.json",
        "coc_evitable_action_yes_stories.json",
        "coc_evitable_prevention_no_stories.json",
        "coc_inevitable_action_yes_stories.json",
        "coc_inevitable_prevention_no_stories.json"
        ]

    for filename in filenames:

        with open(SCENARIO_DIR+filename, 'r') as file:
            scenarios=json.load(file)

        for scenario_id in range(0,10): # go from 0 to 9

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
            output_filepath = OUTPUT_DIR+filename.split('.json')[0]+'/'
            # create output directory if it doesn't exist
            if not os.path.exists(output_filepath):
                os.makedirs(output_filepath)
            output_filename = output_filepath+str(scenario_id)

            # for act_id in scenario_json['options'].keys():   

            choice = "1" if filename.endswith("action_yes_stories.json") else "2"  # determine choice based on filename      
            
            # run the annotation process
            json_filename = annotate_scenario.main(scenario_json,output_filename,choice,"581b7f065762e9e17b0203edbc94d0b99ebe9528",False)  
            print(f'Annotation saved to {json_filename}\n\n')

            # run the translation to vis process
            translate_to_vis.main(json_filename)

    

if __name__ == "__main__":
    typer.run(main)
