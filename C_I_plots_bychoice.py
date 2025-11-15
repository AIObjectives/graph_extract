#!/usr/bin/env python3
"""
Visualization showing all 8 combinations of:
- Evitable/Inevitable
- CC/COC  
- Choice 1/Choice 2

Each scenario is color-coded by its combination type.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple


def parse_causal_string(causal_str: str) -> Dict[str, str]:
    """Parse causal string like 'C+I-K+' into {'C': '+', 'I': '-', 'K': '+'}"""
    result = {}
    i = 0
    while i < len(causal_str):
        if causal_str[i] in ['C', 'I', 'K']:
            var = causal_str[i]
            if i + 1 < len(causal_str) and causal_str[i + 1] in ['+', '-']:
                result[var] = causal_str[i + 1]
                i += 2
            else:
                i += 1
        else:
            i += 1
    return result


def extract_event_data(json_file: Path) -> List[Tuple[Dict[str, str], int]]:
    """Extract causal polarities and utility scores for each event."""
    with open(json_file, 'r') as f:
        lines = f.readlines()
    
    nodes = [json.loads(line) for line in lines]
    
    # Find the I-being node and non-I being
    i_being_node = None
    non_i_being = None
    
    for node in nodes:
        if node['node']['kind'] == 'being':
            if node['node']['label'] == 'I':
                i_being_node = node
            else:
                non_i_being = node['node']['label']
    
    if not i_being_node or not non_i_being:
        return []
    
    # Map event labels to their causal variables
    event_causals = {}
    for link_obj in i_being_node['links']:
        link = link_obj['link']
        if link['kind'] == 'b_link':
            event_label = link_obj['to_node']
            causal_dict = parse_causal_string(link['value'])
            event_causals[event_label] = causal_dict
    
    # Extract utility scores
    results = []
    for node in nodes:
        if node['node']['kind'] == 'event':
            event_label = node['node']['label']
            
            if event_label not in event_causals:
                continue
            
            for link_obj in node['links']:
                link = link_obj['link']
                if link['kind'] == 'utility' and link_obj['to_node'] == non_i_being:
                    utility = int(link['value'])
                    results.append((event_causals[event_label], utility))
                    break
    
    return results


def calculate_scenario_percentages(events: List[Tuple[Dict[str, str], int]]) -> Dict[str, float]:
    """Calculate C+, I+, and K+ percentages for a scenario."""
    c_plus = sum(1 for causal_dict, _ in events if causal_dict.get('C') == '+')
    c_minus = sum(1 for causal_dict, _ in events if causal_dict.get('C') == '-')
    i_plus = sum(1 for causal_dict, _ in events if causal_dict.get('I') == '+')
    i_minus = sum(1 for causal_dict, _ in events if causal_dict.get('I') == '-')
    k_plus = sum(1 for causal_dict, _ in events if causal_dict.get('K') == '+')
    k_minus = sum(1 for causal_dict, _ in events if causal_dict.get('K') == '-')
    
    c_total = c_plus + c_minus
    i_total = i_plus + i_minus
    k_total = k_plus + k_minus
    
    return {
        'c_plus_pct': (c_plus / c_total * 100) if c_total > 0 else 0,
        'i_plus_pct': (i_plus / i_total * 100) if i_total > 0 else 0,
        'k_plus_pct': (k_plus / k_total * 100) if k_total > 0 else 0,
    }


def extract_condition_properties(condition_name: str) -> Dict[str, str]:
    """Extract evitability and causal structure from condition name."""
    # condition_name format: {cc|coc}_{evitable|inevitable}_{action_yes|prevention_no}_stories
    parts = condition_name.split('_')
    
    causal = parts[0]  # cc or coc
    evitability = parts[1]  # evitable or inevitable
    
    return {
        'causal': causal.upper(),
        'evitability': evitability.capitalize()
    }


def get_combination_label(causal: str, evitability: str, choice: int) -> str:
    """Create label for the 8-way combination."""
    return f"{evitability} {causal} Ch{choice}"


def collect_all_scenarios(base_path: Path, severity: str) -> List[Dict]:
    """Collect all scenarios with their combination labels."""
    severity_path = base_path / severity
    
    all_scenarios = []
    
    for subfolder in sorted(severity_path.iterdir()):
        if not subfolder.is_dir():
            continue
        
        condition_name = subfolder.name
        props = extract_condition_properties(condition_name)
        
        # Process all JSON files
        for json_file in sorted(subfolder.glob("*.json")):
            # Parse filename: scenarioID_choice_N.json
            parts = json_file.stem.split('_choice_')
            if len(parts) != 2:
                continue
            
            scenario_id = int(parts[0])
            choice_num = int(parts[1])
            
            events = extract_event_data(json_file)
            
            if events:
                percentages = calculate_scenario_percentages(events)
                combination = get_combination_label(
                    props['causal'], 
                    props['evitability'], 
                    choice_num
                )
                
                all_scenarios.append({
                    'condition': condition_name,
                    'scenario_id': scenario_id,
                    'choice': choice_num,
                    'causal': props['causal'],
                    'evitability': props['evitability'],
                    'combination': combination,
                    'c_plus_pct': percentages['c_plus_pct'],
                    'i_plus_pct': percentages['i_plus_pct'],
                    'k_plus_pct': percentages['k_plus_pct']
                })
    
    return all_scenarios


def create_8way_scatterplot_ci(mild_scenarios: List[Dict], severe_scenarios: List[Dict], output_dir: Path):
    """Create side-by-side scatterplot with 8-way color coding."""
    
    # Define 8 distinct colors for the combinations
    combination_colors = {
        'Evitable CC Ch1': '#1f77b4',    # blue
        'Evitable CC Ch2': '#aec7e8',    # light blue
        'Evitable COC Ch1': '#ff7f0e',   # orange
        'Evitable COC Ch2': '#ffbb78',   # light orange
        'Inevitable CC Ch1': '#2ca02c',  # green
        'Inevitable CC Ch2': '#98df8a',  # light green
        'Inevitable COC Ch1': '#d62728', # red
        'Inevitable COC Ch2': '#ff9896', # light red
    }
    
    # Shorter labels for legend
    combination_labels = {
        'Evitable CC Ch1': '1. Evit CC Ch1',
        'Evitable CC Ch2': '2. Evit CC Ch2',
        'Evitable COC Ch1': '3. Evit COC Ch1',
        'Evitable COC Ch2': '4. Evit COC Ch2',
        'Inevitable CC Ch1': '5. Inev CC Ch1',
        'Inevitable CC Ch2': '6. Inev CC Ch2',
        'Inevitable COC Ch1': '7. Inev COC Ch1',
        'Inevitable COC Ch2': '8. Inev COC Ch2',
    }
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(22, 10))
    
    def plot_scenarios(ax, scenarios, title):
        # Group by combination
        by_combination = defaultdict(list)
        for s in scenarios:
            by_combination[s['combination']].append(s)
        
        # Set random seed for reproducible jitter
        np.random.seed(42)
        
        # Jitter amount (in percentage points)
        jitter_amount = 1.5
        
        # Plot each combination
        handles = []
        for combo in sorted(combination_colors.keys()):
            if combo not in by_combination:
                continue
            
            combo_scenarios = by_combination[combo]
            c_vals = [s['c_plus_pct'] for s in combo_scenarios]
            i_vals = [s['i_plus_pct'] for s in combo_scenarios]
            
            # Add jitter
            c_jittered = [c + np.random.uniform(-jitter_amount, jitter_amount) for c in c_vals]
            i_jittered = [i + np.random.uniform(-jitter_amount, jitter_amount) for i in i_vals]
            
            color = combination_colors[combo]
            label = combination_labels[combo]
            
            scatter = ax.scatter(c_jittered, i_jittered, c=color, alpha=0.7, s=120,
                               edgecolors='black', linewidth=0.5, label=label)
            handles.append(scatter)
        
        # Crosshairs at 50%
        ax.axhline(y=50, color='gray', linestyle='-', linewidth=0.8, alpha=0.4, zorder=0)
        ax.axvline(x=50, color='gray', linestyle='-', linewidth=0.8, alpha=0.4, zorder=0)
        
        # Quadrant labels
        ax.text(5, 95, 'Low C+\nHigh I+', fontsize=9, alpha=0.3, va='top')
        ax.text(95, 95, 'High C+\nHigh I+', fontsize=9, alpha=0.3, va='top', ha='right')
        ax.text(5, 5, 'Low C+\nLow I+', fontsize=9, alpha=0.3, va='bottom')
        ax.text(95, 5, 'High C+\nLow I+', fontsize=9, alpha=0.3, va='bottom', ha='right')
        
        # Styling
        ax.set_xlabel('C+ Percentage (%)', fontsize=12, fontweight='bold')
        ax.set_ylabel('I+ Percentage (%)', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
        ax.set_xlim(-5, 105)
        ax.set_ylim(-5, 105)
        ax.grid(True, alpha=0.25, linestyle='--')
        
        return handles
    
    # Plot both severity levels
    # handles1 = plot_scenarios(ax1, mild_scenarios, 'Mild Harm / Mild Good')
    handles2 = plot_scenarios(ax2, severe_scenarios, 'Severe Harm / Very Good')
    
    # Shared legend below
    fig.legend(handles=handles2, loc='center', bbox_to_anchor=(0.5, -0.02),
              ncol=4, fontsize=10, frameon=True, fancybox=True, shadow=True,
              title='8 Combinations (Evitability × Causal Structure × Choice)')

    
    plt.suptitle('All Scenarios by 8-Way Combination', 
                fontsize=16, fontweight='bold', y=0.98)
    
    plt.tight_layout(rect=[0, 0.06, 1, 0.96])
    
    output_file = output_dir / 'scatterplot_8way_combinations_CI.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()
    
    # Print summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS BY COMBINATION")
    print("=" * 80)
    
    # for severity_name, scenarios in [('MILD', mild_scenarios), ('SEVERE', severe_scenarios)]:
    for severity_name, scenarios in [('SEVERE', severe_scenarios)]:
        print(f"\n{severity_name}:")
        by_combination = defaultdict(list)
        for s in scenarios:
            by_combination[s['combination']].append(s)
        
        for combo in sorted(combination_colors.keys()):
            if combo not in by_combination:
                continue
            combo_scenarios = by_combination[combo]
            
            avg_c = sum(s['c_plus_pct'] for s in combo_scenarios) / len(combo_scenarios)
            avg_i = sum(s['i_plus_pct'] for s in combo_scenarios) / len(combo_scenarios)
            
            print(f"  {combination_labels[combo]:20s} (n={len(combo_scenarios):3d}): "
                  f"C+={avg_c:5.1f}%, I+={avg_i:5.1f}%")


def create_8way_scatterplot_ck(mild_scenarios: List[Dict], severe_scenarios: List[Dict], output_dir: Path):
    """Create side-by-side scatterplot with 8-way color coding for C+ vs K+."""
    
    # Define 8 distinct colors for the combinations
    combination_colors = {
        'Evitable CC Ch1': '#1f77b4',    # blue
        'Evitable CC Ch2': '#aec7e8',    # light blue
        'Evitable COC Ch1': '#ff7f0e',   # orange
        'Evitable COC Ch2': '#ffbb78',   # light orange
        'Inevitable CC Ch1': '#2ca02c',  # green
        'Inevitable CC Ch2': '#98df8a',  # light green
        'Inevitable COC Ch1': '#d62728', # red
        'Inevitable COC Ch2': '#ff9896', # light red
    }
    
    # Shorter labels for legend
    combination_labels = {
        'Evitable CC Ch1': '1. Evit CC Ch1',
        'Evitable CC Ch2': '2. Evit CC Ch2',
        'Evitable COC Ch1': '3. Evit COC Ch1',
        'Evitable COC Ch2': '4. Evit COC Ch2',
        'Inevitable CC Ch1': '5. Inev CC Ch1',
        'Inevitable CC Ch2': '6. Inev CC Ch2',
        'Inevitable COC Ch1': '7. Inev COC Ch1',
        'Inevitable COC Ch2': '8. Inev COC Ch2',
    }
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(22, 10))
    
    def plot_scenarios(ax, scenarios, title):
        # Group by combination
        by_combination = defaultdict(list)
        for s in scenarios:
            by_combination[s['combination']].append(s)
        
        # Set random seed for reproducible jitter
        np.random.seed(42)
        
        # Jitter amount (in percentage points)
        jitter_amount = 1.5
        
        # Plot each combination
        handles = []
        for combo in sorted(combination_colors.keys()):
            if combo not in by_combination:
                continue
            
            combo_scenarios = by_combination[combo]
            c_vals = [s['c_plus_pct'] for s in combo_scenarios]
            k_vals = [s['k_plus_pct'] for s in combo_scenarios]
            
            # Add jitter
            c_jittered = [c + np.random.uniform(-jitter_amount, jitter_amount) for c in c_vals]
            k_jittered = [k + np.random.uniform(-jitter_amount, jitter_amount) for k in k_vals]
            
            color = combination_colors[combo]
            label = combination_labels[combo]
            
            scatter = ax.scatter(c_jittered, k_jittered, c=color, alpha=0.7, s=120,
                               edgecolors='black', linewidth=0.5, label=label)
            handles.append(scatter)
        
        # Crosshairs at 50%
        ax.axhline(y=50, color='gray', linestyle='-', linewidth=0.8, alpha=0.4, zorder=0)
        ax.axvline(x=50, color='gray', linestyle='-', linewidth=0.8, alpha=0.4, zorder=0)
        
        # Quadrant labels
        ax.text(5, 95, 'Low C+\nHigh K+', fontsize=9, alpha=0.3, va='top')
        ax.text(95, 95, 'High C+\nHigh K+', fontsize=9, alpha=0.3, va='top', ha='right')
        ax.text(5, 5, 'Low C+\nLow K+', fontsize=9, alpha=0.3, va='bottom')
        ax.text(95, 5, 'High C+\nLow K+', fontsize=9, alpha=0.3, va='bottom', ha='right')
        
        # Styling
        ax.set_xlabel('C+ Percentage (%)', fontsize=12, fontweight='bold')
        ax.set_ylabel('K+ Percentage (%)', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
        ax.set_xlim(-5, 105)
        ax.set_ylim(-5, 105)
        ax.grid(True, alpha=0.25, linestyle='--')
        
        return handles
    
    # Plot both severity levels
    handles1 = plot_scenarios(ax1, mild_scenarios, 'Mild Harm / Mild Good')
    handles2 = plot_scenarios(ax2, severe_scenarios, 'Severe Harm / Very Good')
    
    # Shared legend below
    fig.legend(handles=handles1, loc='center', bbox_to_anchor=(0.5, -0.02),
              ncol=4, fontsize=10, frameon=True, fancybox=True, shadow=True,
              title='8 Combinations (Evitability × Causal Structure × Choice)')
    
    plt.suptitle('All Scenarios by 8-Way Combination: C+ vs K+', 
                fontsize=16, fontweight='bold', y=0.98)
    
    plt.tight_layout(rect=[0, 0.06, 1, 0.96])
    
    output_file = output_dir / 'scatterplot_8way_combinations_CK.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()
    
    # Print summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS BY COMBINATION (C+ vs K+)")
    print("=" * 80)
    
    for severity_name, scenarios in [('MILD', mild_scenarios), ('SEVERE', severe_scenarios)]:
        print(f"\n{severity_name}:")
        by_combination = defaultdict(list)
        for s in scenarios:
            by_combination[s['combination']].append(s)
        
        for combo in sorted(combination_colors.keys()):
            if combo not in by_combination:
                continue
            combo_scenarios = by_combination[combo]
            
            avg_c = sum(s['c_plus_pct'] for s in combo_scenarios) / len(combo_scenarios)
            avg_k = sum(s['k_plus_pct'] for s in combo_scenarios) / len(combo_scenarios)
            
            print(f"  {combination_labels[combo]:20s} (n={len(combo_scenarios):3d}): "
                  f"C+={avg_c:5.1f}%, K+={avg_k:5.1f}%")


def main():
    """Main visualization function."""

    base_path = Path("franken_annotated_outputs_newnewprompts")
    output_dir = Path("visualization_outputs_newnewprompt")
    
    output_dir.mkdir(exist_ok=True)
    
    if not base_path.exists():
        print(f"Error: Directory '{base_path}' not found!")
        return
    
    print("\n" + "=" * 80)
    print("8-WAY COMBINATION SCATTERPLOT")
    print("=" * 80)
    print("\nAnalyzing all scenarios by:")
    print("  - Evitability (Evitable/Inevitable)")
    print("  - Causal Structure (CC/COC)")
    print("  - Choice (1/2)")
    print("\nCollapsing across action_yes/prevention_no distinction.\n")
    
    # Collect data
    # mild_scenarios = collect_all_scenarios(base_path, 'conditions_mild_harm_mild_good')
    severe_scenarios = collect_all_scenarios(base_path, 'conditions_severe_harm_very_good')
    
    # if mild_scenarios and severe_scenarios:
    #     create_8way_scatterplot_ci(mild_scenarios, severe_scenarios, output_dir)
    #     create_8way_scatterplot_ck(mild_scenarios, severe_scenarios, output_dir)
    mild_scenarios = []  # skipping mild scenarios
    create_8way_scatterplot_ci(mild_scenarios, severe_scenarios, output_dir)
    
    print("\n" + "=" * 80)
    print("VISUALIZATION COMPLETE!")
    print("=" * 80)
    print(f"\nPlots saved to: {output_dir}/")
    print("  - scatterplot_8way_combinations_CI.png (C+ vs I+)")
    print("  - scatterplot_8way_combinations_CK.png (C+ vs K+)\n")


if __name__ == "__main__":
    main()