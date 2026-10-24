"""
Survey schema primitives: the shape of the cleaned utility-validation survey
DataFrame and which columns hold which ratings. Shared by aggregation_analysis
and plot_helper so neither module has to depend on the other.

Everything here is read from the column names (char_{c}_utility,
char_{c}_outcome_{o}, outcome_prob_{o}, causal_{k}_outcome_{o}), so it works for
any number of characters and outcomes.
"""

import re
from typing import Dict, List, Optional

import pandas as pd

# causal_1 = narrator knew, causal_2 = narrator intended, causal_3 = narrator caused
CIK_COLUMNS = {"Cause": 3, "Intend": 2, "Know": 1}


def survey_dims(clean: pd.DataFrame) -> Dict[str, int]:
    """Number of characters and outcomes, read from the column names."""
    def count(pattern):
        return sum(bool(re.fullmatch(pattern, col)) for col in clean.columns)
    return {"n_chars": count(r"char_\d+_utility"), "n_outcomes": count(r"outcome_prob_\d+")}


def char_names(clean: pd.DataFrame, char_labels: Optional[List[Optional[str]]] = None) -> List[str]:
    """Display name per character; falls back to 'char_c' where no label is given."""
    n_chars = survey_dims(clean)["n_chars"]
    char_labels = list(char_labels or []) + [None] * n_chars
    return [char_labels[c] or f"char_{c+1}" for c in range(n_chars)]


def cik_ratings(clean: pd.DataFrame, label: str, o: int) -> pd.Series:
    """One rating type's 1-7 agreement ratings for outcome o."""
    return pd.to_numeric(clean[f"causal_{CIK_COLUMNS[label]}_outcome_{o}"], errors="coerce").dropna()
