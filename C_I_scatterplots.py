#!/usr/bin/env python3
"""
Visualization script for moral scenario annotations.
Creates scatterplots showing C+ vs I+ percentages for each scenario.
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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
    """Calculate C+ and I+ percentages for a scenario."""
    c_plus = sum(1 for causal_dict, _ in events if causal_dict.get('C') == '+')
    c_minus = sum(1 for causal_dict, _ in events if causal_dict.get('C') == '-')
    i_plus = sum(1 for causal_dict, _ in events if causal_dict.get('I') == '+')
    i_minus = sum(1 for causal_dict, _ in events if causal_dict.get('I') == '-')
    
    c_total = c_plus + c_minus
    i_total = i_plus + i_minus
    
    return {
        'c_plus_pct': (c_plus / c_total * 100) if c_total > 0 else 0,
        'i_plus_pct': (i_plus / i_total * 100) if i_total > 0 else 0,
        'c_total': c_total,
        'i_total': i_total
    }


def collect_scenario_data(base_path: Path, severity: str) -> Dict:
    """Collect all scenario data for one severity level."""
    severity_path = base_path / severity
    
    subfolder_data = {}
    
    for subfolder in sorted(severity_path.iterdir()):
        if not subfolder.is_dir():
            continue
        
        condition_name = subfolder.name
        scenarios = []
        
        # Group files by scenario ID
        scenario_files = defaultdict(list)
        for json_file in subfolder.glob("*.json"):
            parts = json_file.stem.split('_choice_')
            if len(parts) == 2:
                scenario_id = int(parts[0])
                scenario_files[scenario_id].append(json_file)
        
        # Process each scenario (combine both choices)
        for scenario_id, files in sorted(scenario_files.items()):
            all_events = []
            for json_file in files:
                events = extract_event_data(json_file)
                all_events.extend(events)
            
            if all_events:
                percentages = calculate_scenario_percentages(all_events)
                scenarios.append({
                    'id': scenario_id,
                    'c_plus_pct': percentages['c_plus_pct'],
                    'i_plus_pct': percentages['i_plus_pct'],
                    'c_total': percentages['c_total'],
                    'i_total': percentages['i_total']
                })
        
        subfolder_data[condition_name] = scenarios
    
    return subfolder_data


def create_scatterplot(subfolder_data: Dict, severity: str, output_dir: Path):
    """Create scatterplot for one severity level with all subfolders."""
    
    # Color palette for 8 conditions
    colors = [
        '#1f77b4',  # blue
        '#ff7f0e',  # orange
        '#2ca02c',  # green
        '#d62728',  # red
        '#9467bd',  # purple
        '#8c564b',  # brown
        '#e377c2',  # pink
        '#7f7f7f',  # gray
    ]
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Plot each condition
    legend_handles = []
    for idx, (condition_name, scenarios) in enumerate(sorted(subfolder_data.items())):
        if not scenarios:
            continue
        
        c_vals = [s['c_plus_pct'] for s in scenarios]
        i_vals = [s['i_plus_pct'] for s in scenarios]
        
        color = colors[idx % len(colors)]
        scatter = ax.scatter(c_vals, i_vals, c=color, alpha=0.6, s=100, 
                           edgecolors='black', linewidth=0.5, label=condition_name)
        legend_handles.append(scatter)
    
    # Add crosshairs at 50%
    ax.axhline(y=50, color='red', linestyle='-', linewidth=0.8, alpha=0.5, zorder=0)
    ax.axvline(x=50, color='red', linestyle='-', linewidth=0.8, alpha=0.5, zorder=0)
    
    # Add quadrant labels (subtle, in corners)
    ax.text(5, 95, 'Low C+\nHigh I+', fontsize=9, alpha=0.4, va='top')
    ax.text(95, 95, 'High C+\nHigh I+', fontsize=9, alpha=0.4, va='top', ha='right')
    ax.text(5, 5, 'Low C+\nLow I+', fontsize=9, alpha=0.4, va='bottom')
    ax.text(95, 5, 'High C+\nLow I+', fontsize=9, alpha=0.4, va='bottom', ha='right')
    
    # Styling
    ax.set_xlabel('C+ Percentage (%)', fontsize=12, fontweight='bold')
    ax.set_ylabel('I+ Percentage (%)', fontsize=12, fontweight='bold')
    ax.set_title(f'Scenario Distribution: C+ vs I+\n{severity.replace("_", " ").title()}', 
                fontsize=14, fontweight='bold', pad=20)
    
    ax.set_xlim(-5, 105)
    ax.set_ylim(-5, 105)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Legend
    ax.legend(handles=legend_handles, loc='upper left', bbox_to_anchor=(1.02, 1), 
             fontsize=9, frameon=True, fancybox=True, shadow=True)
    
    plt.tight_layout()
    
    # Save
    output_file = output_dir / f'scatterplot_{severity}.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()


def create_combined_scatterplot(mild_data: Dict, severe_data: Dict, output_dir: Path):
    """Create side-by-side comparison of mild vs severe."""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 9))
    
    colors = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728',
        '#9467bd', '#8c564b', '#e377c2', '#7f7f7f'
    ]
    
    def plot_on_axis(ax, subfolder_data, title):
        legend_handles = []
        for idx, (condition_name, scenarios) in enumerate(sorted(subfolder_data.items())):
            if not scenarios:
                continue
            
            c_vals = [s['c_plus_pct'] for s in scenarios]
            i_vals = [s['i_plus_pct'] for s in scenarios]
            
            color = colors[idx % len(colors)]
            scatter = ax.scatter(c_vals, i_vals, c=color, alpha=0.6, s=100,
                               edgecolors='black', linewidth=0.5, label=condition_name)
            legend_handles.append(scatter)
        
        # Crosshairs
        ax.axhline(y=50, color='red', linestyle='-', linewidth=0.8, alpha=0.5, zorder=0)
        ax.axvline(x=50, color='red', linestyle='-', linewidth=0.8, alpha=0.5, zorder=0)
        
        # Quadrant labels
        ax.text(5, 95, 'Low C+\nHigh I+', fontsize=8, alpha=0.4, va='top')
        ax.text(95, 95, 'High C+\nHigh I+', fontsize=8, alpha=0.4, va='top', ha='right')
        ax.text(5, 5, 'Low C+\nLow I+', fontsize=8, alpha=0.4, va='bottom')
        ax.text(95, 5, 'High C+\nLow I+', fontsize=8, alpha=0.4, va='bottom', ha='right')
        
        ax.set_xlabel('C+ Percentage (%)', fontsize=11, fontweight='bold')
        ax.set_ylabel('I+ Percentage (%)', fontsize=11, fontweight='bold')
        ax.set_title(title, fontsize=12, fontweight='bold', pad=15)
        ax.set_xlim(-5, 105)
        ax.set_ylim(-5, 105)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        return legend_handles
    
    # Plot both
    handles1 = plot_on_axis(ax1, mild_data, 'Mild Harm / Mild Good')
    handles2 = plot_on_axis(ax2, severe_data, 'Severe Harm / Very Good')
    
    # Shared legend
    fig.legend(handles=handles1, loc='center', bbox_to_anchor=(0.5, -0.05), 
              ncol=4, fontsize=9, frameon=True, fancybox=True, shadow=True)
    
    plt.suptitle('Scenario Distribution Comparison: C+ vs I+', 
                fontsize=16, fontweight='bold', y=0.98)
    
    plt.tight_layout(rect=[0, 0.05, 1, 0.96])
    
    output_file = output_dir / 'scatterplot_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()


def create_by_grouping_scatterplots(mild_data: Dict, severe_data: Dict, output_dir: Path):
    """Create scatterplots grouped by causal structure, evitability, and action type."""
    
    groupings = {
        'causal_structure': {
            'CC': lambda name: name.startswith('cc_'),
            'COC': lambda name: name.startswith('coc_')
        },
        'evitability': {
            'Evitable': lambda name: 'evitable_' in name,
            'Inevitable': lambda name: 'inevitable_' in name
        },
        'action_type': {
            'Action Yes': lambda name: 'action_yes_' in name,
            'Prevention No': lambda name: 'prevention_no_' in name
        }
    }
    
    colors_by_group = {
        'CC': '#2ca02c',
        'COC': '#d62728',
        'Evitable': '#1f77b4',
        'Inevitable': '#ff7f0e',
        'Action Yes': '#9467bd',
        'Prevention No': '#8c564b'
    }
    
    for grouping_name, groups in groupings.items():
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 9))
        
        def plot_grouped(ax, subfolder_data, title):
            legend_handles = []
            
            for group_name, filter_func in groups.items():
                all_c_vals = []
                all_i_vals = []
                
                for condition_name, scenarios in subfolder_data.items():
                    if filter_func(condition_name):
                        for s in scenarios:
                            all_c_vals.append(s['c_plus_pct'])
                            all_i_vals.append(s['i_plus_pct'])
                
                if all_c_vals:
                    color = colors_by_group[group_name]
                    scatter = ax.scatter(all_c_vals, all_i_vals, c=color, alpha=0.6, 
                                       s=100, edgecolors='black', linewidth=0.5, 
                                       label=group_name)
                    legend_handles.append(scatter)
            
            # Crosshairs
            ax.axhline(y=50, color='red', linestyle='-', linewidth=0.8, alpha=0.5, zorder=0)
            ax.axvline(x=50, color='red', linestyle='-', linewidth=0.8, alpha=0.5, zorder=0)
            
            # Quadrant labels
            ax.text(5, 95, 'Low C+\nHigh I+', fontsize=8, alpha=0.4, va='top')
            ax.text(95, 95, 'High C+\nHigh I+', fontsize=8, alpha=0.4, va='top', ha='right')
            ax.text(5, 5, 'Low C+\nLow I+', fontsize=8, alpha=0.4, va='bottom')
            ax.text(95, 5, 'High C+\nLow I+', fontsize=8, alpha=0.4, va='bottom', ha='right')
            
            ax.set_xlabel('C+ Percentage (%)', fontsize=11, fontweight='bold')
            ax.set_ylabel('I+ Percentage (%)', fontsize=11, fontweight='bold')
            ax.set_title(title, fontsize=12, fontweight='bold', pad=15)
            ax.set_xlim(-5, 105)
            ax.set_ylim(-5, 105)
            ax.grid(True, alpha=0.3, linestyle='--')
            
            return legend_handles
        
        # Plot both severity levels
        handles1 = plot_grouped(ax1, mild_data, 'Mild Harm / Mild Good')
        handles2 = plot_grouped(ax2, severe_data, 'Severe Harm / Very Good')
        
        # Shared legend
        fig.legend(handles=handles1, loc='center', bbox_to_anchor=(0.5, -0.05),
                  ncol=len(groups), fontsize=10, frameon=True, fancybox=True, shadow=True)
        
        title = f'Grouped by {grouping_name.replace("_", " ").title()}'
        plt.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
        
        plt.tight_layout(rect=[0, 0.05, 1, 0.96])
        
        output_file = output_dir / f'scatterplot_by_{grouping_name}.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {output_file}")
        plt.close()


def main():
    """Main visualization function."""
    
    base_path = Path("franken_annotated_outputs")
    output_dir = Path("visualization_outputs")
    
    output_dir.mkdir(exist_ok=True)
    
    if not base_path.exists():
        print(f"Error: Directory '{base_path}' not found!")
        return
    
    print("\n" + "=" * 80)
    print("SCENARIO SCATTERPLOT VISUALIZATION")
    print("=" * 80)
    print("\nGenerating C+ vs I+ scatterplots...\n")
    
    # Collect data
    mild_data = collect_scenario_data(base_path, 'conditions_mild_harm_mild_good')
    severe_data = collect_scenario_data(base_path, 'conditions_severe_harm_very_good')
    
    # Create individual severity plots
    if mild_data:
        create_scatterplot(mild_data, 'conditions_mild_harm_mild_good', output_dir)
    
    if severe_data:
        create_scatterplot(severe_data, 'conditions_severe_harm_very_good', output_dir)
    
    # Create comparison plot
    if mild_data and severe_data:
        create_combined_scatterplot(mild_data, severe_data, output_dir)
        
        # Create grouped plots
        create_by_grouping_scatterplots(mild_data, severe_data, output_dir)
    
    print("\n" + "=" * 80)
    print("VISUALIZATION COMPLETE!")
    print("=" * 80)
    print(f"\nPlots saved to: {output_dir}/")
    print("\nGenerated files:")
    print("  - scatterplot_mild_harm_mild_good.png")
    print("  - scatterplot_severe_harm_very_good.png")
    print("  - scatterplot_comparison.png (side-by-side)")
    print("  - scatterplot_by_causal_structure.png")
    print("  - scatterplot_by_evitability.png")
    print("  - scatterplot_by_action_type.png")
    print()


if __name__ == "__main__":
    main()