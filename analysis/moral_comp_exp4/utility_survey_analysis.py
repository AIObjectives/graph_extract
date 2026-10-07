"""
Descriptive statistics and utility aggregations for cleaned utility-validation surveys
(the `clean` dataframe produced by clean_utility_survey.clean_survey).

Works for any number of characters and outcomes: both are read from the column names
(char_{c}_utility, char_{c}_outcome_{o}, outcome_prob_{o}, causal_{k}_outcome_{o}).
"""

import re
import textwrap
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator
import numpy as np
import pandas as pd

# causal_1 = narrator knew, causal_2 = narrator intended, causal_3 = narrator caused
CIK_COLUMNS = {"Cause": 3, "Intend": 2, "Know": 1}
CIK_STATEMENTS = {"Cause": "narrator caused the outcome",
                  "Intend": "narrator intended the outcome",
                  "Know": "narrator knew it would happen"}

UTILITY_BINS = np.arange(-100, 101, 10)
LIKERT_BINS = np.arange(0.5, 8.5, 1)   # 1-7 agreement scale, one bar per value

# Chart ink and surface
INK, INK_SECONDARY, GRID, SURFACE = "#0b0b0b", "#52514e", "#e1e0d9", "#ffffff"

# Diverging colors for the 1-7 agreement scale: red (disagree) - gray midpoint - blue (agree)
LIKERT_COLORS = {1: "#b3302f", 2: "#e34948", 3: "#f2a9a8", 4: "#d9d8d2",
                 5: "#9ec5f4", 6: "#3987e5", 7: "#184f95"}
LIKERT_TEXT = {1: "#ffffff", 2: "#ffffff", 3: INK, 4: INK, 5: INK, 6: "#ffffff", 7: "#ffffff"}
LIKERT_LEGEND = {1: "1 (lowest)", 7: "7 (highest)"}


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


def _hist(ax, values, bins, title, xlabel, bold_title=False):
    """
    Histogram of one variable. With bold_title, the panel title is the heading in bold
    with the statistics on a smaller gray line beneath it.
    """
    values = pd.to_numeric(values, errors="coerce").dropna()
    ax.hist(values, bins=bins, edgecolor="black", color="#6A8EAE")
    stats = f"n={len(values)}, mean={values.mean():.1f}"
    if bold_title:
        ax.set_title(textwrap.fill(title, 24), fontsize=12, fontweight="bold", pad=20)
        ax.text(0.5, 1.03, stats, transform=ax.transAxes, ha="center", va="bottom",
                fontsize=9.5, color=INK_SECONDARY)
    else:
        ax.set_title(f"{title}\n({stats})", fontsize=10)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Participants")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))   # whole numbers of participants


# ---- Descriptive statistics ----

def _cik_ratings(clean: pd.DataFrame, label: str, o: int) -> pd.Series:
    """One rating type's 1-7 agreement ratings for outcome o."""
    return pd.to_numeric(clean[f"causal_{CIK_COLUMNS[label]}_outcome_{o}"], errors="coerce").dropna()


def _grid_panel(ax, values, bins) -> None:
    """One histogram of an outcome grid: bars, a dashed line at the mean, and the mean as a small label."""
    ax.hist(values, bins=bins, edgecolor="black", color="#6A8EAE")
    ax.axvline(values.mean(), color=INK, linestyle="--", linewidth=1.5)
    ax.set_title(f"mean {values.mean():.1f}", fontsize=10, loc="right", color=INK_SECONDARY)
    ax.tick_params(labelbottom=True)   # show tick labels on every subplot, not just the bottom row
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))   # whole numbers of participants


def _label_outcome_grid(fig, axes, title: str, n: int,
                        column_headers: Optional[List[str]] = None,
                        column_subheaders: Optional[List[str]] = None,
                        outcome_labels: Optional[List[Optional[str]]] = None,
                        italic_subheaders: bool = True, show_n: bool = True) -> None:
    """
    Shared labeling for grids with one row per outcome: above each column an optional bold
    header (column_headers) and an optional smaller line (column_subheaders, italic unless
    italic_subheaders is False); "Outcome N" plus its description left of each row; and the
    title centered over the plots, with the sample size beneath it unless show_n is False.
    """
    n_rows, n_cols = axes.shape
    outcome_labels = list(outcome_labels or []) + [None] * n_rows
    headers = []   # row/column header texts, placed outside the subplot grid

    # Column labels above the top row: italic line first, bold header above it
    for j in range(n_cols):
        ax = axes[0, j]
        offset = 22
        if column_subheaders:
            headers.append(ax.annotate(column_subheaders[j], xy=(0.5, 1), xycoords="axes fraction",
                                       xytext=(0, offset), textcoords="offset points",
                                       ha="center", va="bottom", fontsize=11,
                                       style="italic" if italic_subheaders else "normal"))
            offset += 16
        if column_headers:
            headers.append(ax.annotate(column_headers[j], xy=(0.5, 1), xycoords="axes fraction",
                                       xytext=(0, offset), textcoords="offset points",
                                       ha="center", va="bottom", fontsize=15, fontweight="bold"))

    # Row headers left of the first column: which outcome each row shows
    for o in range(1, n_rows + 1):
        ax = axes[o - 1, 0]
        headers.append(ax.annotate(f"Outcome {o}", xy=(0, 0.5), xycoords="axes fraction",
                                   xytext=(-150, 30), textcoords="offset points",
                                   ha="center", va="center", fontsize=13, fontweight="bold"))
        if outcome_labels[o - 1]:
            headers.append(ax.annotate(textwrap.fill(outcome_labels[o - 1], 26),
                                       xy=(0, 0.5), xycoords="axes fraction",
                                       xytext=(-150, 16), textcoords="offset points",
                                       ha="center", va="top", fontsize=10, style="italic"))

    # Lay out the subplot grid without the headers (so they don't squeeze the plots),
    # leaving room for the title and column headers (top) and outcome descriptions (left)
    left = 2.6 / fig.get_figwidth()
    top = (1.5 if column_headers else 1.3) - (0 if show_n else 0.35)
    for text in headers:
        text.set_in_layout(False)
    fig.tight_layout(rect=(left, 0, 1, 1 - top / fig.get_figheight()))
    # Count the headers again afterwards, so notebooks don't crop them out of the figure
    for text in headers:
        text.set_in_layout(True)

    # Center the title over the plots rather than over the whole figure
    grid_center = (axes[0, 0].get_position().x0 + axes[0, -1].get_position().x1) / 2
    fig.suptitle(title, fontsize=17, x=grid_center, y=1 - 0.12 / fig.get_figheight(), va="top")
    if show_n:
        fig.text(grid_center, 1 - 0.5 / fig.get_figheight(), f"n = {n} participants",
                 ha="center", va="top", fontsize=13, color=INK_SECONDARY)


def plot_cik(clean: pd.DataFrame, outcome_labels: Optional[List[Optional[str]]] = None) -> plt.Figure:
    """
    CIK links distribution: histograms of the narrator's Cause / Intend / Know ratings.
    One column per rating type (labeled at the top), one row per outcome (labeled on the
    left, with the outcome's description when outcome_labels is given). The dashed line
    marks each panel's mean.
    """
    n_outcomes = survey_dims(clean)["n_outcomes"]
    fig, axes = plt.subplots(n_outcomes, len(CIK_COLUMNS), figsize=(14.5, 2.4 * n_outcomes),
                             sharex=True, sharey=True, squeeze=False)
    for o in range(1, n_outcomes + 1):
        for j, label in enumerate(CIK_COLUMNS):
            ax = axes[o - 1, j]
            _grid_panel(ax, _cik_ratings(clean, label, o), LIKERT_BINS)
            ax.set_xticks(range(1, 8))

            # Axis labels once: under the bottom row and left of the first column
            if o == n_outcomes:
                ax.set_xlabel("Agreement (1 = lowest, 7 = highest)")
            if j == 0:
                ax.set_ylabel("Participants")

    _label_outcome_grid(fig, axes, "Narrator Cause/Intend/Know Ratings", len(clean),
                        column_headers=[label.upper() for label in CIK_COLUMNS],
                        column_subheaders=[CIK_STATEMENTS[label] for label in CIK_COLUMNS],
                        outcome_labels=outcome_labels)
    return fig


def plot_cik_summary(clean: pd.DataFrame,
                     outcome_labels: Optional[List[Optional[str]]] = None) -> plt.Figure:
    """
    Compact view of the CIK links: one panel per rating type, one stacked bar per outcome.
    Each bar shows how many participants gave each agreement rating (1-7), centered on the
    scale midpoint so disagreement extends left and agreement extends right.
    """
    n_outcomes = survey_dims(clean)["n_outcomes"]
    outcome_labels = list(outcome_labels or []) + [None] * n_outcomes
    ratings = list(range(1, 8))
    n = len(clean)

    # Count ratings per (rating type, outcome); the midpoint rating (4) straddles zero
    counts_by = {(label, o): _cik_ratings(clean, label, o).round().astype(int)
                                 .value_counts().reindex(ratings, fill_value=0)
                 for label in CIK_COLUMNS for o in range(1, n_outcomes + 1)}
    disagree_max = max(c[1] + c[2] + c[3] + c[4] / 2 for c in counts_by.values())
    agree_max = max(c[5] + c[6] + c[7] + c[4] / 2 for c in counts_by.values())
    step = 5 if max(disagree_max, agree_max) > 10 else 2

    fig, axes = plt.subplots(1, len(CIK_COLUMNS), figsize=(14.5, 1.0 * n_outcomes + 2.2),
                             sharex=True, sharey=True, squeeze=False)
    for j, label in enumerate(CIK_COLUMNS):
        ax = axes[0, j]
        for o in range(1, n_outcomes + 1):
            values = _cik_ratings(clean, label, o)
            counts = counts_by[(label, o)]
            left = -(counts[1] + counts[2] + counts[3] + counts[4] / 2)
            for rating in ratings:
                if counts[rating] == 0:
                    continue
                ax.barh(o, counts[rating], left=left, height=0.62, color=LIKERT_COLORS[rating],
                        edgecolor=SURFACE, linewidth=2)   # surface-colored gap between segments
                if counts[rating] >= 2:   # label a segment only when the number fits
                    ax.text(left + counts[rating] / 2, o, str(counts[rating]), ha="center",
                            va="center", fontsize=9, color=LIKERT_TEXT[rating])
                left += counts[rating]
            ax.text(agree_max + 0.6, o, f"mean {values.mean():.1f}", ha="left", va="center",
                    fontsize=10, color=INK_SECONDARY)

        ax.axvline(0, color=INK, linewidth=1)
        ax.set_title(f"{label.upper()}\n", fontsize=14, fontweight="bold")
        ax.text(0.5, 1.02, CIK_STATEMENTS[label], transform=ax.transAxes, ha="center",
                va="bottom", fontsize=10.5, style="italic")
        ax.set_xlim(-disagree_max - 0.8, agree_max + 0.25 * (disagree_max + agree_max))
        ticks = [t for t in range(-step * 10, step * 10 + 1, step)
                 if -disagree_max - 0.8 <= t <= agree_max]
        ax.set_xticks(ticks)
        ax.set_xticklabels([str(abs(t)) for t in ticks])
        ax.set_xlabel("Participants   (disagree  <   |   >  agree)")
        ax.xaxis.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.tick_params(axis="y", length=0)

    names = [f"Outcome {o}" + (f"\n{textwrap.fill(outcome_labels[o - 1], 34)}" if outcome_labels[o - 1] else "")
             for o in range(1, n_outcomes + 1)]
    axes[0, 0].set_yticks(range(1, n_outcomes + 1))
    axes[0, 0].set_yticklabels(names, fontsize=10)
    axes[0, 0].invert_yaxis()   # outcome 1 at the top

    legend_handles = [Patch(facecolor=LIKERT_COLORS[r], label=LIKERT_LEGEND.get(r, str(r))) for r in ratings]
    fig.legend(handles=legend_handles, title="Agreement rating", loc="lower center",
               ncol=len(ratings), frameon=False, fontsize=10, title_fontsize=10)
    fig.suptitle(f"Narrator Cause/Intend/Know Ratings (n = {n})", fontsize=15)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    return fig


def plot_overall_utility(clean: pd.DataFrame) -> plt.Figure:
    """Histogram of the overall utility of the action."""
    fig, ax = plt.subplots(figsize=(6, 4))
    _hist(ax, clean["overall_utility"], UTILITY_BINS, "Overall utility of the action", "Utility")
    fig.tight_layout()
    return fig


def plot_char_utilities(clean: pd.DataFrame, char_labels=None) -> plt.Figure:
    """Histograms of each character's utility for the action as a whole (not per outcome)."""
    names = char_names(clean, char_labels)
    fig, axes = plt.subplots(1, len(names), figsize=(3.5 * len(names), 3.5),
                             sharex=True, sharey=True, squeeze=False)
    for c, name in enumerate(names, start=1):
        _hist(axes[0, c - 1], clean[f"char_{c}_utility"], UTILITY_BINS, name, "Utility",
              bold_title=True)
    fig.suptitle("Utility Per Character", fontsize=14)
    fig.tight_layout()
    return fig


def plot_outcome_char_utilities(clean: pd.DataFrame, char_labels=None,
                                outcome_labels: Optional[List[Optional[str]]] = None) -> plt.Figure:
    """
    Histograms of per-outcome, per-character utility, in the same layout as plot_cik:
    one column per character (named at the top), one row per outcome (labeled on the
    left, with the outcome's description when outcome_labels is given). The dashed line
    marks each panel's mean.
    """
    names = char_names(clean, char_labels)
    n_outcomes = survey_dims(clean)["n_outcomes"]
    fig, axes = plt.subplots(n_outcomes, len(names),
                             figsize=(2.6 + 3.4 * len(names), 2.4 * n_outcomes),
                             sharex=True, sharey=True, squeeze=False)
    for o in range(1, n_outcomes + 1):
        for c in range(1, len(names) + 1):
            ax = axes[o - 1, c - 1]
            values = pd.to_numeric(clean[f"char_{c}_outcome_{o}"], errors="coerce").dropna()
            _grid_panel(ax, values, UTILITY_BINS)

            # Axis labels once: under the bottom row and left of the first column
            if o == n_outcomes:
                ax.set_xlabel("Utility (-100 to +100)")
            if c == 1:
                ax.set_ylabel("Participants")

    _label_outcome_grid(fig, axes, "Utility Per Outcome", len(clean),
                        column_subheaders=names, outcome_labels=outcome_labels,
                        italic_subheaders=False, show_n=False)
    return fig


# ---- Utility aggregations ----

def utility_aggregations(clean: pd.DataFrame) -> pd.DataFrame:
    """
    Per-participant sums used to compare utility levels:
        char_{c}_utility       rated utility of the action for character c
        char_{c}_outcome_sum   sum over outcomes of character c's per-outcome utility
        outcome_utility_sum    sum of char_{c}_outcome_sum over all characters
        char_utility_sum       sum of char_{c}_utility over all characters
        overall_utility        rated overall utility of the action
    """
    dims = survey_dims(clean)
    chars = range(1, dims["n_chars"] + 1)
    outcomes = range(1, dims["n_outcomes"] + 1)

    agg = clean[["Subject", "overall_utility"]].copy()
    for c in chars:
        agg[f"char_{c}_utility"] = clean[f"char_{c}_utility"]
        agg[f"char_{c}_outcome_sum"] = clean[[f"char_{c}_outcome_{o}" for o in outcomes]].sum(axis=1)
    agg["outcome_utility_sum"] = agg[[f"char_{c}_outcome_sum" for c in chars]].sum(axis=1)
    agg["char_utility_sum"] = agg[[f"char_{c}_utility" for c in chars]].sum(axis=1)
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
                  "rated": "overall_utility", "summed": "outcome_utility_sum"})
    pairs.append({"comparison": "(c) sum of character utilities vs. overall utility",
                  "title": "(c) all characters",
                  "rated": "overall_utility", "summed": "char_utility_sum"})
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
            "mean_abs_diff": diff.abs().mean(),
            "pearson_r": rated.corr(summed),
            "same_sign_%": 100 * (np.sign(rated) == np.sign(summed)).mean(),
        })
    return pd.DataFrame(rows).round(2)


def plot_aggregations(agg: pd.DataFrame, pairs: List[dict]) -> plt.Figure:
    """Scatter of summed vs. rated utility per participant; dashed line = perfect recovery."""
    n_cols = 3
    n_rows = int(np.ceil(len(pairs) / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4.5 * n_rows), squeeze=False)
    for ax, pair in zip(axes.flat, pairs):
        x, y = agg[pair["rated"]], agg[pair["summed"]]
        ax.scatter(x, y, s=50, edgecolor="black", color="#6A8EAE")
        lims = [min(x.min(), y.min(), -100), max(x.max(), y.max(), 100)]
        ax.plot(lims, lims, "--", color="gray")
        ax.axhline(0, color="lightgray", lw=0.8)
        ax.axvline(0, color="lightgray", lw=0.8)
        ax.set_xlabel(f"Rated: {pair['rated']}")
        ax.set_ylabel(f"Summed: {pair['summed']}")
        ax.set_title(pair["title"], fontsize=11)
    for ax in list(axes.flat)[len(pairs):]:
        ax.axis("off")
    fig.tight_layout()
    return fig
