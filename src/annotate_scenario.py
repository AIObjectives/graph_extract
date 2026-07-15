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
import src.generic_analysis_utils as analysis
importlib.reload(get_emb_distances)
importlib.reload(prompts)
importlib.reload(node)
importlib.reload(utils)
importlib.reload(core_process)
importlib.reload(analysis)


CONFIG = utils.return_config() #environment settings (API, etc)


# scenario json must be a single line with scenario json with entries 'id', 'text', and 'options' {1:, 2: , etc}
def main(scenario_json,output_filename,act_id,commit_hash,write_qualtrics=False,config=None):
   
   #SET-UP STEPS 


    print(config.get("steps_to_keep"))
   # validate the scenario json
    assert isinstance(scenario_json['id'],int)
    assert scenario_json['text']
    assert scenario_json['options']

    this_output_filename = output_filename+'_choice_'+str(act_id)+'.json'

    
    # get the action choice and convert to various pronoun options
    this_act = scenario_json['options'][act_id]
    this_act_I = "I decide to " + this_act
    this_act_Ziv = prompts.convert_I_Ziv(this_act_I)
    print('\n\nProcessing choice '+act_id +', '+this_act) 

    #get the scenario and convert to various pronoun options
    this_scenario = scenario_json['text']
    this_scenario_Ziv = prompts.convert_I_Ziv(this_scenario)

    # create a dictionary for later write-out
    scenario_dict = {'scenario': this_scenario, 'scenario_idx': scenario_json['id'],
                      'choice': this_act_I}
    
    #initialize Graph object    
    g = node.Graph()
    g.reset()       
    g.set_version(commit_hash) 
    g.add_node(node.Node(this_act,'action_choice'))

    #READ IN EXISTING ANNOTATION FILE AS NEEDED 
    if (steps_to_keep := config.get("steps_to_keep")) is not None:
       
      try:
          prior_nodes = analysis.read_annotation(this_output_filename)
          steps_to_keep = config.get("steps_to_keep")
      except FileNotFoundError:
          prior_nodes = []
          steps_to_keep = []
      
    #BEINGS
    # identify all beings

    #if keeping old beings, read them in
    if('beings' in steps_to_keep):

      beings = analysis.extract_beings(prior_nodes)
      beings_fixed_Ziv = [prompts.convert_I_Ziv(b) for b in beings]
      beings_str_list = ",".join(beings)
      g = core_process.add_beings_to_graph(beings,this_act,g)

    #re-generate beings list
    else:
      
      returned_beings = core_process.process_beings(this_scenario,this_act,g)
      beings_fixed_Ziv = returned_beings[1]
      beings_str_list = returned_beings[2]
      g = returned_beings[3]


    #update the scenario dict with the beings and print
    scenario_dict["entities"]= beings_str_list
    print("\nIdentified these entities: \n\n"+"\n".join(beings_fixed_Ziv))

    #ACTION VALUE

    #if keeping old action value, read it in
    if('action_value' in steps_to_keep):
      processed_value = float(analysis.extract_deontology(prior_nodes))
      g = core_process.add_value_node(this_act, processed_value, g)
    #otherwise, re-generate the action value
    else:
      processed_value,g  = core_process.process_values_simple(this_act,g) 
    print("\n\n Deontic value: " + str(processed_value))
    
    ##OUTCOMES
    #if keeping old outcomes, read them in
    if('outcomes' in steps_to_keep):
      processed_events = analysis.extract_outcomes(prior_nodes)
    #otherwise, re-generate the outcomes
    else:
      processed_events = core_process.process_outcomes(this_scenario, this_act)
    
    events_I = processed_events[1]
    events_Ziv = processed_events[0] 
    scenario_dict["outcomes"]= events_I


    ##UTILITIES (no read-in option for now)  
    [impacts_list,impacts_df,g] = core_process.process_impacts(this_scenario_Ziv, 
                                                               this_act, events_Ziv, 
                                                               events_I,beings_fixed_Ziv,g) 

    ##CAUSAL AND INTENTIONAL LINKS (no read-in option for now)
    core_process.process_causal_links(this_scenario_Ziv, events_Ziv, events_I, this_act, g)    

    if(write_qualtrics):
      # #write scenario dict as json for qualtrics output
      this_output_filename_qual = 'qualtrics_'+output_filename+'_choice_'+str(act_id)+'.json'
      utils.write_json(this_output_filename_qual,[scenario_dict])     
            
    
    # # write out json file with the full graph
    print('\n\nWriting to file: '+this_output_filename)
    g_print = g.print_graph()
    utils.write_jsonlines(this_output_filename,g_print)

    print('\n\n')

    return (this_output_filename)




