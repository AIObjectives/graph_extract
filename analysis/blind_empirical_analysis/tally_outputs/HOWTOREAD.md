The output folders in *tally_outputs/* come from ruuning `tally_table_maker.py` using certain different input data-filtering configurations.

This is part of the so-called "blind" analysis where we aren't qualitatively looking at annotor output events, just trying to make inferences using more quantitiative readouts.

I have table-formatted outputs for Franken scenarios that vary across three types of filters:

1) **Only negative OR both positive and negative utility:** Deciding to discard the individual events that have a positive utility associated with them, since Franken's classifications are only centered around harms.

2) **Choice 1 only OR both choices:** Franken scenarios were originaly not a binary choice dilemma, but our annotator requires choice in its input, and all the Franken scenarios easily and naturally convert to binary choices, so I decided to create choice 2 as the opposing action to choice 1 for all original Franken scenarios. We can decide to discard all the annotator outputs generated using all choice 2s for all scenarios.

3) **Skipping OR inclusing invalid graphs for scenarios:** For some Franken scenarios, for either one or both of the choices' outputs, the annotator may generate a graph that contains no "I" being (i.e. a case of missing agent) or no non-I being (i.e. case of missing patient). It is easier to discard these for now than to do specialized analysis, and there are only a few of them, so we can decide to exclude them before making the tally table. It may be the case that for scenario 34 (S34), choice 1 generates an invalid graph (C1) and choice 2 generates a valid graph (C2). This filter would not count S34-C1 but would S34-C2 (of course depending on whether we are counting C2 at all entirely.) 


With this, I generated outputs at three distinct levels of exclusivity:

1. `"table_negutilonly_choice1only_skipmissingagent_skipmissingpatient"` -- **most filtered** -- throw away all the individual events with negative utility in all graphs, throw away all the choice 2 graphs for all scenarios, throw away all the choice 1 graphs that have missing agents or missing patients

2. `"table_negutilonly_choice1only_noskipinvalids"` -- **moderately filtered** -- throw away all the individual events with negative utility in all graphs, throw away all the choice 2 graphs for all scenarios

3. `"table_negutilonly_bothchoices_noskipinvalids"` -- **least filtered** -- throw away all the individual events with negative utility in all graphs

You can run more configurations by running `tally_table_maker.py` with other configurations of the boolean flags at the very top of that script!

