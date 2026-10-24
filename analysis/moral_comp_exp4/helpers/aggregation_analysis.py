"""
Descriptive statistics and utility aggregations for cleaned utility-validation surveys
(the `clean` dataframe produced by clean_human_survey.clean_survey). The plots built
on these live in plot_helper.

Works for any number of characters and outcomes: both are read from the column names
(char_{c}_utility, char_{c}_outcome_{o}, outcome_prob_{o}, causal_{k}_outcome_{o}).
"""

from typing import List

import pandas as pd

from survey_schema import survey_dims, char_names


# ---- Utility aggregations ----

def utility_aggregations(clean: pd.DataFrame) -> pd.DataFrame:
    """
    Per-participant sums used to compare utility levels:
        char_{c}_utility       rated utility of the action for character c
        char_{c}_outcome_sum   sum over outcomes of character c's per-outcome utility
        sum_outcome_utility    sum of char_{c}_outcome_sum over all characters
        sum_char_utility       sum of char_{c}_utility over all characters
        overall_utility        rated overall utility of the action
    """
    dims = survey_dims(clean)
    chars = range(1, dims["n_chars"] + 1)
    outcomes = range(1, dims["n_outcomes"] + 1)

    agg = clean[["Subject", "overall_utility"]].copy()
    for c in chars:
        agg[f"char_{c}_utility"] = clean[f"char_{c}_utility"]
        agg[f"char_{c}_outcome_sum"] = clean[[f"char_{c}_outcome_{o}" for o in outcomes]].sum(axis=1)
    agg["sum_outcome_utility"] = agg[[f"char_{c}_outcome_sum" for c in chars]].sum(axis=1)
    agg["sum_char_utility"] = agg[[f"char_{c}_utility" for c in chars]].sum(axis=1)
    return agg


def comparison_pairs(clean: pd.DataFrame, char_labels=None) -> List[dict]:
    """The (rated, summed) column pairs to compare, with a readable description."""
    names = char_names(clean, char_labels)
    pairs = [{"comparison": f"(a) {name}: sum over outcomes vs. rated character utility",
              "title": f"(a) {name}",
              "rated": f"char_{c}_utility", "summed": f"char_{c}_outcome_sum"}
             for c, name in enumerate(names, start=1)]
    pairs.append({"comparison": "(b) sum over outcomes and characters vs. overall utility",
                  "title": "(b) all outcomes x characters",
                  "rated": "overall_utility", "summed": "sum_outcome_utility"})
    pairs.append({"comparison": "(c) sum of character utilities vs. overall utility",
                  "title": "(c) all characters",
                  "rated": "overall_utility", "summed": "sum_char_utility"})
    return pairs


def aggregation_summary(agg: pd.DataFrame, pairs: List[dict]) -> pd.DataFrame:
    """How well each summed utility recovers the rated one, across participants."""
    rows = []
    for pair in pairs:
        rated, summed = agg[pair["rated"]], agg[pair["summed"]]
        diff = summed - rated
        rows.append({
            "comparison": pair["comparison"],
            "rated_mean": rated.mean(),
            "summed_mean": summed.mean(),
            "mean_diff (summed - rated)": diff.mean(),
            "pearson_r": rated.corr(summed),
        })
    return pd.DataFrame(rows).round(2)
