NOTE: All of these tables came from running the `tally_table_script.py` using different boolean flags (defined at the top of that script).

Please look at the .txt version of the tables for easier readability.

The lines at the top of the .txt file (before the table starts) describe all the filters settings that were used for tallying the data.

*Here are the steps to find which scenario graph output corresponds to any given row in the tally table (you wil find all the original scenario outputs in `annotated_outputs/franken_annotated_outputs/`):*

In the table, go to any row, and:

**Step 1** = Look at the "Severity" column. You will know whether to find the scenario in `conditions_mild_harm_mild_good` or `conditions_severe_harm_very_good` subfolder.

**Step 2** = Look at the "Condition" column. This will tell you the exact sub-subfolder that the scenario belongs to.

**Step 3** = Look at the "Orig ID" column. Match this number with the scenario file name (e.g. `12_choice_1.json` or `12_choice_2.json` has Orig ID = 12).

Done! You now know exactly which scenario output graph corresponds to the row tally result you are looking at.

(Optional) Step 4 = Look at the "Choice" column. It will have either 1 or 2, telling you which choice's graph is being tallied for that scenario in that row that you are looking at.
