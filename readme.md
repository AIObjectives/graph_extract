
## <b>Graph Extract</b>

This package offers an LLM-based tool to automatically extract meanintful structure in a text scenario with an action choice. Inputs are a text scenario and any number of action choices, entereed as a json. The output is a js/html visualization and associated json object that identifies the entities, actions, events, and relations among them within the scenario. This serves as an input to structured downstream reasoning. See examples in data/. 

Use scenarios_wrapper.ipynb to explore the annotator step by step.

## <i>Input Data</i>

Supply a jsonlines file with scenario text and action choice, with structure: ``[{"id": 0, "text": <YOUR_SCENARIO>, "options": {"1": <ACTION_CHOICE 1>}}]`` in the scenarios/ folder.
See scenarios/scenarios.json for an example, or add to this file. Outputs print to the scenarios/ folder.

Human annotation data is under data/human_annotation and exists for a subset of existing scenarios. Use annotation_results.ipynb to explore the annotation data.

## <i>Installation & Use</i>

Clone this repo and install the packages listed in requirements.txt. 

Ensure you have an openAI API key in a .env file in the root directory:
OPENAI_API_KEY='Bearer sk-...'

To run the annotator (outside the notebook context):

python wrapper.py --filename "scenarios.json" --scenario-id <id>

Filename indicates the json file under data/ you wish to use. Scenario-id specifies which scenario you wish to process within the file, which assumes a jsonlines format.

## <i>Output Data</i>

All outputs will be saved to scenarios/ and named with with this format: input-filename_scenario-id_action choice.html, e.g, scenarios_2_choice_1.html. 

Load the html file in a browser to view your visualization, or use the json file in whatever further processing you wish.




