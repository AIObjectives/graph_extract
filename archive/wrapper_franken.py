import json
import os
import textwrap 
import typer
# import annotate_scenario
import src.annotate_scenario as annotate_scenario
# import translate_to_vis
import src.translate_to_vis as translate_to_vis
import importlib
importlib.reload(annotate_scenario)
importlib.reload(translate_to_vis)


CUR_DIR = os.path.dirname(os.path.abspath(__name__))
# SEVERITY = 'conditions_mild_harm_mild_good/'  # adjust as needed
SEVERITY = 'conditions_severe_harm_very_good/'  # adjust as needed
SCENARIO_DIR = CUR_DIR+'/formatted_franken_scenarios/data/'+SEVERITY
OUTPUT_DIR = CUR_DIR+'/franken_annotated_outputs_newnewprompts/'+SEVERITY

def main(filename: str = 'scenarios.json', scenario_id: int = 0):

    with open(SCENARIO_DIR+filename, 'r') as file:
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
    output_filepath = OUTPUT_DIR+filename.split('.json')[0]+'/'
    # create output directory if it doesn't exist
    if not os.path.exists(output_filepath):
        os.makedirs(output_filepath)
    output_filename = output_filepath+str(scenario_id)

    for act_id in scenario_json['options'].keys():         
    
        # run the annotation process
        json_filename = annotate_scenario.main(scenario_json,output_filename,act_id)  
        print(f'Annotation saved to {json_filename}\n\n')

        # run the translation to vis process
        translate_to_vis.main(json_filename)

    

if __name__ == "__main__":
    typer.run(main)