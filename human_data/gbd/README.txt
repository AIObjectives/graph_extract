"Disability weights for the Global Burden of Disease 2013 study" (Lancet Global Health, 2015).
Salomon, J. A., Haagsma, J. A., Davis, A., Maertens de Noordhout, C., Polinder, S.,
Havelaar, A. H., Cassini, A., Devleesschauwer, B., Kretzschmar, M., Speybroeck, N.,
Murray, C. J. L., & Vos, T.

<<<<<<< HEAD
gbd2013_appendix.pdf: the paper's open supplementary appendix (mmc1), 203 health states
across all domains with disability weights (0 = full health, 1 = death-equivalent) from
paired-comparison surveys, plus lay descriptions of each state.

gbd2013_clean.csv: parsed from the appendix by gbd2013_parse.py (health_state,
lay_description, weight, text_source). Re-run gbd2013_parse.py to regenerate it
(requires poppler's `pdftotext` on PATH).
=======
gbd2013_appendix.pdf: the paper's open supplementary appendix (mmc1), 235 health states
across all domains with disability weights (0 = full health, 1 = death-equivalent) from
paired-comparison surveys, plus lay descriptions of each state. Weights live in Appendix
Tables 2a (135 states), 2b (50), 3 (30 states with revised descriptions) and 4 (20 new).

gbd2013_clean.csv: parsed from the appendix by gbd2013_parse.py (health_state,
lay_description, weight, text_source). Re-run gbd2013_parse.py to regenerate it
(requires poppler's `pdftotext` on PATH). Currently recovers 233 of the 235 states;
the 2 missed are rows whose health-state name wraps in a way the name/description
split can't resolve. text_source records what the lay_description column holds:
"desc" = the lay description from Table 1 (200 states), "inline" = the description
rendered alongside the weight in Table 4 (11), "name" = no description matched, so the
health-state name is used instead (22) - note these are clinical labels rather than the
functional lay wording, so treat them differently if embedding this set.
>>>>>>> v4
