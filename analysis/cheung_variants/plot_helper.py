
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import axes


def make_deont_util_plot(scenario_name, plot_df, results_path):

    plot_df = plot_df.copy()

    # Normalize labels so Seaborn order always matches regardless of input dtype
    for col in ["deontology_label", "utility_label"]:
        plot_df[col] = plot_df[col].astype(str).str.strip()

    plot_df["value"] = plot_df["value"].astype(float)

    deontology_order = [
        x for x in ["1", "2", "3"]
        if x in plot_df["deontology_label"].dropna().unique().tolist()
    ]
    utility_order = [
        x for x in ["1", "2", "3"]
        if x in plot_df["utility_label"].dropna().unique().tolist()
    ]

    if not deontology_order:
        deontology_order = sorted(plot_df["deontology_label"].dropna().unique().tolist())
    if not utility_order:
        utility_order = sorted(plot_df["utility_label"].dropna().unique().tolist())


    # Two blue shades for the two measures
    blue_palette = {
        "deontology_rating": "#9ecae1",  # lighter blue
        "utility_diff": "#3182bd",     # darker blue
    }

    sns.set_theme(style="whitegrid", font_scale=1.1)    

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5), sharey=True)

    # Deontology plot
    sns.barplot(
        data=plot_df,
        x="deontology_label",
        y="value",
        hue="measure",
        estimator="mean",
        errorbar="se",
        capsize=0.12,
        palette=blue_palette,
        order=deontology_order,
        ax=axes[0],
    )

    axes[0].set_title(f"Mean Ratings ± SE by Deontology Label ({scenario_name})", pad=12)
    axes[0].set_xlabel("Deontology Category")
    axes[0].set_ylabel("Rating")
    label_map = {"1": "Low", "2": "Medium", "3": "High"}
    axes[0].set_xticklabels([label_map.get(x, x) for x in deontology_order])
    axes[0].grid(axis="y", linestyle="--", alpha=0.3)
    axes[0].set_ylim(-100, 100)

    # Remove legend here so we only show one
    if axes[0].get_legend() is not None:
        axes[0].get_legend().remove()

    # Utility plot
    sns.barplot(
        data=plot_df,
        x="utility_label",
        y="value",
        hue="measure",
        estimator="mean",
        errorbar="se",
        capsize=0.12,
        palette=blue_palette,
        order=utility_order,
        ax=axes[1],
    )

    axes[1].set_title(f"Mean Ratings ± SE by Utility Label ({scenario_name})", pad=12)
    axes[1].set_xlabel("Utility Category")
    axes[1].set_ylabel("")

    axes[1].set_xticklabels([label_map.get(x, x) for x in utility_order])
    axes[1].set_ylim(-100, 100)

    axes[1].grid(axis="y", linestyle="--", alpha=0.3)

# Unified legend
    handles, labels = axes[1].get_legend_handles_labels()
    axes[1].legend(handles, labels, title="Measure", loc="lower right")

    sns.despine()
    plt.tight_layout()
    plt.savefig(results_path / f"{scenario_name}_deont_util_comparison.png", dpi=300)
    plt.show()