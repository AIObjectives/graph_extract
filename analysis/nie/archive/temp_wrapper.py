import json
import os
import textwrap
import pandas as pd
import importlib
import numpy as np
import src.annotate_scenario as annotate_scenario
import src.prompts as prompts
import src.translate_to_vis as translate_to_vis
import src.node as node
import src.get_emb_distances as get_emb_distances
import src.utils as utils
from pathlib import Path
importlib.reload(annotate_scenario)
importlib.reload(translate_to_vis)

#set main paths
CUR_DIR = Path().resolve()
print(f"current_path: {CUR_DIR}")
SCENARIO_DIR = CUR_DIR / "scenarios_inputs" / "nie" 
DATA_DIR_HUMAN = CUR_DIR / "data" / "human_annotation"
OUTPUT_DIR = CUR_DIR / "annotated_outputs"

#set scenario file filename
FILENAME = 'nie_scenarios.json'

sids = [61]
for sid in sids:
    SCENARIO_ID = sid
    for aid in ['1', '2']:
        ACT_ID = aid

        #read in the scenario
        scenario_json = utils.open_scenario(SCENARIO_DIR, FILENAME, SCENARIO_ID, ACT_ID)

        # get the action choice and convert to two pronoun options (I and Ziv)
        this_act = scenario_json['options'][ACT_ID]
        this_act_I = "I decide to " + this_act
        this_act_Ziv = annotate_scenario.prompts.convert_I_Ziv(this_act_I)
        print('\n\nAction choice:') 
        print(this_act_Ziv)
        print(this_act_I)

        #get the scenario and convert to two pronoun options
        this_scenario = scenario_json['text']
        this_scenario_Ziv = annotate_scenario.prompts.convert_I_Ziv(this_scenario)
        print("\n\nScenario:")
        print(this_scenario_Ziv)
        print(this_scenario)

        # create a dictionary to write out to csv later
        scenario_dict = {'scenario': this_scenario, 'scenario_idx': scenario_json['id'],
                            'choice': this_act_I}

        #initialize Graph object    
        g = annotate_scenario.node.Graph()
        g.reset()   
        print('Graph g initialized and reset.')

        #Step 0. Get entities
        # identify all sentient beings, returning both pronoun forms and a string list
        returned_beings = annotate_scenario.process_beings(this_scenario,this_act,g)
        beings_I = returned_beings[0]
        beings_Ziv = returned_beings[1]
        beings_str_list = returned_beings[2]

        #update the scenario dict with the beings
        scenario_dict["entities"] = beings_str_list

        #Step 1.  #ACTION VALUE SCORES
        #call the process_values function to rate the moral goodness or wrongness of the action with no context
        processed_values  = annotate_scenario.process_value_simple(this_act,this_act_I,g) 
        print(processed_values)

        #Step 2. Outcomes
        processed_events = annotate_scenario.process_outcomes(this_scenario, this_act)
        events_I= processed_events[1]
        events_Ziv= processed_events[0]
        print("\n".join(events_I))         
        scenario_dict["outcomes"]= events_I

        #Step 3. Outcome utilities
        impacts_list = annotate_scenario.process_impacts(this_scenario_Ziv, this_act, this_act_Ziv, events_Ziv, events_I, beings_Ziv, g) 

        #Step 4. causal / intentional / knowledge links -- run on currently generated event/outcome list
        output_links = annotate_scenario.process_causal_links(this_scenario_Ziv, events_Ziv, events_I, this_act_Ziv,g)    

        #optional -- write out the results 
        this_output_filename = f"nie_scenarios_{scenario_json['id']}_choice_{ACT_ID}.json"
        print('\n\nWriting to file: '+this_output_filename)
        g_print = g.print_graph()
        utils.write_jsonlines(this_output_filename, g_print)
        print('\n\n')
        translate_to_vis.main(this_output_filename)

        # Move to annotated_outputs folder
        source = CUR_DIR / this_output_filename
        destination = OUTPUT_DIR / this_output_filename
        source.rename(destination)
        other_output_filename = f"nie_scenarios_{scenario_json['id']}_choice_{ACT_ID}.html"
        source2 = CUR_DIR / other_output_filename
        destination2 = OUTPUT_DIR / other_output_filename
        source2.rename(destination2)


