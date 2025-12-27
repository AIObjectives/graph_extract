import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import sys

# Configuration
CSV_FILE = 'tally_outputs/table_negutilonly_choice1only_skipmissingagent_skipmissingpatient/scenario_data_table.csv' # Path to the CSV file
UITLITY_FILTER = 1 if "negutilonly" in CSV_FILE else None # Set to 1 to filter only negative utility rows, or None for all rows
CHOICE_FILTER = 1 if "choice1only" in CSV_FILE else None # Set to 1 to filter only choice=1, or None for all rows
OUTPUT_PLOT = 'frankenviolin_' + ('negutilonly_' if UITLITY_FILTER is not None else '') + ('choice1only' if CHOICE_FILTER is not None else 'bothchoices') + '.png'
OUTPUT_STATS = 'Ttestanalysis-' + ('negutilonly_' if UITLITY_FILTER is not None else '') + ('choice1only' if CHOICE_FILTER is not None else 'bothchoices') + '.txt'


def calculate_cohens_d(group1, group2):
    """Calculate Cohen's d effect size"""
    n1, n2 = len(group1), len(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    pooled_std = np.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2))
    return (np.mean(group1) - np.mean(group2)) / pooled_std

def analyze_relationship(df, predictor_col, outcome_col, predictor_values, severity):
    """Perform statistical analysis for a given relationship"""
    group1 = df[(df[predictor_col] == predictor_values[0]) & (df['severity'] == severity)][outcome_col]
    group2 = df[(df[predictor_col] == predictor_values[1]) & (df['severity'] == severity)][outcome_col]
    
    # T-test
    t_stat, p_value = stats.ttest_ind(group1, group2)
    
    # Cohen's d
    cohens_d = calculate_cohens_d(group1, group2)
    
    # Descriptive statistics
    results = {
        'group1_name': predictor_values[0],
        'group1_mean': np.mean(group1),
        'group1_std': np.std(group1, ddof=1),
        'group1_n': len(group1),
        'group2_name': predictor_values[1],
        'group2_mean': np.mean(group2),
        'group2_std': np.std(group2, ddof=1),
        'group2_n': len(group2),
        't_statistic': t_stat,
        'p_value': p_value,
        'cohens_d': cohens_d
    }
    
    return results

def create_plots(df):
    """Create side-by-side violin plots for both analyses"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Distribution Analysis by Severity', fontsize=16, fontweight='bold')
    
    severities = ['Mild', 'Severe']
    
    # Plot 1: Evitability vs c_plus_pct
    for idx, severity in enumerate(severities):
        ax = axes[0, idx]
        data_to_plot = []
        positions = []
        
        for pos, evit in enumerate(['Evitable', 'Inevitable'], 1):
            subset = df[(df['evitability'] == evit) & (df['severity'] == severity)]
            data_to_plot.append(subset['c_plus_pct'])
            positions.append(pos)
        
        parts = ax.violinplot(data_to_plot, positions=positions, showmeans=True, 
                              showmedians=True, widths=0.7)
        
        # Color the violin plots
        for pc in parts['bodies']:
            pc.set_facecolor('lightblue')
            pc.set_alpha(0.7)
        
        ax.set_xticks([1, 2])
        ax.set_xticklabels(['Evitable', 'Inevitable'])
        ax.set_ylabel('C+ Percentage', fontsize=11)
        ax.set_title(f'{severity} - Evitability Franken Label vs Annotator C+ Label Proportion', fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
    
    # Plot 2: Causal vs i_plus_pct
    for idx, severity in enumerate(severities):
        ax = axes[1, idx]
        data_to_plot = []
        positions = []
        
        for pos, causal in enumerate(['CC', 'COC'], 1):
            subset = df[(df['causal'] == causal) & (df['severity'] == severity)]
            data_to_plot.append(subset['i_plus_pct'])
            positions.append(pos)
        
        parts = ax.violinplot(data_to_plot, positions=positions, showmeans=True,
                              showmedians=True, widths=0.7)
        
        # Color the violin plots
        for pc in parts['bodies']:
            pc.set_facecolor('lightcoral')
            pc.set_alpha(0.7)
        
        ax.set_xticks([1, 2])
        ax.set_xticklabels(['Causal Chain CC', 'Common Cause COC'])
        ax.set_ylabel('I+ Percentage', fontsize=11)
        ax.set_title(f'{severity} - Causality Franken Label vs Annotator I+ Label Proportion', fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_PLOT, dpi=300, bbox_inches='tight')
    print(f"Plot saved to {OUTPUT_PLOT}")

def write_statistics(df, output_file):
    """Write detailed statistical results to text file"""
    with open(output_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("STATISTICAL ANALYSIS RESULTS\n")
        f.write("=" * 80 + "\n\n")
        
        if CHOICE_FILTER is not None:
            f.write(f"Filter applied: choice = {CHOICE_FILTER}\n")
        else:
            f.write("No filter applied (all choice values included)\n")
        f.write(f"Total rows analyzed: {len(df)}\n\n")
        
        # Analysis 1: Evitability vs c_plus_pct
        f.write("-" * 80 + "\n")
        f.write("ANALYSIS 1: Evitability Franken Label vs Annotator C+ Label Percentage\n")
        f.write("-" * 80 + "\n\n")
        
        for severity in ['Mild', 'Severe']:
            f.write(f"\n{severity.upper()} SEVERITY:\n")
            f.write("-" * 40 + "\n")
            
            results = analyze_relationship(df, 'evitability', 'c_plus_pct', 
                                          ['Evitable', 'Inevitable'], severity)
            
            f.write(f"\nDescriptive Statistics:\n")
            f.write(f"  {results['group1_name']}: M = {results['group1_mean']:.2f}, "
                   f"SD = {results['group1_std']:.2f}, N = {results['group1_n']}\n")
            f.write(f"  {results['group2_name']}: M = {results['group2_mean']:.2f}, "
                   f"SD = {results['group2_std']:.2f}, N = {results['group2_n']}\n")
            
            f.write(f"\nInferential Statistics:\n")
            f.write(f"  Independent t-test: t({results['group1_n'] + results['group2_n'] - 2}) = "
                   f"{results['t_statistic']:.3f}, p = {results['p_value']:.4f}\n")
            f.write(f"  Cohen's d = {results['cohens_d']:.3f}")
            
            if abs(results['cohens_d']) < 0.2:
                effect = "negligible"
            elif abs(results['cohens_d']) < 0.5:
                effect = "small"
            elif abs(results['cohens_d']) < 0.8:
                effect = "medium"
            else:
                effect = "large"
            f.write(f" ({effect} effect size)\n")
            
            if results['p_value'] < 0.001:
                sig = "***"
            elif results['p_value'] < 0.01:
                sig = "**"
            elif results['p_value'] < 0.05:
                sig = "*"
            else:
                sig = "ns (not significant)"
            f.write(f"  Significance: {sig}\n")
        
        # Analysis 2: Causal vs i_plus_pct
        f.write("\n\n" + "-" * 80 + "\n")
        f.write("ANALYSIS 2: Causality Franken Label vs Annotator I+ Label Percentage\n")
        f.write("-" * 80 + "\n\n")
        
        for severity in ['Mild', 'Severe']:
            f.write(f"\n{severity.upper()} SEVERITY:\n")
            f.write("-" * 40 + "\n")
            
            results = analyze_relationship(df, 'causal', 'i_plus_pct', 
                                          ['CC', 'COC'], severity)
            
            f.write(f"\nDescriptive Statistics:\n")
            f.write(f"  {results['group1_name']}: M = {results['group1_mean']:.2f}, "
                   f"SD = {results['group1_std']:.2f}, N = {results['group1_n']}\n")
            f.write(f"  {results['group2_name']}: M = {results['group2_mean']:.2f}, "
                   f"SD = {results['group2_std']:.2f}, N = {results['group2_n']}\n")
            
            f.write(f"\nInferential Statistics:\n")
            f.write(f"  Independent t-test: t({results['group1_n'] + results['group2_n'] - 2}) = "
                   f"{results['t_statistic']:.3f}, p = {results['p_value']:.4f}\n")
            f.write(f"  Cohen's d = {results['cohens_d']:.3f}")
            
            if abs(results['cohens_d']) < 0.2:
                effect = "negligible"
            elif abs(results['cohens_d']) < 0.5:
                effect = "small"
            elif abs(results['cohens_d']) < 0.8:
                effect = "medium"
            else:
                effect = "large"
            f.write(f" ({effect} effect size)\n")
            
            if results['p_value'] < 0.001:
                sig = "***"
            elif results['p_value'] < 0.01:
                sig = "**"
            elif results['p_value'] < 0.05:
                sig = "*"
            else:
                sig = "ns (not significant)"
            f.write(f"  Significance: {sig}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("Legend: *** p<0.001, ** p<0.01, * p<0.05, ns = not significant\n")
        f.write("=" * 80 + "\n")
    
    print(f"Statistical results saved to {output_file}")

def main():
    # Read CSV
    try:
        df = pd.read_csv(CSV_FILE)
        print(f"Loaded {len(df)} rows from {CSV_FILE}")
    except FileNotFoundError:
        print(f"Error: Could not find file '{CSV_FILE}'")
        sys.exit(1)
    
    # Apply choice filter if specified
    if CHOICE_FILTER is not None:
        df = df[df['choice'] == CHOICE_FILTER]
        print(f"Filtered to {len(df)} rows where choice={CHOICE_FILTER}")
    
    # Create plots
    create_plots(df)
    
    # Generate statistics
    write_statistics(df, OUTPUT_STATS)
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()