"""Shared plotting/stats helpers for analysis_top_level.ipynb (Franken analyses 1-6).

Import with `from analysis_ntbk_helpers import *` to bring these into a notebook's namespace, and
also `import analysis_ntbk_helpers` (module form) if you need to override UTILITY_PICK_STRATEGY --
see that variable's docstring below for why the module form is required for that specifically.
"""

import numpy as np
import matplotlib.pyplot as plt
import pprint
from scipy.stats import ttest_rel, ttest_ind, pointbiserialr


def sig_stars(p):
    """Turns a p-value into significance stars ("***" / "**" / "*" / "ns")."""
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    return "ns"


def bar_dot_sem(ax, groups, colors=None):
    """Bar (mean) + SEM error bars + jittered individual points, for unpaired group comparisons.

    groups: dict label -> array-like of numeric values. Draws bar (mean) + SEM error bars + jittered individual points.
    """
    labels = list(groups.keys())
    if colors is None:
        colors = ["cornflowerblue", "indianred"][:len(labels)]
    means = [np.mean(groups[l]) for l in labels]
    sems  = [np.std(groups[l], ddof=1) / np.sqrt(len(groups[l])) for l in labels]
    ns    = [len(groups[l]) for l in labels]

    x = np.arange(len(labels))
    ax.bar(x, means, yerr=sems, capsize=6, color=colors, error_kw=dict(elinewidth=1.5), zorder=2)

    rng = np.random.default_rng(0)
    for xi, l in zip(x, labels):
        vals = np.asarray(groups[l], dtype=float)
        jitter = rng.uniform(-0.15, 0.15, size=len(vals))
        ax.scatter(xi + jitter, vals, color="black", alpha=0.4, s=14, zorder=3)

    ax.set_xticks(x)
    ax.set_xticklabels([f"{l}\n(n={n})" for l, n in zip(labels, ns)])
    return means, sems, ns


def paired_bar_dot_sem(ax, vals_a, vals_b, label_a="A", label_b="B", colors=None):
    """Same as bar_dot_sem, but for paired/matched data: draws a thin connecting line between each
    matched pair of points (e.g. the same scenario's CC vs COC value).

    vals_a, vals_b: aligned arrays (same length, same order = same underlying scenario).
    Draws bar (mean) + SEM error bars per group, jittered dots, and a line connecting each matched pair.
    """
    vals_a = np.asarray(vals_a, dtype=float)
    vals_b = np.asarray(vals_b, dtype=float)
    n = len(vals_a)
    if colors is None:
        colors = ["pink", "turquoise"]

    means = [vals_a.mean(), vals_b.mean()]
    sems  = [vals_a.std(ddof=1) / np.sqrt(n), vals_b.std(ddof=1) / np.sqrt(n)]

    x = np.array([0, 1])
    ax.bar(x, means, yerr=sems, capsize=6, color=colors, error_kw=dict(elinewidth=1.5), zorder=2)

    rng = np.random.default_rng(0)
    jitter = rng.uniform(-0.15, 0.15, size=n)
    for i in range(n):
        ax.plot([jitter[i], 1 + jitter[i]], [vals_a[i], vals_b[i]], color="gray", alpha=0.3, lw=0.8, zorder=1)
    ax.scatter(jitter, vals_a, color="black", alpha=0.5, s=14, zorder=3)
    ax.scatter(1 + jitter, vals_b, color="black", alpha=0.5, s=14, zorder=3)

    ax.set_xticks(x)
    ax.set_xticklabels([f"{label_a}\n(n={n})", f"{label_b}\n(n={n})"])
    return means, sems, n


def per_scenario_proportion(df, causal_condition, column):
    """Collapses an event-level +/- column down to one proportion per scenario (per SID), so that
    scenario -- not event -- is the unit of analysis.

    Returns a Series indexed by SID: proportion of '+' events for this causal_condition (one value per scenario).
    """
    sub = df[df["causal_condition"] == causal_condition]
    return sub.groupby("SID")[column].apply(lambda s: (s == "+").mean())


def paired_proportion_barplots(df, title_suffix, column, condition_pairs, pair_labels, colors, suptitle):
    """Builds the standard 4-sub-condition + overall 5-panel proportion comparison (used by Analyses 1A, 2, 3),
    each panel a paired t-test.

    condition_pairs: list of (cond_a, cond_b, panel_title). pair_labels: (label_a, label_b).
    Computes per-scenario proportion of '+' in `column`, pairs cond_a vs cond_b by SID within each
    condition-pair, and paired-t-tests each pair plus an overall pooled paired test.
    """
    label_a, label_b = pair_labels
    fig, axs = plt.subplots(1, 5, figsize=(32, 7))

    panel_vals = []
    all_vals_a, all_vals_b = [], []
    for cond_a, cond_b, panel_title in condition_pairs:
        prop_a = per_scenario_proportion(df, cond_a, column)
        prop_b = per_scenario_proportion(df, cond_b, column)
        common_sids = sorted(set(prop_a.index) & set(prop_b.index))
        vals_a = prop_a.loc[common_sids].values * 100
        vals_b = prop_b.loc[common_sids].values * 100
        panel_vals.append((vals_a, vals_b, panel_title))
        all_vals_a.extend(vals_a)
        all_vals_b.extend(vals_b)
    panel_vals.append((np.array(all_vals_a), np.array(all_vals_b), "Overall across all causal conditions"))

    for ax, (vals_a, vals_b, panel_title) in zip(axs, panel_vals):
        p_val = ttest_rel(vals_a, vals_b).pvalue
        means, sems, n = paired_bar_dot_sem(ax, vals_a, vals_b, label_a, label_b, colors=colors)
        y_top = max(m + s for m, s in zip(means, sems)) + 4
        ax.plot([0, 0, 1, 1], [y_top, y_top + 2, y_top + 2, y_top], lw=1.2, c="black")
        ax.text(0.5, y_top + 3, f"{sig_stars(p_val)}\np={p_val:.3f}", ha="center", va="bottom", fontsize=14)
        ax.set_ylim(0, 115)
        ax.set_ylabel(f"% '+' for '{column}' per scenario (mean ± SEM)")
        ax.yaxis.label.set_size(14)
        ax.set_title(panel_title, fontsize=18)

    plt.suptitle(suptitle, fontsize=22)
    plt.tight_layout(rect=[0, 0, 1, 0.98])
    plt.show()


# Which entities count towards a scenario's pooled utility value -- "simplest" (everyone: the agent
# "i" and every other identified entity), "i_only" (just the agent "i"), or "non_i_only" (everyone
# except "i", i.e. all patients/bystanders, undifferentiated). Used by _reduce_to_per_scenario
# (Analysis 4 in the notebook).
#
# To override this from the notebook, set it on the module itself (not as a bare notebook-local
# name) -- _reduce_to_per_scenario reads the module's own global, so a bare
# `UTILITY_PICK_STRATEGY = "i_only"` in the notebook (even after `from analysis_ntbk_helpers import
# *`) would just shadow it locally and have no effect. Instead do:
#     import analysis_ntbk_helpers
#     analysis_ntbk_helpers.UTILITY_PICK_STRATEGY = "i_only"
UTILITY_PICK_STRATEGY = "simplest"


def _filter_utility_dict_by_strategy(utility_dict, strategy):
    if strategy == "simplest":
        return utility_dict
    elif strategy == "i_only":
        return {k: v for k, v in utility_dict.items() if k == "i"}
    elif strategy == "non_i_only":
        return {k: v for k, v in utility_dict.items() if k != "i"}
    else:
        raise ValueError(f'Unknown strategy {strategy!r} -- must be "simplest", "i_only", or "non_i_only"')


def _reduce_to_per_scenario(df, agg_func, strategy=None):
    """Reduces each scenario down to one independent utility observation.

    For every event in a scenario, keeps the utility value of every entity selected by
    UTILITY_PICK_STRATEGY (or `strategy` if passed explicitly), pools all of those values --
    across every entity AND every event of the scenario -- into one flat list, then reduces that
    flat pool to a single number with `agg_func` (e.g. the builtins `min`/`max`, or `np.mean`).

    Entities are never treated specially relative to each other or to other events within the same
    strategy -- once `simplest`/`i_only`/`non_i_only` picks which entities count, every one of
    their per-event values is just one more sample in the pool `agg_func` reduces over. Note
    `min(pool)`/`max(pool)` of the flat pool are exactly equivalent to the old nested
    per-event-then-per-scenario min/max, so this is a pure simplification for those two -- but for
    `agg_func=np.mean`, pooling first (rather than averaging each event's already-reduced extreme)
    is what makes it a true "average across everything considered," not an average of extremes.
    """
    strategy = strategy if strategy is not None else UTILITY_PICK_STRATEGY

    def reduce_group(utility_dicts):
        pooled = []
        for utility_dict in utility_dicts:
            utility_dict = {k: float(v) for k, v in utility_dict.items()}
            pooled.extend(_filter_utility_dict_by_strategy(utility_dict, strategy).values())
        return agg_func(pooled) if pooled else float("nan")

    return df.groupby([df["SID"], df["causal_condition"], df["intensity"]])["utility"].agg(reduce_group)


def create_utility_bar_dot_plots(df, title_suffix, agg_func, ylabel):
    """The 8-causal-condition + overall mild-vs-severe utility comparison grid (used by Analysis 4).

    agg_func: how a scenario's pooled utility values (see _reduce_to_per_scenario) are reduced to
    one value per scenario, so mild vs severe are compared at the scenario level (not event level,
    which would treat a scenario's several events as independent observations when they aren't).
    """
    scenario_vals = _reduce_to_per_scenario(df, agg_func)

    # make 3 rows of plots, 4 plots in the first two rows and 1 overall plot in the third row
    fig, axs = plt.subplots(3, 4, figsize=(36, 19))
    axs = axs.flatten()
    causal_conditions = ["cc_evitable_action_yes_stories", "cc_evitable_prevention_no_stories", "cc_inevitable_action_yes_stories", "cc_inevitable_prevention_no_stories", "coc_evitable_action_yes_stories", "coc_evitable_prevention_no_stories", "coc_inevitable_action_yes_stories", "coc_inevitable_prevention_no_stories"]
    for i, causal_condition in enumerate(causal_conditions):
        mild_data = scenario_vals.xs((causal_condition, "mild_harm_mild_good"), level=["causal_condition", "intensity"]).dropna()
        severe_data = scenario_vals.xs((causal_condition, "severe_harm_very_good"), level=["causal_condition", "intensity"]).dropna()
        bar_dot_sem(axs[i], {"Mild": mild_data, "Severe": severe_data})
        axs[i].tick_params(axis='x', labelsize=16)
        axs[i].set_title(f"{causal_condition} {title_suffix}", fontsize=20)
        axs[i].set_ylabel(ylabel, fontsize=16)
        axs[i].tick_params(axis='y', labelsize=16)
    overall_mild_data = scenario_vals.xs("mild_harm_mild_good", level="intensity").dropna()
    overall_severe_data = scenario_vals.xs("severe_harm_very_good", level="intensity").dropna()
    bar_dot_sem(axs[8], {"Mild": overall_mild_data, "Severe": overall_severe_data})
    axs[8].set_title("Overall Mild vs Severe", fontsize=20)
    axs[8].set_ylabel(ylabel, fontsize=16)
    axs[8].tick_params(axis='y', labelsize=16)
    axs[8].tick_params(axis='x', labelsize=16)

    plt.tight_layout()
    plt.show()


def perform_t_tests(df, agg_func, alternative):
    """Runs the mild-vs-severe one-sided t-test per causal condition + overall (used by Analysis 4).

    alternative='less' tests severe < mild (harm side); alternative='greater' tests severe > mild (good side).
    agg_func: same per-scenario reduction as create_utility_bar_dot_plots -- each scenario
    contributes exactly one observation to the test, rather than one per event.
    """
    causal_conditions = ["cc_evitable_action_yes_stories", "cc_evitable_prevention_no_stories", "cc_inevitable_action_yes_stories", "cc_inevitable_prevention_no_stories", "coc_evitable_action_yes_stories", "coc_evitable_prevention_no_stories", "coc_inevitable_action_yes_stories", "coc_inevitable_prevention_no_stories"]
    results = {}
    scenario_vals = _reduce_to_per_scenario(df, agg_func)

    for causal_condition in causal_conditions:
        mild_data = scenario_vals.xs((causal_condition, "mild_harm_mild_good"), level=["causal_condition", "intensity"]).dropna()
        severe_data = scenario_vals.xs((causal_condition, "severe_harm_very_good"), level=["causal_condition", "intensity"]).dropna()
        t_stat, p_value = ttest_ind(severe_data, mild_data, alternative=alternative)
        results[causal_condition] = {"t_stat": t_stat, "p_value": p_value}

    overall_mild_data = scenario_vals.xs("mild_harm_mild_good", level="intensity").dropna()
    overall_severe_data = scenario_vals.xs("severe_harm_very_good", level="intensity").dropna()
    t_stat, p_value = ttest_ind(overall_severe_data, overall_mild_data, alternative=alternative)
    results["overall"] = {"t_stat": t_stat, "p_value": p_value}
    return results


def intentionality_by_I_label_plot(df, suptitle, print_label):
    """Builds the standard 7-subgroup (CC/COC/Action/Prevention/Evitable/Inevitable/Overall) I+/I-
    vs avg_intention_rating bar+dot+SEM comparison, with the point-biserial r/p annotated on every
    panel (used by Analysis 5A).

    df must have columns: I_binary (0/1), I_label ('I+'/'I-'), avg_intention_rating, causal_condition.
    Prints + returns the per-group correlation results dict.
    """
    groups = {
        "CC": df[df["causal_condition"].str.startswith("cc")],
        "COC": df[df["causal_condition"].str.startswith("coc")],
        "Action (Commission)": df[df["causal_condition"].str.contains("action_yes")],
        "Prevention (Omission)": df[df["causal_condition"].str.contains("prevention_no")],
        "Evitable": df[df["causal_condition"].str.contains("_evitable_")],
        "Inevitable": df[df["causal_condition"].str.contains("_inevitable_")],
        "Overall": df,
    }

    correlation_results = {}
    fig, axs = plt.subplots(1, 7, figsize=(28, 6.5), sharey=True)
    for ax, (group_name, group_df) in zip(axs, groups.items()):
        group_df = group_df.dropna(subset=["avg_intention_rating"]).copy()
        n_iplus = int(group_df["I_binary"].sum())

        if group_df["I_binary"].nunique() < 2:
            r_pb, p_pb = float("nan"), float("nan")
        else:
            r_pb, p_pb = pointbiserialr(group_df["I_binary"], group_df["avg_intention_rating"])

        correlation_results[group_name] = {
            "r_I_intention (point-biserial)": float(r_pb) if not np.isnan(r_pb) else "NaN",
            "p_I_intention": float(p_pb) if not np.isnan(p_pb) else "NaN",
            "n_scenarios": len(group_df),
            "n_I+": n_iplus,
        }

        # I+ and I- are two independent groups here (a scenario belongs to exactly one, never both --
        # unlike the CC vs COC comparisons elsewhere, which really are the same scenario measured twice),
        # so this is an unpaired comparison: bar_dot_sem (not paired_bar_dot_sem), no connecting lines.
        iplus_vals  = group_df[group_df["I_label"] == "I+"]["avg_intention_rating"]
        iminus_vals = group_df[group_df["I_label"] == "I-"]["avg_intention_rating"]
        means, sems, _ = bar_dot_sem(ax, {"I+": iplus_vals, "I-": iminus_vals}, colors=["lightcoral", "lightsteelblue"])

        r_text = f"r={r_pb:.2f}" if not np.isnan(r_pb) else "r=NaN"
        ax.set_title(f"{group_name} (n={len(group_df)}, I+={n_iplus})  {r_text}", fontsize=12)
        ax.set_xlabel("")
        ax.set_ylabel("Avg Human Intention Rating (mean ± SEM)" if ax is axs[0] else "")
        ax.set_ylim(0, 5.9)
        ax.tick_params(axis='x', labelsize=13)

        # significance bracket, matching the visual convention used everywhere else in the notebook.
        # a bar's SEM is undefined (NaN) for a group of size 1 (e.g. a subgroup with only 1 I+ scenario),
        # so use nanmax to fall back on whichever bar has a defined SEM.
        if not np.isnan(p_pb):
            y_top = np.nanmax([m + s for m, s in zip(means, sems)])
            ax.plot([0, 0, 1, 1], [y_top + 0.2, y_top + 0.3, y_top + 0.3, y_top + 0.2], lw=1.2, c="black")
            ax.text(0.5, y_top + 0.35, f"{sig_stars(p_pb)}\np={p_pb:.3f}", ha="center", va="bottom", fontsize=12)

    plt.suptitle(suptitle, fontsize=16)
    plt.tight_layout()
    plt.show()

    print(f"Correlation results — {print_label}:")
    pprint.pprint(correlation_results)
    return correlation_results
