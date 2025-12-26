#!/usr/bin/env python3
"""
Decomposed visualization showing scenarios split by different properties.
Creates 8 separate plots with cleaner, less crowded visualizations.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

# ============================================================================
# CONFIGURATION: Filter out events with non-negative utility to non-I being
# ============================================================================
EXCLUDE_NON_NEGATIVE_UTILITY = False  # Set to False to include all events
# ============================================================================


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
    
    event_causals = {}
    for link_obj in i_being_node['links']:
        link = link_obj['link']
        if link['kind'] == 'b_link':
            event_label = link_obj['to_node']
            causal_dict = parse_causal_string(link['value'])
            event_causals[event_label] = causal_dict
    
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
                    
                    # Apply filter if enabled
                    if EXCLUDE_NON_NEGATIVE_UTILITY and utility >= 0:
                        break  # Skip this event
                    
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
    parts = condition_name.split('_')
    causal = parts[0]  # cc or coc
    evitability = parts[1]  # evitable or inevitable
    
    return {
        'causal': causal.upper(),
        'evitability': evitability.capitalize()
    }


def collect_all_scenarios(base_path: Path, severity: str) -> List[Dict]:
    """Collect all scenarios with their properties."""
    severity_path = base_path / severity
    all_scenarios = []
    
    for subfolder in sorted(severity_path.iterdir()):
        if not subfolder.is_dir():
            continue
        
        condition_name = subfolder.name
        props = extract_condition_properties(condition_name)
        
        for json_file in sorted(subfolder.glob("*.json")):
            parts = json_file.stem.split('_choice_')
            if len(parts) != 2:
                continue
            
            scenario_id = int(parts[0])
            choice_num = int(parts[1])
            
            events = extract_event_data(json_file)
            
            if events:
                percentages = calculate_scenario_percentages(events)
                
                all_scenarios.append({
                    'condition': condition_name,
                    'scenario_id': scenario_id,
                    'choice': choice_num,
                    'causal': props['causal'],
                    'evitability': props['evitability'],
                    'c_plus_pct': percentages['c_plus_pct'],
                    'i_plus_pct': percentages['i_plus_pct'],
                    'k_plus_pct': percentages['k_plus_pct']
                })
    
    return all_scenarios


def plot_single_group(mild_scenarios, severe_scenarios, title, output_file, base_color='#1f77b4', y_axis='i'):
    """Plot scenarios with single color (dark=Ch1, light=Ch2) - side by side for mild and severe."""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 9))
    
    from matplotlib.colors import to_rgba
    
    def plot_on_axis(ax, scenarios, subtitle):
        # Separate by choice
        ch1_scenarios = [s for s in scenarios if s['choice'] == 1]
        ch2_scenarios = [s for s in scenarios if s['choice'] == 2]
        
        np.random.seed(42)
        jitter = 1.0
        
        y_key = f'{y_axis}_plus_pct'
        y_label = f'{y_axis.upper()}+ Percentage (%)'
        
        # Plot Choice 2 (light) first so Choice 1 (dark) is on top
        if ch2_scenarios:
            c_vals = [s['c_plus_pct'] for s in ch2_scenarios]
            y_vals = [s[y_key] for s in ch2_scenarios]
            c_jit = [c + np.random.uniform(-jitter, jitter) for c in c_vals]
            y_jit = [y + np.random.uniform(-jitter, jitter) for y in y_vals]
            
            # Light color (add alpha to make it lighter)
            light_color = list(to_rgba(base_color))
            light_color[3] = 0.4  # Make it lighter by reducing alpha
            
            ax.scatter(c_jit, y_jit, c=[light_color], s=100, 
                      edgecolors='black', linewidth=0.5, label='Choice 2', zorder=2)
        
        # Plot Choice 1 (dark)
        if ch1_scenarios:
            c_vals = [s['c_plus_pct'] for s in ch1_scenarios]
            y_vals = [s[y_key] for s in ch1_scenarios]
            c_jit = [c + np.random.uniform(-jitter, jitter) for c in c_vals]
            y_jit = [y + np.random.uniform(-jitter, jitter) for y in y_vals]
            
            ax.scatter(c_jit, y_jit, c=base_color, alpha=0.7, s=100,
                      edgecolors='black', linewidth=0.5, label='Choice 1', zorder=3)
        
        # Crosshairs
        ax.axhline(y=50, color='gray', linestyle='-', linewidth=0.8, alpha=0.4, zorder=0)
        ax.axvline(x=50, color='gray', linestyle='-', linewidth=0.8, alpha=0.4, zorder=0)
        
        # Styling
        ax.set_xlabel('C+ Percentage (%)', fontsize=11, fontweight='bold')
        ax.set_ylabel(y_label, fontsize=11, fontweight='bold')
        ax.set_title(subtitle, fontsize=12, fontweight='bold', pad=15)
        ax.set_xlim(-5, 105)
        ax.set_ylim(-5, 105)
        ax.grid(True, alpha=0.25, linestyle='--')
        ax.legend(fontsize=9, loc='upper left')
    
    plot_on_axis(ax1, mild_scenarios, 'Mild Harm / Mild Good')
    plot_on_axis(ax2, severe_scenarios, 'Severe Harm / Very Good')
    
    plt.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()


def plot_two_groups(mild_scenarios, severe_scenarios, title, output_file, group_key, group_colors, y_axis='i'):
    """Plot scenarios with two colors for groups (each with dark/light for choices) - side by side."""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 9))
    
    from matplotlib.colors import to_rgba
    
    def plot_on_axis(ax, scenarios, subtitle):
        np.random.seed(42)
        jitter = 1.5
        
        y_key = f'{y_axis}_plus_pct'
        y_label = f'{y_axis.upper()}+ Percentage (%)'
        
        # Plot each group
        for group_value, base_color in group_colors.items():
            group_scenarios = [s for s in scenarios if s[group_key] == group_value]
            
            ch1 = [s for s in group_scenarios if s['choice'] == 1]
            ch2 = [s for s in group_scenarios if s['choice'] == 2]
            
            # Plot Choice 2 (light) first
            if ch2:
                c_vals = [s['c_plus_pct'] for s in ch2]
                y_vals = [s[y_key] for s in ch2]
                c_jit = [c + np.random.uniform(-jitter, jitter) for c in c_vals]
                y_jit = [y + np.random.uniform(-jitter, jitter) for y in y_vals]
                
                light_color = list(to_rgba(base_color))
                light_color[3] = 0.4
                
                ax.scatter(c_jit, y_jit, c=[light_color], s=100,
                          edgecolors='black', linewidth=0.5, 
                          label=f'{group_value} Ch2', zorder=2)
            
            # Plot Choice 1 (dark)
            if ch1:
                c_vals = [s['c_plus_pct'] for s in ch1]
                y_vals = [s[y_key] for s in ch1]
                c_jit = [c + np.random.uniform(-jitter, jitter) for c in c_vals]
                y_jit = [y + np.random.uniform(-jitter, jitter) for y in y_vals]
                
                ax.scatter(c_jit, y_jit, c=base_color, alpha=0.7, s=100,
                          edgecolors='black', linewidth=0.5,
                          label=f'{group_value} Ch1', zorder=3)
        
        # Crosshairs
        ax.axhline(y=50, color='gray', linestyle='-', linewidth=0.8, alpha=0.4, zorder=0)
        ax.axvline(x=50, color='gray', linestyle='-', linewidth=0.8, alpha=0.4, zorder=0)
        
        # Styling
        ax.set_xlabel('C+ Percentage (%)', fontsize=11, fontweight='bold')
        ax.set_ylabel(y_label, fontsize=11, fontweight='bold')
        ax.set_title(subtitle, fontsize=12, fontweight='bold', pad=15)
        ax.set_xlim(-5, 105)
        ax.set_ylim(-5, 105)
        ax.grid(True, alpha=0.25, linestyle='--')
        ax.legend(fontsize=9, loc='upper left')
    
    plot_on_axis(ax1, mild_scenarios, 'Mild Harm / Mild Good')
    plot_on_axis(ax2, severe_scenarios, 'Severe Harm / Very Good')
    
    plt.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()


def main():
    """Main visualization function."""
    
    base_path = Path("franken_annotated_outputs")
    output_dir = Path("decomposed_plots_onlynegative_utility" if EXCLUDE_NON_NEGATIVE_UTILITY else "decomposed_plots_all_events")
    
    output_dir.mkdir(exist_ok=True)
    
    if not base_path.exists():
        print(f"Error: Directory '{base_path}' not found!")
        return
    
    print("\n" + "=" * 80)
    print("DECOMPOSED SCATTERPLOT VISUALIZATIONS")
    print("=" * 80)
    print(f"\nExclude non-negative utility events: {EXCLUDE_NON_NEGATIVE_UTILITY}")
    print("\nGenerating 8 separate plots for cleaner visualization...\n")
    
    # Collect data for both severity levels
    mild_scenarios = collect_all_scenarios(base_path, 'conditions_mild_harm_mild_good')
    severe_scenarios = collect_all_scenarios(base_path, 'conditions_severe_harm_very_good')
    
    # Filter scenarios by properties for MILD
    mild_evitable = [s for s in mild_scenarios if s['evitability'] == 'Evitable']
    mild_inevitable = [s for s in mild_scenarios if s['evitability'] == 'Inevitable']
    mild_cc = [s for s in mild_scenarios if s['causal'] == 'CC']
    mild_coc = [s for s in mild_scenarios if s['causal'] == 'COC']
    
    # Filter scenarios by properties for SEVERE
    severe_evitable = [s for s in severe_scenarios if s['evitability'] == 'Evitable']
    severe_inevitable = [s for s in severe_scenarios if s['evitability'] == 'Inevitable']
    severe_cc = [s for s in severe_scenarios if s['causal'] == 'CC']
    severe_coc = [s for s in severe_scenarios if s['causal'] == 'COC']
    
    # === PLOTS 1-4: Single color with dark/light for choice ===
    
    # Plot 1: All Evitable
    plot_single_group(
        mild_evitable, severe_evitable,
        'All Evitable Scenarios (CC + COC)',
        output_dir / '1_evitable_only.png',
        base_color='#1f77b4',  # blue
        y_axis='i'
    )
    
    # Plot 2: All Inevitable
    plot_single_group(
        mild_inevitable, severe_inevitable,
        'All Inevitable Scenarios (CC + COC)',
        output_dir / '2_inevitable_only.png',
        base_color='#ff7f0e',  # orange
        y_axis='i'
    )
    
    # Plot 3: All CC
    plot_single_group(
        mild_cc, severe_cc,
        'All CC Scenarios (Evitable + Inevitable)',
        output_dir / '3_cc_only.png',
        base_color='#2ca02c',  # green
        y_axis='i'
    )
    
    # Plot 4: All COC
    plot_single_group(
        mild_coc, severe_coc,
        'All COC Scenarios (Evitable + Inevitable)',
        output_dir / '4_coc_only.png',
        base_color='#d62728',  # red
        y_axis='i'
    )
    
    # === PLOTS 5-8: Two colors for secondary property + dark/light for choice ===
    
    # Plot 5: All Evitable, split by CC/COC
    plot_two_groups(
        mild_evitable, severe_evitable,
        'All Evitable: CC vs COC',
        output_dir / '5_evitable_by_causal.png',
        group_key='causal',
        group_colors={'CC': '#2ca02c', 'COC': '#d62728'},
        y_axis='i'
    )
    
    # Plot 6: All Inevitable, split by CC/COC
    plot_two_groups(
        mild_inevitable, severe_inevitable,
        'All Inevitable: CC vs COC',
        output_dir / '6_inevitable_by_causal.png',
        group_key='causal',
        group_colors={'CC': '#2ca02c', 'COC': '#d62728'},
        y_axis='i'
    )
    
    # Plot 7: All CC, split by Evitable/Inevitable
    plot_two_groups(
        mild_cc, severe_cc,
        'All CC: Evitable vs Inevitable',
        output_dir / '7_cc_by_evitability.png',
        group_key='evitability',
        group_colors={'Evitable': '#1f77b4', 'Inevitable': '#ff7f0e'},
        y_axis='i'
    )
    
    # Plot 8: All COC, split by Evitable/Inevitable
    plot_two_groups(
        mild_coc, severe_coc,
        'All COC: Evitable vs Inevitable',
        output_dir / '8_coc_by_evitability.png',
        group_key='evitability',
        group_colors={'Evitable': '#1f77b4', 'Inevitable': '#ff7f0e'},
        y_axis='i'
    )
    
    print("\n" + "=" * 80)
    print("VISUALIZATION COMPLETE!")
    print("=" * 80)
    print(f"\nAll 8 plots saved to: {output_dir}/\n")
    print("Plot 1: All Evitable (single color)")
    print("Plot 2: All Inevitable (single color)")
    print("Plot 3: All CC (single color)")
    print("Plot 4: All COC (single color)")
    print("Plot 5: All Evitable split by CC/COC (two colors)")
    print("Plot 6: All Inevitable split by CC/COC (two colors)")
    print("Plot 7: All CC split by Evitable/Inevitable (two colors)")
    print("Plot 8: All COC split by Evitable/Inevitable (two colors)\n")


if __name__ == "__main__":
    main()