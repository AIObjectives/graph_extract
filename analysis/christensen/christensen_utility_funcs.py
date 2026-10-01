"""Shared data-loading/reshaping helpers for the christensen analysis notebooks.

Unlike franken, christensen has a single flat input scenarios file and a single flat annotated
outputs folder (no per-condition nesting) -- the four classification dimensions (evitability,
personal_force, intentionality, beneficial_to) are literal columns on each scenario, not derived
from folder/file names. We always use choice_1 (the harmful/instrumental action) per scenario;
choice_2 outputs exist too but are intentionally not used in this analysis.

All plotting lives in src/generic_analysis_utils.py -- this module only builds dataframes.
"""

from pathlib import Path
import pandas as pd
import numpy as np

import src.generic_analysis_utils as generic_analysis_utils

STATIC_SCENARIO_COLUMNS = ["scenario_title", "evitability", "personal_force", "intentionality", "beneficial_to"]


def read_all_christensen_scenarios(inputs_json, outputs_dir, choice="1"):
    """Reads every choice_<choice> annotated christensen scenario into one event-level dataframe.

    Args:
    inputs_json: path to christensen_first_person_all_titled.json
    outputs_dir: path to the flat annotated_outputs/christensen/ folder
    choice: which option's annotated output to read ("1" or "2"); defaults to "1"
    Returns:
    pd.DataFrame with one row per (SID, event): columns SID, option, event, C, I, K, utility (dict
    of being -> numeric utility for that event), deontic, plus the STATIC_SCENARIO_COLUMNS.
    """
    rows = []
    for output_file in sorted(Path(outputs_dir).glob(f"*_choice_{choice}.json")):
        sid = generic_analysis_utils.parse_filename_nie(str(output_file))
        scenario_inputs = generic_analysis_utils.read_input_scenario(inputs_json, sid)
        nodes = generic_analysis_utils.read_annotation(output_file)

        cik_df = generic_analysis_utils.get_cik_links(nodes)
        util_df = generic_analysis_utils.events_to_utility_df(nodes)
        deontic = generic_analysis_utils.extract_deontology(nodes)

        for _, cik_row in cik_df.iterrows():
            event = cik_row["event"]
            utility = util_df.loc[event].to_dict() if event in util_df.index else {}
            row = {
                "SID": sid,
                "option": choice,
                "event": event,
                "C": cik_row["C"],
                "I": cik_row["I"],
                "K": cik_row["K"],
                "utility": utility,
                "deontic": deontic,
            }
            for col in STATIC_SCENARIO_COLUMNS:
                row[col] = scenario_inputs.get(col)
            rows.append(row)

    return pd.DataFrame(rows)


def filter_utility_dict_by_strategy(utility_dict, strategy):
    """Picks which beings' utility values count towards a pooled scenario-level utility score.

    "non_i_only": everyone except the agent "i" -- i.e. impact on patients/bystanders. This is the
    default for christensen since the analyses care about harm inflicted on others, not on self.
    "i_only": just the agent "i". "simplest": everyone, undifferentiated.
    """
    if strategy == "simplest":
        return utility_dict
    elif strategy == "i_only":
        return {k: v for k, v in utility_dict.items() if k == "i"}
    elif strategy == "non_i_only":
        return {k: v for k, v in utility_dict.items() if k != "i"}
    else:
        raise ValueError(f'Unknown strategy {strategy!r} -- must be "simplest", "i_only", or "non_i_only"')


def per_scenario_utility_score(event_df, agg_func=min, strategy="i_only"):
    """Pools every (event, being) utility value selected by `strategy` across a scenario's events
    into one flat list, then reduces it to a single number with agg_func.

    Returns a Series indexed by SID.
    """
    def reduce_group(utility_dicts):
        pooled = []
        for utility_dict in utility_dicts:
            utility_dict = {k: float(v) for k, v in utility_dict.items()}
            pooled.extend(filter_utility_dict_by_strategy(utility_dict, strategy).values())
        return agg_func(pooled) if pooled else float("nan")

    return event_df.groupby("SID")["utility"].agg(reduce_group)


def is_patient_harm_event(utility_dict):
    """True if this event is negative-utility for at least one non-'i' (patient/bystander) being."""
    non_i_vals = [float(v) for k, v in utility_dict.items() if k != "i"]
    return any(v < 0 for v in non_i_vals)


def pct_plus_per_scenario(event_df, column, restrict_to_harm_events=False):
    """Per-scenario % of '+' events for `column` (one of "C", "I", "K").

    restrict_to_harm_events=True restricts to events that are negative-utility for the patient
    (see is_patient_harm_event) before computing the percentage -- e.g. for asking whether the
    annotator marks I+ specifically on the events that actually harm someone.

    Returns a Series indexed by SID, in percent (0-100).
    """
    df = event_df
    if restrict_to_harm_events:
        df = df[df["utility"].apply(is_patient_harm_event)]
    return df.groupby("SID")[column].apply(lambda s: (s == "+").mean() * 100)


# Every (strategy, agg_func) combination worth comparing side by side. Keyed by the suffix used to
# name its column ("utility_score_<name>"). "non_i_only_min" is the original default (worst-case
# impact on the patient/bystander) and is also aliased to the bare "utility_score" column below for
# backward compatibility with analyses that don't care which variant they're using (e.g. 4-5).
DEFAULT_UTILITY_VARIANTS = {
    "non_i_only_min": ("non_i_only", min),
    # "non_i_only_mean": ("non_i_only", np.mean),
    "simplest_min": ("simplest", min),
    # "simplest_mean": ("simplest", np.mean),
    "i_only_min": ("i_only", min),
    # "i_only_mean": ("i_only", np.mean),
}


def build_scenario_level_df(event_df, human_ratings_df=None, utility_variants=None):
    """Collapses the event-level dataframe down to one row per scenario (SID), with:
    - the static scenario columns (scenario_title, evitability, personal_force, intentionality, beneficial_to)
    - deontic (constant per scenario)
    - one utility_score_<name> column per entry in `utility_variants` (defaults to
      DEFAULT_UTILITY_VARIANTS), each computed by per_scenario_utility_score(event_df, agg_func, strategy)
    - utility_score: alias for utility_score_non_i_only_min, the original single-variant default
    - pct_C_plus, pct_I_plus: pct_plus_per_scenario for the full scenario
    - pct_I_plus_harm_only: pct_plus_per_scenario for "I", restricted to patient-harm events

    If human_ratings_df is given (columns must include "id" plus rating columns, e.g.
    arousal_mean/sd, valence_mean/sd, moral_judgment_mean/sd), it is left-merged in on SID == id.
    """
    utility_variants = utility_variants if utility_variants is not None else DEFAULT_UTILITY_VARIANTS

    static_df = event_df.groupby("SID")[STATIC_SCENARIO_COLUMNS + ["deontic"]].first()

    scenario_df = static_df.copy()
    for variant_name, (strategy, agg_func) in utility_variants.items():
        scenario_df[f"utility_score_{variant_name}"] = per_scenario_utility_score(event_df, agg_func, strategy)
    if "utility_score_non_i_only_min" in scenario_df.columns:
        scenario_df["utility_score"] = scenario_df["utility_score_non_i_only_min"]
    scenario_df["pct_C_plus"] = pct_plus_per_scenario(event_df, "C")
    scenario_df["pct_I_plus"] = pct_plus_per_scenario(event_df, "I")
    scenario_df["pct_I_plus_harm_only"] = pct_plus_per_scenario(event_df, "I", restrict_to_harm_events=True)
    scenario_df = scenario_df.reset_index()

    if human_ratings_df is not None:
        scenario_df = scenario_df.merge(human_ratings_df, left_on="SID", right_on="id", how="left").drop(columns=["id"])

    return scenario_df
