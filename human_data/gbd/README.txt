"Disability weights for the Global Burden of Disease 2013 study" (Lancet Global Health, 2015).
Salomon, J. A., Haagsma, J. A., Davis, A., Maertens de Noordhout, C., Polinder, S.,
Havelaar, A. H., Cassini, A., Devleesschauwer, B., Kretzschmar, M., Speybroeck, N.,
Murray, C. J. L., & Vos, T.

gbd2013_appendix.pdf: the paper's open supplementary appendix (mmc1), 203 health states
across all domains with disability weights (0 = full health, 1 = death-equivalent) from
paired-comparison surveys, plus lay descriptions of each state.

gbd2013_clean.csv: parsed from the appendix by gbd2013_parse.py (health_state,
lay_description, weight, text_source). Re-run gbd2013_parse.py to regenerate it
(requires poppler's `pdftotext` on PATH).
