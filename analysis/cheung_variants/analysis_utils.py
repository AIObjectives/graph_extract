
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import axes


def make_deont_util_plot(scenario_name, plot_df, results_path):


    # Two blue shades for the two measures
    blue_palette = {
        "deontology_rating": "#9ecae1",  # lighter blue
        "utility_rating": "#3182bd",     # darker blue
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
        order=["1", "2", "3"],
        ax=axes[0],
    )

    axes[0].set_title(f"Mean Ratings ± SE by Deontology Label ({scenario_name})", pad=12)
    axes[0].set_xlabel("Deontology Category")
    axes[0].set_ylabel("Rating")
    axes[0].set_xticklabels(["Low", "Medium", "High"])
    axes[0].grid(axis="y", linestyle="--", alpha=0.3)

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
        order=["1", "2", "3"],
        ax=axes[1],
    )

    axes[1].set_title(f"Mean Ratings ± SE by Utility Label ({scenario_name})", pad=12)
    axes[1].set_xlabel("Utility Category")
    axes[1].set_ylabel("")

    axes[1].set_xticklabels(["Low", "Medium", "High"])
    axes[1].set_ylim(-100, 0)

    axes[1].grid(axis="y", linestyle="--", alpha=0.3)

# Unified legend
    handles, labels = axes[1].get_legend_handles_labels()
    axes[1].legend(handles, labels, title="Measure", loc="lower right")

    sns.despine()
    plt.tight_layout()
    plt.savefig(results_path / f"{scenario_name}_deont_util_comparison.png", dpi=300)