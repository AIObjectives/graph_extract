import json
import os
import textwrap 
import typer
import annotate_scenario
import translate_to_vis
import importlib
importlib.reload(annotate_scenario)
importlib.reload(translate_to_vis)



CUR_DIR = os.path.dirname(os.path.abspath(__name__))
DATA_DIR = CUR_DIR+'formatted_franken/data/conditions_mild_harm_mild_good/'


# filename = 'scenarios.json'
# scenario_id = 3

def main(filename: str = 'cc_evitable_action_yes_stories.json', scenario_id: int = 0):
    # for filename in os.listdir(DATA_DIR):
    with open(DATA_DIR+filename, 'r') as file:
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
    output_filename = filename.split('.json')[0]+'_'+str(scenario_id)

    # loop through action choices to generate basic json, value json, and visualization
    for act_id in scenario_json['options'].keys(): 
    
        # run the annotation process
        json_filename = annotate_scenario.main(scenario_json,output_filename,act_id)  

        # json_filename = '/Users/anna/Dropbox/AOI/MoralLearning/CodeSets/graph_extract/data/scenarios_0_choice_1.json'
        translate_to_vis.main(json_filename)

    

if __name__ == "__main__":
    typer.run(main)