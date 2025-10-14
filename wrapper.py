import json
import os
import textwrap 
import typer
import src.annotate_scenario as annotate_scenario
import src.translate_to_vis as translate_to_vis
import importlib
import pandas as pd
importlib.reload(annotate_scenario)
importlib.reload(translate_to_vis)


CUR_DIR = os.path.dirname(os.path.abspath(__name__))
# DATA_DIR = CUR_DIR+'/data/'
DATA_DIR = CUR_DIR+'/formatted_franken/data/conditions_mild_harm_mild_good/'
DATA_DIR_HUMAN = DATA_DIR+'/human_annotation/'


# filename = 'scenarios.json'
# scenario_id = 1

def main(filename: str = 'cc_evitable_action_yes_stories.json', scenario_id: int = 0):

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
    # act_id = '2'
    for act_id in scenario_json['options'].keys(): 

        #load some human annotation data
        this_human_filename = DATA_DIR_HUMAN+output_filename+'_choice_'+str(act_id)+'_value_scores.csv'
        all_human_data= {}
        if os.path.exists(this_human_filename):
            #load csv file
             this_human_data = pd.read_csv(this_human_filename)
             #use value_names as keys and mean as values and make a dictionary
             all_human_data['value_scores']= this_human_data.set_index('value_names')['mean'].to_dict()
        else:
            print('No human annotation data found for this scenario and action choice.')
            
    
        # run the annotation process
        json_filename = annotate_scenario.main(scenario_json,output_filename,act_id,all_human_data)  

        # json_filename = '/Users/anna/Dropbox/AOI/MoralLearning/CodeSets/graph_extract/data/scenarios_0_choice_1.json'
        # translate_to_vis.main(json_filename)

    

if __name__ == "__main__":
    typer.run(main)