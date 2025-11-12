#!/usr/bin/env python3
"""
Analysis script for moral scenario annotations.
Generates statistical reports on causal variable polarities (C, I, K)
grouped by utility scores and various experimental conditions.
"""

import json
import os
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Set

# ============================================================================
# CONFIGURATION FLAGS
# ============================================================================
INCLUDE_COC = False  # Set to True when COC data is ready
# ============================================================================


def parse_causal_string(causal_str: str) -> Dict[str, str]:
    """
    Parse causal string like 'C+I-K+' into {'C': '+', 'I': '-', 'K': '+'}
    """
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
            
            # Skip if this event doesn't have causal info from I-being
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


def count_polarities(data: List[Tuple[Dict[str, str], int]]) -> Dict:
    """
    Count C, I, K polarities by utility category.
    Returns dict with 'positive', 'negative', 'zero', and 'total' counts.
    """
    counts = {
        'positive': Counter(),
        'negative': Counter(),
        'zero': Counter(),
        'total': Counter()
    }
    
    for causal_dict, utility in data:
        # Determine utility category
        if utility > 0:
            category = 'positive'
        elif utility < 0:
            category = 'negative'
        else:
            category = 'zero'
        
        # Count polarities
        for var in ['C', 'I', 'K']:
            if var in causal_dict:
                key = f"{var}{causal_dict[var]}"
                counts[category][key] += 1
                counts['total'][key] += 1
    
    return counts


def format_counts_report(counts: Dict, title: str, global_counts: Dict = None) -> str:
    """
    Format counts into a readable report section with local and global proportions.
    """
    lines = [f"\n{'=' * 80}", title, '=' * 80, ""]
    
    # Total causal assignments
    total_assignments = sum(counts['total'].values())
    lines.append(f"Total causal variable assignments: {total_assignments}")
    lines.append("")
    
    # Helper function to format counts with proportions
    def format_category(cat_name, cat_counts):
        cat_total = sum(cat_counts.values())
        lines.append(f"\n{cat_name.upper()} UTILITY:")
        lines.append(f"  Events in category: {cat_total // 3 if cat_total > 0 else 0}")
        lines.append(f"  Total assignments: {cat_total}")
        
        for var in ['C', 'I', 'K']:
            pos_key = f"{var}+"
            neg_key = f"{var}-"
            pos_count = cat_counts.get(pos_key, 0)
            neg_count = cat_counts.get(neg_key, 0)
            var_total = pos_count + neg_count
            
            if var_total > 0:
                local_pos_pct = (pos_count / var_total) * 100
                local_neg_pct = (neg_count / var_total) * 100
            else:
                local_pos_pct = local_neg_pct = 0
            
            pos_line = f"    {var}+: {pos_count:4d} (local: {local_pos_pct:5.1f}%"
            
            # Add global proportion if provided
            if global_counts:
                global_cat_counts = global_counts[cat_name.lower()]
                global_var_total = global_cat_counts.get(pos_key, 0) + global_cat_counts.get(neg_key, 0)
                if global_var_total > 0:
                    global_pos_pct = (pos_count / global_var_total) * 100
                    pos_line += f", global: {global_pos_pct:5.1f}%"
            
            pos_line += ")"
            lines.append(pos_line)
            
            neg_line = f"    {var}-: {neg_count:4d} (local: {local_neg_pct:5.1f}%"
            
            if global_counts:
                global_cat_counts = global_counts[cat_name.lower()]
                global_var_total = global_cat_counts.get(pos_key, 0) + global_cat_counts.get(neg_key, 0)
                if global_var_total > 0:
                    global_neg_pct = (neg_count / global_var_total) * 100
                    neg_line += f", global: {global_neg_pct:5.1f}%"
            
            neg_line += ")"
            lines.append(neg_line)
    
    # Report for each utility category
    format_category("Positive", counts['positive'])
    format_category("Negative", counts['negative'])
    format_category("Zero", counts['zero'])
    
    # Overall totals
    lines.append(f"\nOVERALL (all utility categories):")
    lines.append(f"  Total assignments: {total_assignments}")
    
    for var in ['C', 'I', 'K']:
        pos_key = f"{var}+"
        neg_key = f"{var}-"
        pos_count = counts['total'].get(pos_key, 0)
        neg_count = counts['total'].get(neg_key, 0)
        var_total = pos_count + neg_count
        
        if var_total > 0:
            local_pos_pct = (pos_count / var_total) * 100
            local_neg_pct = (neg_count / var_total) * 100
        else:
            local_pos_pct = local_neg_pct = 0
        
        pos_line = f"    {var}+: {pos_count:4d} (local: {local_pos_pct:5.1f}%"
        
        if global_counts:
            global_var_total = global_counts['total'].get(pos_key, 0) + global_counts['total'].get(neg_key, 0)
            if global_var_total > 0:
                global_pos_pct = (pos_count / global_var_total) * 100
                pos_line += f", global: {global_pos_pct:5.1f}%"
        
        pos_line += ")"
        lines.append(pos_line)
        
        neg_line = f"    {var}-: {neg_count:4d} (local: {local_neg_pct:5.1f}%"
        
        if global_counts:
            global_var_total = global_counts['total'].get(pos_key, 0) + global_counts['total'].get(neg_key, 0)
            if global_var_total > 0:
                global_neg_pct = (neg_count / global_var_total) * 100
                neg_line += f", global: {global_neg_pct:5.1f}%"
        
        neg_line += ")"
        lines.append(neg_line)
    
    return '\n'.join(lines)


def merge_counts(counts_list: List[Dict]) -> Dict:
    """Merge multiple count dictionaries."""
    merged = {
        'positive': Counter(),
        'negative': Counter(),
        'zero': Counter(),
        'total': Counter()
    }
    
    for counts in counts_list:
        for category in ['positive', 'negative', 'zero', 'total']:
            merged[category].update(counts[category])
    
    return merged


def analyze_directory(base_path: Path, severity: str, output_file):
    """Analyze all subfolders for a given severity level."""
    
    severity_path = base_path / severity
    
    # Header
    header = f"\n\n{'#' * 80}\n"
    header += f"ANALYSIS FOR: {severity.upper()}\n"
    header += f"{'#' * 80}\n"
    output_file.write(header)
    
    # Storage for all subfolder data and raw events
    subfolder_data = {}
    subfolder_events = {}  # Store raw events for utility analysis
    all_counts = []
    
    # Get all subfolders
    subfolders = sorted([d for d in severity_path.iterdir() if d.is_dir()])
    
    # Filter out COC folders if not included
    if not INCLUDE_COC:
        subfolders = [d for d in subfolders if not d.name.startswith('coc_')]
        if not subfolders:
            output_file.write("\nNote: All COC data excluded. No CC data found.\n")
            return {}
    
    # Process each subfolder
    for subfolder in subfolders:
        subfolder_name = subfolder.name
        
        # Extract all event data from JSON files
        all_events = []
        json_files = sorted(subfolder.glob("*.json"))
        
        for json_file in json_files:
            events = extract_event_data(json_file)
            all_events.extend(events)
        
        # Count polarities
        counts = count_polarities(all_events)
        subfolder_data[subfolder_name] = counts
        subfolder_events[subfolder_name] = all_events
        all_counts.append(counts)
    
    # Calculate global counts for this severity
    global_counts = merge_counts(all_counts)
    
    # Report individual subfolders
    output_file.write("\n" + "=" * 80)
    output_file.write("\nINDIVIDUAL SUBFOLDER ANALYSIS")
    output_file.write("\n" + "=" * 80 + "\n")
    
    for subfolder_name in sorted(subfolder_data.keys()):
        counts = subfolder_data[subfolder_name]
        report = format_counts_report(counts, f"Subfolder: {subfolder_name}", global_counts)
        output_file.write(report)
    
    # Group by causal structure (CC vs COC)
    output_file.write("\n\n" + "=" * 80)
    output_file.write("\nGROUPED BY CAUSAL STRUCTURE")
    output_file.write("\n" + "=" * 80 + "\n")
    
    cc_counts = merge_counts([counts for name, counts in subfolder_data.items() if name.startswith('cc_')])
    
    if INCLUDE_COC:
        coc_counts = merge_counts([counts for name, counts in subfolder_data.items() if name.startswith('coc_')])
        output_file.write(format_counts_report(cc_counts, "CC (Causal Chain)", global_counts))
        output_file.write(format_counts_report(coc_counts, "COC (Common Cause)", global_counts))
    else:
        output_file.write("\nNote: COC data excluded from analysis (INCLUDE_COC = False)\n")
        output_file.write(format_counts_report(cc_counts, "CC (Causal Chain) - ONLY", global_counts))
    
    # Group by evitability
    output_file.write("\n\n" + "=" * 80)
    output_file.write("\nGROUPED BY EVITABILITY")
    output_file.write("\n" + "=" * 80 + "\n")
    
    evitable_counts = merge_counts([counts for name, counts in subfolder_data.items() if 'evitable_' in name])
    inevitable_counts = merge_counts([counts for name, counts in subfolder_data.items() if 'inevitable_' in name])
    
    output_file.write(format_counts_report(evitable_counts, "EVITABLE", global_counts))
    output_file.write(format_counts_report(inevitable_counts, "INEVITABLE", global_counts))
    
    # Group by action type
    output_file.write("\n\n" + "=" * 80)
    output_file.write("\nGROUPED BY ACTION TYPE")
    output_file.write("\n" + "=" * 80 + "\n")
    
    action_yes_counts = merge_counts([counts for name, counts in subfolder_data.items() if 'action_yes_' in name])
    prevention_no_counts = merge_counts([counts for name, counts in subfolder_data.items() if 'prevention_no_' in name])
    
    output_file.write(format_counts_report(action_yes_counts, "ACTION_YES", global_counts))
    output_file.write(format_counts_report(prevention_no_counts, "PREVENTION_NO", global_counts))
    
    # Additional comparative analyses
    output_file.write("\n\n" + "=" * 80)
    output_file.write("\nCOMPARATIVE ANALYSES")
    output_file.write("\n" + "=" * 80 + "\n")
    
    # Question 1: I polarity dominance between CC and COC (only if COC included)
    if INCLUDE_COC:
        output_file.write("\n" + "-" * 80)
        output_file.write("\n1. I POLARITY COMPARISON: CC vs COC")
        output_file.write("\n" + "-" * 80 + "\n")
        
        coc_counts = merge_counts([counts for name, counts in subfolder_data.items() if name.startswith('coc_')])
        
        cc_i_plus = cc_counts['total'].get('I+', 0)
        cc_i_minus = cc_counts['total'].get('I-', 0)
        cc_i_total = cc_i_plus + cc_i_minus
        
        coc_i_plus = coc_counts['total'].get('I+', 0)
        coc_i_minus = coc_counts['total'].get('I-', 0)
        coc_i_total = coc_i_plus + coc_i_minus
        
        output_file.write(f"\nCC Scenarios:")
        output_file.write(f"\n  I+: {cc_i_plus:4d} ({100*cc_i_plus/cc_i_total if cc_i_total > 0 else 0:5.1f}%)")
        output_file.write(f"\n  I-: {cc_i_minus:4d} ({100*cc_i_minus/cc_i_total if cc_i_total > 0 else 0:5.1f}%)")
        output_file.write(f"\n  Total I assignments: {cc_i_total}")
        
        output_file.write(f"\n\nCOC Scenarios:")
        output_file.write(f"\n  I+: {coc_i_plus:4d} ({100*coc_i_plus/coc_i_total if coc_i_total > 0 else 0:5.1f}%)")
        output_file.write(f"\n  I-: {coc_i_minus:4d} ({100*coc_i_minus/coc_i_total if coc_i_total > 0 else 0:5.1f}%)")
        output_file.write(f"\n  Total I assignments: {coc_i_total}")
        
        if cc_i_total > 0 and coc_i_total > 0:
            cc_i_plus_pct = 100 * cc_i_plus / cc_i_total
            coc_i_plus_pct = 100 * coc_i_plus / coc_i_total
            diff = abs(cc_i_plus_pct - coc_i_plus_pct)
            dominant_structure = "CC" if cc_i_plus_pct > coc_i_plus_pct else "COC"
            dominant_polarity = "I+" if cc_i_plus_pct > coc_i_plus_pct else "I-"
            
            output_file.write(f"\n\nInterpretation:")
            output_file.write(f"\n  {dominant_structure} scenarios show {diff:.1f}% more {dominant_polarity} assignments")
            if diff > 10:
                output_file.write(f"\n  This suggests a STRONG systematic dominance of {dominant_polarity} in {dominant_structure} scenarios")
            elif diff > 5:
                output_file.write(f"\n  This suggests a MODERATE systematic dominance of {dominant_polarity} in {dominant_structure} scenarios")
            else:
                output_file.write(f"\n  The difference is SMALL, suggesting no strong systematic dominance")
    else:
        output_file.write("\n" + "-" * 80)
        output_file.write("\n1. I POLARITY COMPARISON: CC vs COC")
        output_file.write("\n" + "-" * 80)
        output_file.write("\n\n[SKIPPED - COC data not included (INCLUDE_COC = False)]")
    
    # Question 2: C polarity dominance between evitable and inevitable
    output_file.write("\n\n" + "-" * 80)
    output_file.write("\n2. C POLARITY COMPARISON: Evitable vs Inevitable")
    output_file.write("\n" + "-" * 80 + "\n")
    
    evit_c_plus = evitable_counts['total'].get('C+', 0)
    evit_c_minus = evitable_counts['total'].get('C-', 0)
    evit_c_total = evit_c_plus + evit_c_minus
    
    inev_c_plus = inevitable_counts['total'].get('C+', 0)
    inev_c_minus = inevitable_counts['total'].get('C-', 0)
    inev_c_total = inev_c_plus + inev_c_minus
    
    output_file.write(f"\nEvitable Scenarios:")
    output_file.write(f"\n  C+: {evit_c_plus:4d} ({100*evit_c_plus/evit_c_total if evit_c_total > 0 else 0:5.1f}%)")
    output_file.write(f"\n  C-: {evit_c_minus:4d} ({100*evit_c_minus/evit_c_total if evit_c_total > 0 else 0:5.1f}%)")
    output_file.write(f"\n  Total C assignments: {evit_c_total}")
    
    output_file.write(f"\n\nInevitable Scenarios:")
    output_file.write(f"\n  C+: {inev_c_plus:4d} ({100*inev_c_plus/inev_c_total if inev_c_total > 0 else 0:5.1f}%)")
    output_file.write(f"\n  C-: {inev_c_minus:4d} ({100*inev_c_minus/inev_c_total if inev_c_total > 0 else 0:5.1f}%)")
    output_file.write(f"\n  Total C assignments: {inev_c_total}")
    
    if evit_c_total > 0 and inev_c_total > 0:
        evit_c_plus_pct = 100 * evit_c_plus / evit_c_total
        inev_c_plus_pct = 100 * inev_c_plus / inev_c_total
        diff = abs(evit_c_plus_pct - inev_c_plus_pct)
        dominant_evitability = "Evitable" if evit_c_plus_pct > inev_c_plus_pct else "Inevitable"
        dominant_polarity = "C+" if evit_c_plus_pct > inev_c_plus_pct else "C-"
        
        output_file.write(f"\n\nInterpretation:")
        output_file.write(f"\n  {dominant_evitability} scenarios show {diff:.1f}% more {dominant_polarity} assignments")
        if diff > 10:
            output_file.write(f"\n  This suggests a STRONG systematic dominance of {dominant_polarity} in {dominant_evitability} scenarios")
        elif diff > 5:
            output_file.write(f"\n  This suggests a MODERATE systematic dominance of {dominant_polarity} in {dominant_evitability} scenarios")
        else:
            output_file.write(f"\n  The difference is SMALL, suggesting no strong systematic dominance")
    
    # Question 4: Polarity patterns by action type
    output_file.write("\n\n" + "-" * 80)
    output_file.write("\n3. POLARITY PATTERNS BY ACTION TYPE")
    output_file.write("\n" + "-" * 80 + "\n")
    
    output_file.write("\nAction_Yes Scenarios:")
    for var in ['C', 'I', 'K']:
        plus = action_yes_counts['total'].get(f'{var}+', 0)
        minus = action_yes_counts['total'].get(f'{var}-', 0)
        total = plus + minus
        if total > 0:
            output_file.write(f"\n  {var}+: {plus:4d} ({100*plus/total:5.1f}%)  |  {var}-: {minus:4d} ({100*minus/total:5.1f}%)")
    
    output_file.write("\n\nPrevention_No Scenarios:")
    for var in ['C', 'I', 'K']:
        plus = prevention_no_counts['total'].get(f'{var}+', 0)
        minus = prevention_no_counts['total'].get(f'{var}-', 0)
        total = plus + minus
        if total > 0:
            output_file.write(f"\n  {var}+: {plus:4d} ({100*plus/total:5.1f}%)  |  {var}-: {minus:4d} ({100*minus/total:5.1f}%)")
    
    output_file.write("\n\nDifferences (Action_Yes % - Prevention_No %):")
    distinguishing_features = []
    for var in ['C', 'I', 'K']:
        ay_plus = action_yes_counts['total'].get(f'{var}+', 0)
        ay_minus = action_yes_counts['total'].get(f'{var}-', 0)
        ay_total = ay_plus + ay_minus
        
        pn_plus = prevention_no_counts['total'].get(f'{var}+', 0)
        pn_minus = prevention_no_counts['total'].get(f'{var}-', 0)
        pn_total = pn_plus + pn_minus
        
        if ay_total > 0 and pn_total > 0:
            ay_plus_pct = 100 * ay_plus / ay_total
            pn_plus_pct = 100 * pn_plus / pn_total
            diff_plus = ay_plus_pct - pn_plus_pct
            diff_minus = -diff_plus  # Inverse for minus
            
            output_file.write(f"\n  {var}+: {diff_plus:+6.1f}%  |  {var}-: {diff_minus:+6.1f}%")
            
            if abs(diff_plus) > 10:
                distinguishing_features.append((var, diff_plus))
    
    output_file.write("\n\nInterpretation:")
    if distinguishing_features:
        output_file.write("\n  DISTINGUISHING FEATURES found:")
        for var, diff in distinguishing_features:
            if diff > 0:
                output_file.write(f"\n    - {var}+ is {abs(diff):.1f}% more common in Action_Yes scenarios")
            else:
                output_file.write(f"\n    - {var}- is {abs(diff):.1f}% more common in Action_Yes scenarios")
    else:
        output_file.write("\n  No strong distinguishing features found (all differences < 10%)")
    
    return subfolder_events  # Return for cross-severity analysis


def main():
    """Main analysis function."""
    
    base_path = Path("franken_annotated_outputs")
    output_filename = "moral_scenario_analysis_report.txt"
    
    if not base_path.exists():
        print(f"Error: Directory '{base_path}' not found!")
        return
    
    # Store events from both severity levels for cross-severity comparison
    severity_events = {}
    
    with open(output_filename, 'w') as output_file:
        # Write header
        output_file.write("=" * 80 + "\n")
        output_file.write("MORAL SCENARIO ANNOTATION ANALYSIS REPORT\n")
        output_file.write("=" * 80 + "\n")
        output_file.write(f"Analysis of causal variable polarities (C, I, K)\n")
        output_file.write(f"grouped by utility scores and experimental conditions\n")
        
        # Analyze each severity level
        for severity in ['conditions_mild_harm_mild_good', 'conditions_severe_harm_very_good']:
            severity_path = base_path / severity
            if severity_path.exists():
                events = analyze_directory(base_path, severity, output_file)
                severity_events[severity] = events
            else:
                output_file.write(f"\nWarning: {severity} directory not found!\n")
        
        # Cross-severity analysis: utility score ranges
        output_file.write("\n\n" + "#" * 80)
        output_file.write("\nCROSS-SEVERITY ANALYSIS: UTILITY SCORE DISTRIBUTIONS")
        output_file.write("\n" + "#" * 80 + "\n")
        
        for severity in ['conditions_mild_harm_mild_good', 'conditions_severe_harm_very_good']:
            if severity not in severity_events:
                continue
            
            output_file.write(f"\n\n{severity.upper().replace('_', ' ')}:")
            output_file.write("\n" + "-" * 80 + "\n")
            
            # Collect all utility scores
            all_utilities = []
            positive_utilities = []
            negative_utilities = []
            
            for subfolder_name, events in severity_events[severity].items():
                for causal_dict, utility in events:
                    all_utilities.append(utility)
                    if utility > 0:
                        positive_utilities.append(utility)
                    elif utility < 0:
                        negative_utilities.append(utility)
            
            if all_utilities:
                output_file.write(f"\nAll Utilities:")
                output_file.write(f"\n  Count: {len(all_utilities)}")
                output_file.write(f"\n  Range: [{min(all_utilities)}, {max(all_utilities)}]")
                output_file.write(f"\n  Mean: {sum(all_utilities)/len(all_utilities):.2f}")
                
                if positive_utilities:
                    output_file.write(f"\n\nPositive Utilities:")
                    output_file.write(f"\n  Count: {len(positive_utilities)}")
                    output_file.write(f"\n  Range: [{min(positive_utilities)}, {max(positive_utilities)}]")
                    output_file.write(f"\n  Mean: {sum(positive_utilities)/len(positive_utilities):.2f}")
                    
                    # Check extremity (how many are >= 80)
                    extreme_positive = sum(1 for u in positive_utilities if u >= 80)
                    output_file.write(f"\n  Extreme values (≥80): {extreme_positive} ({100*extreme_positive/len(positive_utilities):.1f}%)")
                
                if negative_utilities:
                    output_file.write(f"\n\nNegative Utilities:")
                    output_file.write(f"\n  Count: {len(negative_utilities)}")
                    output_file.write(f"\n  Range: [{min(negative_utilities)}, {max(negative_utilities)}]")
                    output_file.write(f"\n  Mean: {sum(negative_utilities)/len(negative_utilities):.2f}")
                    
                    # Check extremity (how many are <= -80)
                    extreme_negative = sum(1 for u in negative_utilities if u <= -80)
                    output_file.write(f"\n  Extreme values (≤-80): {extreme_negative} ({100*extreme_negative/len(negative_utilities):.1f}%)")
        
        # Comparison between severity levels
        if len(severity_events) == 2:
            output_file.write("\n\n" + "-" * 80)
            output_file.write("\nCOMPARISON: Mild vs Severe")
            output_file.write("\n" + "-" * 80 + "\n")
            
            mild_utils = []
            severe_utils = []
            
            for events in severity_events.get('conditions_mild_harm_mild_good', {}).values():
                mild_utils.extend([u for _, u in events])
            
            for events in severity_events.get('conditions_severe_harm_very_good', {}).values():
                severe_utils.extend([u for _, u in events])
            
            if mild_utils and severe_utils:
                mild_pos = [u for u in mild_utils if u > 0]
                severe_pos = [u for u in severe_utils if u > 0]
                mild_neg = [u for u in mild_utils if u < 0]
                severe_neg = [u for u in severe_utils if u < 0]
                
                output_file.write(f"\nPositive Utilities:")
                if mild_pos:
                    mild_extreme_pct = 100 * sum(1 for u in mild_pos if u >= 80) / len(mild_pos)
                    output_file.write(f"\n  Mild - Mean: {sum(mild_pos)/len(mild_pos):.2f}, Extreme (≥80): {mild_extreme_pct:.1f}%")
                if severe_pos:
                    severe_extreme_pct = 100 * sum(1 for u in severe_pos if u >= 80) / len(severe_pos)
                    output_file.write(f"\n  Severe - Mean: {sum(severe_pos)/len(severe_pos):.2f}, Extreme (≥80): {severe_extreme_pct:.1f}%")
                
                output_file.write(f"\n\nNegative Utilities:")
                if mild_neg:
                    mild_extreme_pct = 100 * sum(1 for u in mild_neg if u <= -80) / len(mild_neg)
                    output_file.write(f"\n  Mild - Mean: {sum(mild_neg)/len(mild_neg):.2f}, Extreme (≤-80): {mild_extreme_pct:.1f}%")
                if severe_neg:
                    severe_extreme_pct = 100 * sum(1 for u in severe_neg if u <= -80) / len(severe_neg)
                    output_file.write(f"\n  Severe - Mean: {sum(severe_neg)/len(severe_neg):.2f}, Extreme (≤-80): {severe_extreme_pct:.1f}%")
                
                # Interpretation
                output_file.write(f"\n\nInterpretation:")
                if severe_pos and mild_pos:
                    severe_mean = sum(severe_pos)/len(severe_pos)
                    mild_mean = sum(mild_pos)/len(mild_pos)
                    if severe_mean > mild_mean + 10:
                        output_file.write(f"\n  Severe scenarios show MORE EXTREME positive utilities (mean difference: {severe_mean - mild_mean:.1f})")
                    elif mild_mean > severe_mean + 10:
                        output_file.write(f"\n  Mild scenarios show MORE EXTREME positive utilities (mean difference: {mild_mean - severe_mean:.1f})")
                    else:
                        output_file.write(f"\n  Similar positive utility distributions between mild and severe")
                
                if severe_neg and mild_neg:
                    severe_mean = sum(severe_neg)/len(severe_neg)
                    mild_mean = sum(mild_neg)/len(mild_neg)
                    if severe_mean < mild_mean - 10:
                        output_file.write(f"\n  Severe scenarios show MORE EXTREME negative utilities (mean difference: {abs(severe_mean - mild_mean):.1f})")
                    elif mild_mean < severe_mean - 10:
                        output_file.write(f"\n  Mild scenarios show MORE EXTREME negative utilities (mean difference: {abs(mild_mean - severe_mean):.1f})")
                    else:
                        output_file.write(f"\n  Similar negative utility distributions between mild and severe")
    
    print(f"Analysis complete! Report saved to: {output_filename}")


if __name__ == "__main__":
    main()