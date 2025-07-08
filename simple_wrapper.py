import json
import os
import textwrap
import annotate_scenario
import translate_to_vis
import importlib
importlib.reload(annotate_scenario)
importlib.reload(translate_to_vis)
import pandas as pd


#set main paths
CUR_DIR = os.path.dirname(os.path.abspath(__name__))
DATA_DIR = CUR_DIR+'/data/'
DATA_DIR_HUMAN = DATA_DIR+'/human_annotation/'


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


output_filename = filename.split('.json')[0]+'_'+str(scenario_id)

#load human annotation data
this_human_filename = DATA_DIR_HUMAN+output_filename+'_choice_'+str(act_id)+'_value_scores.csv'
all_human_data= {}
if os.path.exists(this_human_filename):
    #load csv file
        this_human_data = pd.read_csv(this_human_filename)
        #use value_names as keys and mean as values and make a dictionary
        all_human_data['value_scores']= this_human_data.set_index('value_names')['mean'].to_dict()

        all_human_data['values_missing']= this_human_data['values_missing'][0]
else:
    print('No human annotation data found for this scenario and action choice.')
        

# run the annotation process -- or just jump into that code for interactive mode
json_filename = annotate_scenario.main(scenario_json,output_filename,act_id,all_human_data)  

translate_to_vis.main(json_filename)
