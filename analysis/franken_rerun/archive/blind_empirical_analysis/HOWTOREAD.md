This is part of the so-called "blind" analysis where we aren't qualitatively looking at annotator output events, just trying to make inferences using more quantitiative readouts.

I have three types of filters:

1) **Only negative OR both positive and negative utility:** Deciding to discard the individual events that have a positive utility associated with them, since Franken's classifications are only centered around harms.

2) **Choice 1 only OR both choices:** Franken scenarios were originally not a binary choice dilemma, but our annotator requires choice in its input, and all the Franken scenarios easily and naturally convert to binary choices, so I decided to create choice 2 as the opposing action to choice 1 for all original Franken scenarios. We can decide to discard all the annotator outputs generated using all choice 2s for all scenarios.

3) **Skipping OR including invalid graphs for scenarios:** For some Franken scenarios, for either one or both of the choices' outputs, the annotator may generate a graph that contains no "I" being (i.e. a case of missing agent) or no non-I being (i.e. case of missing patient). It is easier to discard these for now than to do specialized analysis, and there are only a few of them, so we can decide to exclude them before making the tally table. It may be the case that for scenario 34 (S34), choice 1 generates an invalid graph (C1) and choice 2 generates a valid graph (C2). This filter would not count S34-C1 but would S34-C2 (of course depending on whether we are counting C2 at all entirely.) 


With these filters, you will see output subfolders that indicate whether or not I used these filters in the following way:

1. `"...{negutilonly / negposutil}..."` -- whether or not we discard the negative-utility events in all the selected graph outputs for the considered scenarios.

2. `"...{choice1only / bothchoices}..."` -- whether or not we are completely discard all graphs generated for the choice 2 for all scenarios (i.e. the binary choice where the agent takes the opposite action than the one in the original Franken scenario).

3. `"...{skipinvalids/ noskipinvalids}..."` -- whether or not we discard all the graph outputs where there was no I-being or no non-I (patient) being.

**Therefore, the analysis done with the most exclusive set of annotator output data would have `"...negutilonly_choice1only_skipinvalids..."` in its subfolder name.**