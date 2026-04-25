#import packages
import os
import sys
import math
import requests
import json, jsonlines
import pandas as pd
import numpy as np
import re
import textwrap
from dotenv import dotenv_values
from dotenv import load_dotenv
import typer
import importlib

# local imports
import src.get_emb_distances as get_emb_distances
import src.prompts as prompts
import src.node as node
import src.utils as utils
import src.core_process as core_process
importlib.reload(get_emb_distances)
importlib.reload(prompts)
importlib.reload(node)
importlib.reload(utils)
importlib.reload(core_process)

CONFIG = utils.return_config()



# scenario json must be a single line with scenario json with entries 'id', 'text', and 'options' {1:, 2: , etc}
def main(scenario_json,output_filename,act_id,commit_hash,write_qualtrics=False):
   
   # validate the scenario json
    assert isinstance(scenario_json['id'],int)
    assert scenario_json['text']
    assert scenario_json['options']

    print('writing to ' +  output_filename)
    
    # get the action choice and convert to various pronoun options
    this_act = scenario_json['options'][act_id]
    this_act_I = "I decide to " + this_act
    this_act_Ziv = prompts.convert_I_Ziv(this_act_I)
    print('\n\nProcessing choice '+act_id +', '+this_act) 

    #get the scenario and convert to various pronoun options
    this_scenario = scenario_json['text']
    this_scenario_Ziv = prompts.convert_I_Ziv(this_scenario)

    # create a dictionary to write out to csv later
    scenario_dict = {'scenario': this_scenario, 'scenario_idx': scenario_json['id'],
                      'choice': this_act_I}
    
    #initialize Graph object    
    g = node.Graph()
    g.reset()       
    g.set_version(commit_hash) 

    #BEINGS
    # identify all sentient beings
    returned_beings = core_process.process_beings(this_scenario,this_act,g)
    # beings_fixed = returned_beings[0]
    beings_fixed_Ziv = returned_beings[1]
    beings_str_list = returned_beings[2]
    g = returned_beings[3]
    #update the scenario dict with the beings
    scenario_dict["entities"]= beings_str_list

    #VALUE SCORES
    processed_value,g  = core_process.process_values_simple(this_act,g) 
    print("\n\n Deontic value: " + str(processed_value))
    
    ##OUTCOMES
    processed_events = core_process.process_outcomes(this_scenario, this_act)
    events_I = processed_events[1]
    events_Ziv = processed_events[0]      
    scenario_dict["outcomes"]= events_I

    ##UTILITIES
    [impacts_list,impacts_df,g] = core_process.process_impacts(this_scenario_Ziv, 
                                                               this_act, events_Ziv, 
                                                               events_I,beings_fixed_Ziv,g) 

    ##CAUSAL AND INTENTIONAL LINKS
    core_process.process_causal_links(this_scenario_Ziv, events_Ziv, events_I, this_act, g)    

    if(write_qualtrics):
      # #write scenario dict as json for qualtrics output
      this_output_filename_qual = 'qualtrics_'+output_filename+'_choice_'+str(act_id)+'.json'
      utils.write_json(this_output_filename_qual,[scenario_dict])     
            
    this_output_filename = output_filename+'_choice_'+str(act_id)+'.json'
    print('\n\nWriting to file: '+this_output_filename)

    # # write out json file with the full graph
    g_print = g.print_graph()
    utils.write_jsonlines(this_output_filename,g_print)

    print('\n\n')

    return (this_output_filename)




