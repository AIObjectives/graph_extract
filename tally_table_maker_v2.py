#!/usr/bin/env python3
"""
Generate comprehensive table of scenario data with ground truth labels
and calculated C+/I+ percentages for each choice.
"""

import json
from pathlib import Path
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


def extract_event_data(json_file: Path) -> tuple[List[Tuple[Dict[str, str], int]], bool]:
    """
    Extract causal polarities and utility scores for each event.
    Returns (events_list, has_valid_data) where has_valid_data indicates if file should be included.
    """
    try:
        with open(json_file, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"  ERROR reading {json_file}: {e}")
        return [], False
    
    nodes = [json.loads(line) for line in lines]
    
    i_being_node = None
    non_i_being = None
    
    for node in nodes:
        if node['node']['kind'] == 'being':
            if node['node']['label'] == 'I':
                i_being_node = node
            else:
                non_i_being = node['node']['label']
    
    if not i_being_node:
        print(f"  WARNING: No I-being found in {json_file.name} - SKIPPING")
        return [], False
    
    if not non_i_being:
        print(f"  WARNING: No non-I being found in {json_file.name} - SKIPPING")
        return [], False
    
    event_causals = {}
    for link_obj in i_being_node['links']:
        link = link_obj['link']
        if link['kind'] == 'b_link':
            event_label = link_obj['to_node']
            causal_dict = parse_causal_string(link['value'])
            event_causals[event_label] = causal_dict
    
    results = []
    has_negative_utility = False
    
    for node in nodes:
        if node['node']['kind'] == 'event':
            event_label = node['node']['label']
            
            if event_label not in event_causals:
                continue
            
            for link_obj in node['links']:
                link = link_obj['link']
                if link['kind'] == 'utility' and link_obj['to_node'] == non_i_being:
                    utility = int(link['value'])
                    
                    # Check if there's at least one negative utility event
                    if utility < 0:
                        has_negative_utility = True
                    
                    # Apply filter if enabled
                    if EXCLUDE_NON_NEGATIVE_UTILITY and utility >= 0:
                        break  # Skip this event
                    
                    results.append((event_causals[event_label], utility))
                    break
    
    # If filtering is enabled, we need at least one negative utility event
    if EXCLUDE_NON_NEGATIVE_UTILITY and not has_negative_utility:
        print(f"  WARNING: {json_file.name} - No negative utility events found - SKIPPING")
        return [], False
    
    # If filtering is disabled, we need at least some events
    if not EXCLUDE_NON_NEGATIVE_UTILITY and len(results) == 0:
        print(f"  WARNING: {json_file.name} - No events with utility links found - SKIPPING")
        return [], False
    
    # File is valid and has usable events
    return results, True


def calculate_percentages(events: List[Tuple[Dict[str, str], int]]) -> Dict[str, float]:
    """Calculate C+ and I+ percentages."""
    if not events:
        return {'c_plus_pct': 0.0, 'i_plus_pct': 0.0, 'num_events': 0}
    
    c_plus = sum(1 for causal_dict, _ in events if causal_dict.get('C') == '+')
    c_minus = sum(1 for causal_dict, _ in events if causal_dict.get('C') == '-')
    i_plus = sum(1 for causal_dict, _ in events if causal_dict.get('I') == '+')
    i_minus = sum(1 for causal_dict, _ in events if causal_dict.get('I') == '-')
    
    c_total = c_plus + c_minus
    i_total = i_plus + i_minus
    
    return {
        'c_plus_pct': (c_plus / c_total * 100) if c_total > 0 else 0.0,
        'i_plus_pct': (i_plus / i_total * 100) if i_total > 0 else 0.0,
        'num_events': len(events)
    }


def extract_condition_properties(condition_name: str) -> Dict[str, str]:
    """Extract evitability and causal structure from condition name."""
    parts = condition_name.split('_')
    causal = parts[0].upper()  # CC or COC
    evitability = parts[1].capitalize()  # Evitable or Inevitable
    
    return {
        'causal': causal,
        'evitability': evitability
    }


def collect_scenario_data(base_path: Path) -> List[Dict]:
    """Collect all scenario data with ground truth labels."""
    all_rows = []
    table_row_id = 1
    skipped_count = 0
    
    # Process both severity levels
    for severity_folder in ['conditions_mild_harm_mild_good', 'conditions_severe_harm_very_good']:
        severity_path = base_path / severity_folder
        
        if not severity_path.exists():
            continue
        
        # Determine severity label
        if 'mild' in severity_folder.lower():
            severity = 'Mild'
        else:
            severity = 'Severe'
        
        # Process each condition subfolder
        for subfolder in sorted(severity_path.iterdir()):
            if not subfolder.is_dir():
                continue
            
            condition_name = subfolder.name
            props = extract_condition_properties(condition_name)
            
            # Group files by scenario ID
            scenario_files = {}
            for json_file in subfolder.glob("*.json"):
                parts = json_file.stem.split('_choice_')
                if len(parts) != 2:
                    continue
                
                scenario_id = int(parts[0])
                choice_num = int(parts[1])
                
                if scenario_id not in scenario_files:
                    scenario_files[scenario_id] = {}
                
                scenario_files[scenario_id][choice_num] = json_file
            
            # Process each scenario
            for scenario_id in sorted(scenario_files.keys()):
                choices = scenario_files[scenario_id]
                
                # Process both choices (should be 1 and 2)
                for choice_num in sorted(choices.keys()):
                    json_file = choices[choice_num]
                    events, is_valid = extract_event_data(json_file)
                    
                    # Skip if file doesn't have valid structure (Option C)
                    if not is_valid:
                        skipped_count += 1
                        continue
                    
                    percentages = calculate_percentages(events)
                    
                    all_rows.append({
                        'table_id': table_row_id,
                        'original_scenario_id': scenario_id,
                        'severity': severity,
                        'evitability': props['evitability'],
                        'causal': props['causal'],
                        'choice': choice_num,
                        'c_plus_pct': percentages['c_plus_pct'],
                        'i_plus_pct': percentages['i_plus_pct'],
                        'num_events': percentages['num_events'],
                        'condition': condition_name
                    })
                    
                    table_row_id += 1
    
    if skipped_count > 0:
        print(f"\nSkipped {skipped_count} files due to missing non-I being or no valid events\n")
    
    return all_rows


def write_table(rows: List[Dict], output_file: Path):
    """Write data to formatted text table."""
    
    with open(output_file, 'w') as f:
        # Write header
        f.write("=" * 120 + "\n")
        f.write("SCENARIO DATA TABLE\n")
        f.write("=" * 120 + "\n")
        f.write(f"Filter non-negative utility events: {EXCLUDE_NON_NEGATIVE_UTILITY}\n")
        f.write(f"Total rows: {len(rows)}\n")
        f.write("=" * 120 + "\n\n")
        
        # Column headers
        header = (
            f"{'ID':>4} | "
            f"{'Orig ID':>7} | "
            f"{'Severity':>8} | "
            f"{'Evitability':>11} | "
            f"{'Causal':>6} | "
            f"{'Choice':>6} | "
            f"{'C+ %':>7} | "
            f"{'I+ %':>7} | "
            f"{'N Events':>8} | "
            f"{'Condition'}"
        )
        f.write(header + "\n")
        f.write("-" * 120 + "\n")
        
        # Data rows
        for row in rows:
            line = (
                f"{row['table_id']:>4} | "
                f"{row['original_scenario_id']:>7} | "
                f"{row['severity']:>8} | "
                f"{row['evitability']:>11} | "
                f"{row['causal']:>6} | "
                f"{row['choice']:>6} | "
                f"{row['c_plus_pct']:>7.2f} | "
                f"{row['i_plus_pct']:>7.2f} | "
                f"{row['num_events']:>8} | "
                f"{row['condition']}"
            )
            f.write(line + "\n")
        
        # Summary statistics
        f.write("\n" + "=" * 120 + "\n")
        f.write("SUMMARY STATISTICS\n")
        f.write("=" * 120 + "\n\n")
        
        # Count by severity
        mild_count = sum(1 for r in rows if r['severity'] == 'Mild')
        severe_count = sum(1 for r in rows if r['severity'] == 'Severe')
        f.write(f"Mild scenarios: {mild_count} rows\n")
        f.write(f"Severe scenarios: {severe_count} rows\n\n")
        
        # Count by evitability
        evitable_count = sum(1 for r in rows if r['evitability'] == 'Evitable')
        inevitable_count = sum(1 for r in rows if r['evitability'] == 'Inevitable')
        f.write(f"Evitable: {evitable_count} rows\n")
        f.write(f"Inevitable: {inevitable_count} rows\n\n")
        
        # Count by causal structure
        cc_count = sum(1 for r in rows if r['causal'] == 'CC')
        coc_count = sum(1 for r in rows if r['causal'] == 'COC')
        f.write(f"CC: {cc_count} rows\n")
        f.write(f"COC: {coc_count} rows\n\n")
        
        # Count by choice
        choice1_count = sum(1 for r in rows if r['choice'] == 1)
        choice2_count = sum(1 for r in rows if r['choice'] == 2)
        f.write(f"Choice 1: {choice1_count} rows\n")
        f.write(f"Choice 2: {choice2_count} rows\n\n")
        
        # Average percentages
        avg_c = sum(r['c_plus_pct'] for r in rows) / len(rows) if rows else 0
        avg_i = sum(r['i_plus_pct'] for r in rows) / len(rows) if rows else 0
        f.write(f"Average C+ %: {avg_c:.2f}\n")
        f.write(f"Average I+ %: {avg_i:.2f}\n\n")
        
        # Average events per row
        avg_events = sum(r['num_events'] for r in rows) / len(rows) if rows else 0
        f.write(f"Average events per choice: {avg_events:.2f}\n")


def write_csv(rows: List[Dict], output_file: Path):
    """Write data to CSV format for easy import into other tools."""
    
    with open(output_file, 'w') as f:
        # Header
        f.write("table_id,original_scenario_id,severity,evitability,causal,choice,c_plus_pct,i_plus_pct,num_events,condition\n")
        
        # Data
        for row in rows:
            f.write(
                f"{row['table_id']},"
                f"{row['original_scenario_id']},"
                f"{row['severity']},"
                f"{row['evitability']},"
                f"{row['causal']},"
                f"{row['choice']},"
                f"{row['c_plus_pct']:.2f},"
                f"{row['i_plus_pct']:.2f},"
                f"{row['num_events']},"
                f"{row['condition']}\n"
            )


def main():
    """Main function."""
    
    base_path = Path("franken_annotated_outputs")
    output_dir = Path("table_outputs_v2_onlynegative_utility" if EXCLUDE_NON_NEGATIVE_UTILITY else "table_outputs_v2_all_events")
    
    output_dir.mkdir(exist_ok=True)
    
    if not base_path.exists():
        print(f"Error: Directory '{base_path}' not found!")
        return
    
    print("\n" + "=" * 80)
    print("SCENARIO DATA TABLE GENERATOR")
    print("=" * 80)
    print(f"\nFilter non-negative utility: {EXCLUDE_NON_NEGATIVE_UTILITY}")
    print("\nCollecting scenario data...\n")
    
    # Collect all data
    rows = collect_scenario_data(base_path)
    
    print(f"Collected {len(rows)} rows of data")
    print(f"  - {len(set(r['original_scenario_id'] for r in rows))} unique scenarios")
    print(f"  - Each scenario has 2 choices (rows)")
    
    # Write outputs
    txt_file = output_dir / "scenario_data_table.txt"
    csv_file = output_dir / "scenario_data_table.csv"
    
    write_table(rows, txt_file)
    write_csv(rows, csv_file)
    
    print(f"\n✓ Text table saved to: {txt_file}")
    print(f"✓ CSV file saved to: {csv_file}")
    
    print("\n" + "=" * 80)
    print("TABLE GENERATION COMPLETE!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()