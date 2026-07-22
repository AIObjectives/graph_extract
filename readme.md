
## <b>Graph Extract</b>

This package offers an LLM-based tool to automatically extract meanintful structure in a text scenario with an action choice. Inputs are a text scenario and any number of action choices, entereed as a json. The output is a js/html visualization and associated json object that identifies the entities, actions, events, and relations among them within the scenario. This serves as an input to structured downstream reasoning. See examples in data/. 


## <i> Set-up </i>

`conda_setup.sh` will run all initialization commands and create a conda environment. 

Alternatively, use `environment.yml` to load in the required python dependencies. This skips visualization package installs but allows most functionality.

You must create a .env file in the root directory containing an openAI API Key:

OPENAI_API_KEY='Bearer sk-...'


## <i> Repo Structure </i>

`src`
    contains utility code including core annotation functionality

`analysis`
    contains notbooks for analyzing annotations, with sub-folders for specific sets of scenarios

`annotated_outputs `
    contains annotations produced by the annotator system, with sub-folders for specific sets of scenarios

`human_data`
    contains files from human surveys to compare against annotations; use `annotation_results.ipynb` to explore the annotation data.

`run_annotation`
    contains wrapper code for running an annotation over some set of scenarios and exploration notebooks (with initials for users)

`sceanrios_inputs`
    contains sets of scenarios to be passed into annotation, organized by sub-folders for specific sets

## <i>Creating an Annotation</i>

Start with  `run_annotation\scenarios_exploration_notebook_template.ipynb` for a step by step example of the annotator steps.

When ready to batch process a scenario set, create a jsonlines file conforming to the templates in `scenarios_inputs` under a new folder. The structure is: ``[{"id": 0, "text": <YOUR_SCENARIO>, "options": {"1": <ACTION_CHOICE 1>}}]`` 

Create a config file following `run_annotation/example_config.yml`. Set `commit_hash` to the git commit hash point of the latest change to this repo, and indicating the input scenarios you want to be run as directories. 

You can then call:

`python run_annotation.py example_config.yml`





