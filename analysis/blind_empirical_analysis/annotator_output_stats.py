#!/usr/bin/env python3
"""
Analysis script for moral scenario annotations with scenario-level weighting.
Each scenario (combining both choices) is weighted equally regardless of event count.
Outputs are organized into multiple files for clarity.
"""

import json
import os
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Set


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
    """
    Extract causal polarities and utility scores for each event in a JSON file.
    Returns list of (causal_dict, utility_to_non_i) tuples.
    """
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
    
    # Map event labels to their causal variables from I-being links
    event_causals = {}
    for link_obj in i_being_node['links']:
        link = link_obj['link']
        if link['kind'] == 'b_link':
            event_label = link_obj['to_node']
            causal_dict = parse_causal_string(link['value'])
            event_causals[event_label] = causal_dict
    
    # Extract utility scores from event nodes to non-I being
    results = []
    for node in nodes:
        if node['node']['kind'] == 'event':
            event_label = node['node']['label']
            
            if event_label not in event_causals:
                continue
            
            # Find utility to non-I being
            for link_obj in node['links']:
                link = link_obj['link']
                if link['kind'] == 'utility' and link_obj['to_node'] == non_i_being:
                    utility = int(link['value'])
                    results.append((event_causals[event_label], utility))
                    break
    
    return results


class ScenarioStats:
    """Statistics for a single scenario (combining both choices)."""
    
    def __init__(self, scenario_id: int):
        self.scenario_id = scenario_id
        self.events_by_utility = {'positive': [], 'negative': [], 'zero': []}
        self.all_events = []
    
    def add_events(self, events: List[Tuple[Dict[str, str], int]]):
        """Add events from a choice file."""
        for causal_dict, utility in events:
            self.all_events.append((causal_dict, utility))
            
            if utility > 0:
                category = 'positive'
            elif utility < 0:
                category = 'negative'
            else:
                category = 'zero'
            
            self.events_by_utility[category].append(causal_dict)
    
    def get_proportions(self) -> Dict:
        """Calculate proportions for this scenario."""
        proportions = {
            'positive': {},
            'negative': {},
            'zero': {},
            'total': {}
        }
        
        # Calculate for each utility category
        for category in ['positive', 'negative', 'zero']:
            events = self.events_by_utility[category]
            
            for var in ['C', 'I', 'K']:
                plus_count = sum(1 for e in events if e.get(var) == '+')
                minus_count = sum(1 for e in events if e.get(var) == '-')
                total = plus_count + minus_count
                
                if total > 0:
                    proportions[category][f'{var}+'] = plus_count / total
                    proportions[category][f'{var}-'] = minus_count / total
                else:
                    proportions[category][f'{var}+'] = 0
                    proportions[category][f'{var}-'] = 0
        
        # Calculate overall
        for var in ['C', 'I', 'K']:
            plus_count = sum(1 for e, _ in self.all_events if e.get(var) == '+')
            minus_count = sum(1 for e, _ in self.all_events if e.get(var) == '-')
            total = plus_count + minus_count
            
            if total > 0:
                proportions['total'][f'{var}+'] = plus_count / total
                proportions['total'][f'{var}-'] = minus_count / total
            else:
                proportions['total'][f'{var}+'] = 0
                proportions['total'][f'{var}-'] = 0
        
        return proportions
    
    def get_counts(self) -> Dict:
        """Get raw counts for this scenario."""
        counts = {
            'positive': Counter(),
            'negative': Counter(),
            'zero': Counter(),
            'total': Counter()
        }
        
        for category in ['positive', 'negative', 'zero']:
            for causal_dict in self.events_by_utility[category]:
                for var in ['C', 'I', 'K']:
                    if var in causal_dict:
                        key = f"{var}{causal_dict[var]}"
                        counts[category][key] += 1
                        counts['total'][key] += 1
        
        return counts


class ConditionStats:
    """Statistics for a condition (subfolder), using scenario-level weighting."""
    
    def __init__(self, name: str):
        self.name = name
        self.scenarios = {}  # scenario_id -> ScenarioStats
    
    def add_scenario_events(self, scenario_id: int, events: List[Tuple[Dict[str, str], int]]):
        """Add events for a scenario."""
        if scenario_id not in self.scenarios:
            self.scenarios[scenario_id] = ScenarioStats(scenario_id)
        self.scenarios[scenario_id].add_events(events)
    
    def get_weighted_stats(self) -> Dict:
        """Calculate scenario-weighted statistics."""
        if not self.scenarios:
            return None
        
        # Average proportions across scenarios
        avg_proportions = {
            'positive': defaultdict(float),
            'negative': defaultdict(float),
            'zero': defaultdict(float),
            'total': defaultdict(float)
        }
        
        n_scenarios = len(self.scenarios)
        
        for scenario in self.scenarios.values():
            proportions = scenario.get_proportions()
            
            for category in ['positive', 'negative', 'zero', 'total']:
                for key, value in proportions[category].items():
                    avg_proportions[category][key] += value / n_scenarios
        
        # Also get total counts (for reference)
        total_counts = {
            'positive': Counter(),
            'negative': Counter(),
            'zero': Counter(),
            'total': Counter()
        }
        
        for scenario in self.scenarios.values():
            counts = scenario.get_counts()
            for category in ['positive', 'negative', 'zero', 'total']:
                total_counts[category].update(counts[category])
        
        return {
            'proportions': avg_proportions,
            'counts': total_counts,
            'n_scenarios': n_scenarios
        }
    
    def get_all_utilities(self) -> List[int]:
        """Get all utility scores across all scenarios."""
        utilities = []
        for scenario in self.scenarios.values():
            for _, utility in scenario.all_events:
                utilities.append(utility)
        return utilities


def format_stats_report(stats: Dict, title: str, global_stats: Dict = None) -> str:
    """Format statistics into a readable report."""
    if not stats:
        return f"\n{title}\nNo data available.\n"
    
    lines = [f"\n{'=' * 80}", title, '=' * 80, ""]
    
    proportions = stats['proportions']
    counts = stats['counts']
    n_scenarios = stats['n_scenarios']
    
    lines.append(f"Number of scenarios: {n_scenarios}")
    lines.append(f"Total events analyzed: {sum(counts['total'].values())}")
    lines.append("")
    
    # Helper function to format a category
    def format_category(cat_name):
        cat_props = proportions[cat_name]
        cat_counts = counts[cat_name]
        
        lines.append(f"\n{cat_name.upper()} UTILITY:")
        lines.append(f"  Total assignments: {sum(cat_counts.values())}")
        
        for var in ['C', 'I', 'K']:
            plus_key = f'{var}+'
            minus_key = f'{var}-'
            
            # Get this condition's values
            plus_prop = cat_props.get(plus_key, 0)
            minus_prop = cat_props.get(minus_key, 0)
            plus_count = cat_counts.get(plus_key, 0)
            minus_count = cat_counts.get(minus_key, 0)
            
            plus_line = f"    {var}+: {plus_count:4d} (scenario-avg: {100*plus_prop:5.1f}%"
            minus_line = f"    {var}-: {minus_count:4d} (scenario-avg: {100*minus_prop:5.1f}%"
            
            # Add global comparison if provided
            if global_stats:
                global_props = global_stats['proportions'][cat_name]
                global_plus = global_props.get(plus_key, 0)
                global_minus = global_props.get(minus_key, 0)
                
                plus_line += f", global-avg: {100*global_plus:5.1f}%"
                minus_line += f", global-avg: {100*global_minus:5.1f}%"
            
            plus_line += ")"
            minus_line += ")"
            
            lines.append(plus_line)
            lines.append(minus_line)
    
    # Report each category
    format_category('positive')
    format_category('negative')
    format_category('zero')
    format_category('total')
    
    return '\n'.join(lines)


def merge_condition_stats(conditions: List[ConditionStats]) -> Dict:
    """Merge multiple conditions, maintaining scenario-level weighting."""
    all_scenarios = []
    
    for condition in conditions:
        all_scenarios.extend(condition.scenarios.values())
    
    if not all_scenarios:
        return None
    
    # Average proportions across all scenarios
    avg_proportions = {
        'positive': defaultdict(float),
        'negative': defaultdict(float),
        'zero': defaultdict(float),
        'total': defaultdict(float)
    }
    
    n_scenarios = len(all_scenarios)
    
    for scenario in all_scenarios:
        proportions = scenario.get_proportions()
        
        for category in ['positive', 'negative', 'zero', 'total']:
            for key, value in proportions[category].items():
                avg_proportions[category][key] += value / n_scenarios
    
    # Get total counts
    total_counts = {
        'positive': Counter(),
        'negative': Counter(),
        'zero': Counter(),
        'total': Counter()
    }
    
    for scenario in all_scenarios:
        counts = scenario.get_counts()
        for category in ['positive', 'negative', 'zero', 'total']:
            total_counts[category].update(counts[category])
    
    return {
        'proportions': avg_proportions,
        'counts': total_counts,
        'n_scenarios': n_scenarios
    }


def analyze_severity_level(base_path: Path, severity: str, output_dir: Path):
    """Analyze one severity level and output to file."""
    
    severity_path = base_path / severity
    output_file = output_dir / f"{severity}_individual_subfolders.txt"
    
    # Storage
    conditions = {}  # condition_name -> ConditionStats
    
    # Process each subfolder
    subfolders = sorted([d for d in severity_path.iterdir() if d.is_dir()])
    
    for subfolder in subfolders:
        condition_name = subfolder.name
        condition = ConditionStats(condition_name)
        
        # Group files by scenario ID
        scenario_files = defaultdict(list)
        for json_file in subfolder.glob("*.json"):
            # Parse filename: scenarioID_choice_N.json
            parts = json_file.stem.split('_choice_')
            if len(parts) == 2:
                scenario_id = int(parts[0])
                scenario_files[scenario_id].append(json_file)
        
        # Process each scenario (both choices)
        for scenario_id, files in scenario_files.items():
            for json_file in files:
                events = extract_event_data(json_file)
                condition.add_scenario_events(scenario_id, events)
        
        conditions[condition_name] = condition
    
    # Calculate global stats for this severity
    global_stats = merge_condition_stats(list(conditions.values()))
    
    # Write individual subfolder report
    with open(output_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write(f"INDIVIDUAL SUBFOLDER ANALYSIS: {severity.upper().replace('_', ' ')}\n")
        f.write("=" * 80 + "\n")
        f.write("Note: Proportions are scenario-weighted (each scenario contributes equally)\n")
        f.write("=" * 80 + "\n")
        
        for condition_name in sorted(conditions.keys()):
            stats = conditions[condition_name].get_weighted_stats()
            report = format_stats_report(stats, f"Subfolder: {condition_name}", global_stats)
            f.write(report)
    
    print(f"✓ Written: {output_file}")
    
    return conditions, global_stats


def write_grouped_analysis(conditions_by_severity: Dict, output_dir: Path):
    """Write grouped analyses across both severity levels."""
    
    # Group by causal structure (CC vs COC)
    output_file = output_dir / "grouped_by_causal_structure.txt"
    with open(output_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("GROUPED ANALYSIS: CAUSAL STRUCTURE (CC vs COC)\n")
        f.write("=" * 80 + "\n\n")
        
        for severity in ['conditions_mild_harm_mild_good', 'conditions_severe_harm_very_good']:
            conditions, global_stats = conditions_by_severity[severity]
            
            f.write("\n" + "#" * 80 + "\n")
            f.write(f"SEVERITY: {severity.upper().replace('_', ' ')}\n")
            f.write("#" * 80 + "\n")
            
            cc_conditions = [c for name, c in conditions.items() if name.startswith('cc_')]
            coc_conditions = [c for name, c in conditions.items() if name.startswith('coc_')]
            
            cc_stats = merge_condition_stats(cc_conditions)
            coc_stats = merge_condition_stats(coc_conditions)
            
            f.write(format_stats_report(cc_stats, "CC (Causal Chain)", global_stats))
            f.write(format_stats_report(coc_stats, "COC (Common Cause)", global_stats))
            
            # Comparative analysis
            f.write("\n\n" + "-" * 80 + "\n")
            f.write("COMPARATIVE ANALYSIS: I POLARITY\n")
            f.write("-" * 80 + "\n")
            
            cc_i_plus = cc_stats['proportions']['total']['I+']
            cc_i_minus = cc_stats['proportions']['total']['I-']
            coc_i_plus = coc_stats['proportions']['total']['I+']
            coc_i_minus = coc_stats['proportions']['total']['I-']
            
            f.write(f"\nCC Scenarios (scenario-weighted average):")
            f.write(f"\n  I+: {100*cc_i_plus:5.1f}%")
            f.write(f"\n  I-: {100*cc_i_minus:5.1f}%")
            
            f.write(f"\n\nCOC Scenarios (scenario-weighted average):")
            f.write(f"\n  I+: {100*coc_i_plus:5.1f}%")
            f.write(f"\n  I-: {100*coc_i_minus:5.1f}%")
            
            diff = abs(100*cc_i_plus - 100*coc_i_plus)
            dominant = "CC" if cc_i_plus > coc_i_plus else "COC"
            dominant_pol = "I+" if cc_i_plus > coc_i_plus else "I-"
            
            f.write(f"\n\nInterpretation:")
            f.write(f"\n  {dominant} scenarios show {diff:.1f}% more {dominant_pol}")
            if diff > 10:
                f.write(f"\n  → STRONG systematic dominance")
            elif diff > 5:
                f.write(f"\n  → MODERATE systematic dominance")
            else:
                f.write(f"\n  → WEAK/no systematic dominance")
    
    print(f"✓ Written: {output_file}")
    
    # Group by evitability
    output_file = output_dir / "grouped_by_evitability.txt"
    with open(output_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("GROUPED ANALYSIS: EVITABILITY (Evitable vs Inevitable)\n")
        f.write("=" * 80 + "\n\n")
        
        for severity in ['conditions_mild_harm_mild_good', 'conditions_severe_harm_very_good']:
            conditions, global_stats = conditions_by_severity[severity]
            
            f.write("\n" + "#" * 80 + "\n")
            f.write(f"SEVERITY: {severity.upper().replace('_', ' ')}\n")
            f.write("#" * 80 + "\n")
            
            evit_conditions = [c for name, c in conditions.items() if 'evitable_' in name]
            inev_conditions = [c for name, c in conditions.items() if 'inevitable_' in name]
            
            evit_stats = merge_condition_stats(evit_conditions)
            inev_stats = merge_condition_stats(inev_conditions)
            
            f.write(format_stats_report(evit_stats, "EVITABLE", global_stats))
            f.write(format_stats_report(inev_stats, "INEVITABLE", global_stats))
            
            # Comparative analysis
            f.write("\n\n" + "-" * 80 + "\n")
            f.write("COMPARATIVE ANALYSIS: C POLARITY\n")
            f.write("-" * 80 + "\n")
            
            evit_c_plus = evit_stats['proportions']['total']['C+']
            evit_c_minus = evit_stats['proportions']['total']['C-']
            inev_c_plus = inev_stats['proportions']['total']['C+']
            inev_c_minus = inev_stats['proportions']['total']['C-']
            
            f.write(f"\nEvitable Scenarios (scenario-weighted average):")
            f.write(f"\n  C+: {100*evit_c_plus:5.1f}%")
            f.write(f"\n  C-: {100*evit_c_minus:5.1f}%")
            
            f.write(f"\n\nInevitable Scenarios (scenario-weighted average):")
            f.write(f"\n  C+: {100*inev_c_plus:5.1f}%")
            f.write(f"\n  C-: {100*inev_c_minus:5.1f}%")
            
            diff = abs(100*evit_c_plus - 100*inev_c_plus)
            dominant = "Evitable" if evit_c_plus > inev_c_plus else "Inevitable"
            dominant_pol = "C+" if evit_c_plus > inev_c_plus else "C-"
            
            f.write(f"\n\nInterpretation:")
            f.write(f"\n  {dominant} scenarios show {diff:.1f}% more {dominant_pol}")
            if diff > 10:
                f.write(f"\n  → STRONG systematic dominance")
            elif diff > 5:
                f.write(f"\n  → MODERATE systematic dominance")
            else:
                f.write(f"\n  → WEAK/no systematic dominance")
    
    print(f"✓ Written: {output_file}")
    
    # Group by action type
    output_file = output_dir / "grouped_by_action_type.txt"
    with open(output_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("GROUPED ANALYSIS: ACTION TYPE (Action_Yes vs Prevention_No)\n")
        f.write("=" * 80 + "\n\n")
        
        for severity in ['conditions_mild_harm_mild_good', 'conditions_severe_harm_very_good']:
            conditions, global_stats = conditions_by_severity[severity]
            
            f.write("\n" + "#" * 80 + "\n")
            f.write(f"SEVERITY: {severity.upper().replace('_', ' ')}\n")
            f.write("#" * 80 + "\n")
            
            action_conditions = [c for name, c in conditions.items() if 'action_yes_' in name]
            prevention_conditions = [c for name, c in conditions.items() if 'prevention_no_' in name]
            
            action_stats = merge_condition_stats(action_conditions)
            prevention_stats = merge_condition_stats(prevention_conditions)
            
            f.write(format_stats_report(action_stats, "ACTION_YES", global_stats))
            f.write(format_stats_report(prevention_stats, "PREVENTION_NO", global_stats))
            
            # Comparative analysis
            f.write("\n\n" + "-" * 80 + "\n")
            f.write("COMPARATIVE ANALYSIS: POLARITY PATTERNS\n")
            f.write("-" * 80 + "\n")
            
            f.write("\nAction_Yes (scenario-weighted average):")
            for var in ['C', 'I', 'K']:
                plus = action_stats['proportions']['total'][f'{var}+']
                minus = action_stats['proportions']['total'][f'{var}-']
                f.write(f"\n  {var}+: {100*plus:5.1f}%  |  {var}-: {100*minus:5.1f}%")
            
            f.write("\n\nPrevention_No (scenario-weighted average):")
            for var in ['C', 'I', 'K']:
                plus = prevention_stats['proportions']['total'][f'{var}+']
                minus = prevention_stats['proportions']['total'][f'{var}-']
                f.write(f"\n  {var}+: {100*plus:5.1f}%  |  {var}-: {100*minus:5.1f}%")
            
            f.write("\n\nDifferences (Action_Yes % - Prevention_No %):")
            distinguishing = []
            for var in ['C', 'I', 'K']:
                action_plus = action_stats['proportions']['total'][f'{var}+']
                prevention_plus = prevention_stats['proportions']['total'][f'{var}+']
                diff = 100 * (action_plus - prevention_plus)
                
                f.write(f"\n  {var}+: {diff:+6.1f}%  |  {var}-: {-diff:+6.1f}%")
                
                if abs(diff) > 10:
                    distinguishing.append((var, diff))
            
            f.write("\n\nInterpretation:")
            if distinguishing:
                f.write("\n  DISTINGUISHING FEATURES found:")
                for var, diff in distinguishing:
                    pol = '+' if diff > 0 else '-'
                    f.write(f"\n    - {var}{pol} is {abs(diff):.1f}% more common in Action_Yes")
            else:
                f.write("\n  No strong distinguishing features (all differences < 10%)")
    
    print(f"✓ Written: {output_file}")


def write_utility_analysis(conditions_by_severity: Dict, output_dir: Path):
    """Write utility distribution analysis."""
    
    output_file = output_dir / "utility_distributions.txt"
    
    with open(output_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("UTILITY SCORE DISTRIBUTIONS\n")
        f.write("=" * 80 + "\n\n")
        
        severity_utils = {}
        
        for severity in ['conditions_mild_harm_mild_good', 'conditions_severe_harm_very_good']:
            conditions, _ = conditions_by_severity[severity]
            
            f.write("\n" + "#" * 80 + "\n")
            f.write(f"SEVERITY: {severity.upper().replace('_', ' ')}\n")
            f.write("#" * 80 + "\n")
            
            all_utils = []
            for condition in conditions.values():
                all_utils.extend(condition.get_all_utilities())
            
            severity_utils[severity] = all_utils
            
            pos_utils = [u for u in all_utils if u > 0]
            neg_utils = [u for u in all_utils if u < 0]
            zero_utils = [u for u in all_utils if u == 0]
            
            f.write(f"\nAll Utilities:")
            f.write(f"\n  Count: {len(all_utils)}")
            if all_utils:
                f.write(f"\n  Range: [{min(all_utils)}, {max(all_utils)}]")
                f.write(f"\n  Mean: {sum(all_utils)/len(all_utils):.2f}")
            
            if pos_utils:
                extreme_pos = sum(1 for u in pos_utils if u >= 80)
                f.write(f"\n\nPositive Utilities:")
                f.write(f"\n  Count: {len(pos_utils)}")
                f.write(f"\n  Range: [{min(pos_utils)}, {max(pos_utils)}]")
                f.write(f"\n  Mean: {sum(pos_utils)/len(pos_utils):.2f}")
                f.write(f"\n  Extreme (≥80): {extreme_pos} ({100*extreme_pos/len(pos_utils):.1f}%)")
            
            if neg_utils:
                extreme_neg = sum(1 for u in neg_utils if u <= -80)
                f.write(f"\n\nNegative Utilities:")
                f.write(f"\n  Count: {len(neg_utils)}")
                f.write(f"\n  Range: [{min(neg_utils)}, {max(neg_utils)}]")
                f.write(f"\n  Mean: {sum(neg_utils)/len(neg_utils):.2f}")
                f.write(f"\n  Extreme (≤-80): {extreme_neg} ({100*extreme_neg/len(neg_utils):.1f}%)")
            
            if zero_utils:
                f.write(f"\n\nZero Utilities: {len(zero_utils)}")
        
        # Cross-severity comparison
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("COMPARISON: Mild vs Severe\n")
        f.write("=" * 80 + "\n")
        
        mild_utils = severity_utils.get('conditions_mild_harm_mild_good', [])
        severe_utils = severity_utils.get('conditions_severe_harm_very_good', [])
        
        if mild_utils and severe_utils:
            mild_pos = [u for u in mild_utils if u > 0]
            severe_pos = [u for u in severe_utils if u > 0]
            mild_neg = [u for u in mild_utils if u < 0]
            severe_neg = [u for u in severe_utils if u < 0]
            
            f.write("\nPositive Utilities:")
            if mild_pos:
                mild_ext_pct = 100 * sum(1 for u in mild_pos if u >= 80) / len(mild_pos)
                f.write(f"\n  Mild - Mean: {sum(mild_pos)/len(mild_pos):.2f}, Extreme (≥80): {mild_ext_pct:.1f}%")
            if severe_pos:
                severe_ext_pct = 100 * sum(1 for u in severe_pos if u >= 80) / len(severe_pos)
                f.write(f"\n  Severe - Mean: {sum(severe_pos)/len(severe_pos):.2f}, Extreme (≥80): {severe_ext_pct:.1f}%")
            
            f.write("\n\nNegative Utilities:")
            if mild_neg:
                mild_ext_pct = 100 * sum(1 for u in mild_neg if u <= -80) / len(mild_neg)
                f.write(f"\n  Mild - Mean: {sum(mild_neg)/len(mild_neg):.2f}, Extreme (≤-80): {mild_ext_pct:.1f}%")
            if severe_neg:
                severe_ext_pct = 100 * sum(1 for u in severe_neg if u <= -80) / len(severe_neg)
                f.write(f"\n  Severe - Mean: {sum(severe_neg)/len(severe_neg):.2f}, Extreme (≤-80): {severe_ext_pct:.1f}%")
            
            f.write("\n\nInterpretation:")
            if severe_pos and mild_pos:
                severe_mean = sum(severe_pos)/len(severe_pos)
                mild_mean = sum(mild_pos)/len(mild_pos)
                if severe_mean > mild_mean + 10:
                    f.write(f"\n  Severe scenarios show MORE EXTREME positive utilities (+{severe_mean - mild_mean:.1f})")
                elif mild_mean > severe_mean + 10:
                    f.write(f"\n  Mild scenarios show MORE EXTREME positive utilities (+{mild_mean - severe_mean:.1f})")
                else:
                    f.write(f"\n  Similar positive utility distributions")
            
            if severe_neg and mild_neg:
                severe_mean = sum(severe_neg)/len(severe_neg)
                mild_mean = sum(mild_neg)/len(mild_neg)
                if severe_mean < mild_mean - 10:
                    f.write(f"\n  Severe scenarios show MORE EXTREME negative utilities ({abs(severe_mean - mild_mean):.1f} more negative)")
                elif mild_mean < severe_mean - 10:
                    f.write(f"\n  Mild scenarios show MORE EXTREME negative utilities ({abs(mild_mean - severe_mean):.1f} more negative)")
                else:
                    f.write(f"\n  Similar negative utility distributions")
    
    print(f"✓ Written: {output_file}")


def main():
    """Main analysis function."""
    
    base_path = Path("franken_annotated_outputs")
    output_dir = Path("analysis_reports")
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    if not base_path.exists():
        print(f"Error: Directory '{base_path}' not found!")
        return
    
    print("\n" + "=" * 80)
    print("MORAL SCENARIO ANALYSIS - Scenario-Weighted Statistics")
    print("=" * 80)
    print("\nProcessing data with equal scenario weighting...")
    print("Each scenario (both choices combined) contributes equally to statistics.\n")
    
    # Analyze both severity levels
    conditions_by_severity = {}
    
    for severity in ['conditions_mild_harm_mild_good', 'conditions_severe_harm_very_good']:
        severity_path = base_path / severity
        if severity_path.exists():
            print(f"\nAnalyzing {severity}...")
            conditions, global_stats = analyze_severity_level(base_path, severity, output_dir)
            conditions_by_severity[severity] = (conditions, global_stats)
        else:
            print(f"Warning: {severity} directory not found!")
    
    # Write grouped analyses
    if conditions_by_severity:
        print("\nGenerating grouped analyses...")
        write_grouped_analysis(conditions_by_severity, output_dir)
        
        print("\nGenerating utility distribution analysis...")
        write_utility_analysis(conditions_by_severity, output_dir)
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"\nReports saved to: {output_dir}/")
    print("\nGenerated files:")
    print("  - mild_harm_mild_good_individual_subfolders.txt")
    print("  - severe_harm_very_good_individual_subfolders.txt")
    print("  - grouped_by_causal_structure.txt")
    print("  - grouped_by_evitability.txt")
    print("  - grouped_by_action_type.txt")
    print("  - utility_distributions.txt")
    print()


if __name__ == "__main__":
    main()