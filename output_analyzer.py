import json
import os
from collections import defaultdict
from pathlib import Path

def extract_label(link_value, label_char):
    """
    Extract polarity for a specific label (C, I, or K) from a link value.
    
    Args:
        link_value: String like 'C+I+K+' or 'C-I-K+'
        label_char: Character to look for ('C', 'I', or 'K')
    
    Returns:
        '+' or '-' or None if label not found
    """
    if not link_value or not isinstance(link_value, str):
        return None
    
    # Find the label character in the string
    label_index = link_value.find(label_char)
    if label_index == -1 or label_index + 1 >= len(link_value):
        return None
    
    # Get the character immediately after the label
    polarity = link_value[label_index + 1]
    if polarity in ['+', '-']:
        return polarity
    return None

def parse_json_file(filepath):
    """
    Parse a JSON file and extract C, I, K labels from b-links.
    
    Returns:
        List of tuples: [(c_label, i_label, k_label), ...]
        where each label is '+' or '-' or None
    """
    labels = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # Read all lines (each line is a separate JSON object)
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    
                    # Check if this is the first node (being node with links)
                    if 'node' in data and 'links' in data:
                        node = data['node']
                        
                        # Only process if it's a 'being' node
                        if node.get('kind') == 'being':
                            links = data['links']
                            
                            # Extract C, I, K labels from b-links
                            for link_obj in links:
                                if 'link' in link_obj:
                                    link = link_obj['link']
                                    if link.get('kind') in ['b-link', 'b_link']:
                                        link_value = link.get('value', '')
                                        c_label = extract_label(link_value, 'C')
                                        i_label = extract_label(link_value, 'I')
                                        k_label = extract_label(link_value, 'K')
                                        
                                        if c_label:  # Only add if we found at least C
                                            labels.append((c_label, i_label, k_label))
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    
    return labels

def categorize_folder(folder_name):
    """
    Determine evitability and agency type from folder name.
    
    Returns:
        Tuple: (evitability, agency_type)
        evitability: 'evitable' or 'inevitable'
        agency_type: 'action' or 'prevention'
    """
    folder_lower = folder_name.lower()
    
    # Determine evitability
    if 'evitable' in folder_lower and 'inevitable' not in folder_lower:
        evitability = 'evitable'
    elif 'inevitable' in folder_lower:
        evitability = 'inevitable'
    else:
        return None, None
    
    # Determine agency type
    if 'action_yes' in folder_lower:
        agency_type = 'action'
    elif 'prevention_no' in folder_lower:
        agency_type = 'prevention'
    else:
        return evitability, None
    
    return evitability, agency_type

def analyze_causality_labels(base_path):
    """
    Main analysis function.
    
    Returns:
        Dictionary with analysis results for both C-alone and C×I analysis
    """
    base_path = Path(base_path)
    
    # Storage for C-alone analysis (by evitability)
    c_alone_results = {
        'evitable': defaultdict(lambda: {'C+': 0, 'C-': 0}),
        'inevitable': defaultdict(lambda: {'C+': 0, 'C-': 0})
    }
    
    # Storage for I-alone analysis (by agency type)
    i_alone_results = {
        'action': defaultdict(lambda: {'I+': 0, 'I-': 0}),
        'prevention': defaultdict(lambda: {'I+': 0, 'I-': 0})
    }
    
    # Storage for C×I joint analysis (by folder type)
    ci_joint_results = defaultdict(lambda: {
        'C+I+': 0, 'C+I-': 0, 'C-I+': 0, 'C-I-': 0,
        'C_only': 0, 'I_only': 0, 'neither': 0
    })
    
    # Target folders
    target_folders = [
        'cc_evitable_action_yes_stories',
        'cc_evitable_prevention_no_stories',
        'cc_inevitable_action_yes_stories',
        'cc_inevitable_prevention_no_stories'
    ]
    
    # Process each folder
    for folder_name in target_folders:
        folder_path = base_path / folder_name
        
        if not folder_path.exists():
            print(f"Warning: Folder not found: {folder_path}")
            continue
        
        evitability, agency_type = categorize_folder(folder_name)
        if not evitability:
            print(f"Warning: Could not categorize folder: {folder_name}")
            continue
        
        print(f"\nProcessing {folder_name}...")
        print(f"  Evitability: {evitability}, Agency: {agency_type}")
        
        # Find all JSON files
        json_files = list(folder_path.glob('*.json'))
        print(f"  Found {len(json_files)} JSON files")
        
        # Process each JSON file
        for json_file in json_files:
            label_tuples = parse_json_file(json_file)
            
            # Process each label tuple
            for c_label, i_label, k_label in label_tuples:
                # C-alone analysis
                if c_label:
                    if c_label == '+':
                        c_alone_results[evitability][folder_name]['C+'] += 1
                    elif c_label == '-':
                        c_alone_results[evitability][folder_name]['C-'] += 1
                
                # I-alone analysis
                if i_label and agency_type:
                    if i_label == '+':
                        i_alone_results[agency_type][folder_name]['I+'] += 1
                    elif i_label == '-':
                        i_alone_results[agency_type][folder_name]['I-'] += 1
                
                # C×I joint analysis
                if c_label and i_label:
                    combo_key = f"C{c_label}I{i_label}"
                    ci_joint_results[folder_name][combo_key] += 1
                elif c_label:
                    ci_joint_results[folder_name]['C_only'] += 1
                elif i_label:
                    ci_joint_results[folder_name]['I_only'] += 1
                else:
                    ci_joint_results[folder_name]['neither'] += 1
    
    return {
        'c_alone': c_alone_results,
        'i_alone': i_alone_results,
        'ci_joint': ci_joint_results
    }

def print_c_alone_analysis(results):
    """
    Print C-alone analysis: Does C track evitability?
    
    This analysis validates: Evitable → C+, Inevitable → C-
    """
    print("\n" + "="*80)
    print("ANALYSIS 1: C-ALONE (Causality tracks Evitability)")
    print("="*80)
    print("\nHypothesis: C should track whether the outcome is evitable")
    print("  - Evitable scenarios → C+ (agent causes the outcome)")
    print("  - Inevitable scenarios → C- (outcome happens regardless)")
    print("="*80)
    
    c_alone = results['c_alone']
    
    for evitability in ['evitable', 'inevitable']:
        print(f"\n{evitability.upper()} SCENARIOS:")
        print("-" * 80)
        
        category_total_plus = 0
        category_total_minus = 0
        
        for folder_name, counts in c_alone[evitability].items():
            c_plus = counts['C+']
            c_minus = counts['C-']
            total = c_plus + c_minus
            
            category_total_plus += c_plus
            category_total_minus += c_minus
            
            if total > 0:
                plus_pct = (c_plus / total) * 100
                minus_pct = (c_minus / total) * 100
            else:
                plus_pct = minus_pct = 0
            
            # Determine if this matches expectation
            if evitability == 'evitable':
                expected = "C+"
                matches = plus_pct > 50
            else:
                expected = "C-"
                matches = minus_pct > 50
            
            match_symbol = "✓" if matches else "✗"
            
            print(f"\n  {folder_name}:")
            print(f"    C+ count: {c_plus:4d} ({plus_pct:5.1f}%)")
            print(f"    C- count: {c_minus:4d} ({minus_pct:5.1f}%)")
            print(f"    Total:    {total:4d}")
            print(f"    Expected: {expected} dominates {match_symbol}")
        
        # Category totals
        category_total = category_total_plus + category_total_minus
        if category_total > 0:
            cat_plus_pct = (category_total_plus / category_total) * 100
            cat_minus_pct = (category_total_minus / category_total) * 100
        else:
            cat_plus_pct = cat_minus_pct = 0
        
        if evitability == 'evitable':
            matches = cat_plus_pct > 50
        else:
            matches = cat_minus_pct > 50
        
        match_symbol = "✓" if matches else "✗"
        
        print(f"\n  {evitability.upper()} AGGREGATE:")
        print(f"    C+ count: {category_total_plus:4d} ({cat_plus_pct:5.1f}%)")
        print(f"    C- count: {category_total_minus:4d} ({cat_minus_pct:5.1f}%)")
        print(f"    Total:    {category_total:4d}")
        print(f"    Validation: {match_symbol}")

def print_i_alone_analysis(results):
    """
    Print I-alone analysis: Does I track agency type?
    
    This analysis validates: action → I+, prevention → I-
    """
    print("\n\n" + "="*80)
    print("ANALYSIS 2: I-ALONE (Intent tracks Agency Type)")
    print("="*80)
    print("\nHypothesis: I should track whether the agent actively acts or passively allows")
    print("  - Action scenarios → I+ (agent actively does something)")
    print("  - Prevention scenarios → I- (agent passively allows something)")
    print("="*80)
    
    i_alone = results['i_alone']
    
    for agency_type in ['action', 'prevention']:
        if agency_type not in i_alone or not i_alone[agency_type]:
            continue
            
        print(f"\n{agency_type.upper()} SCENARIOS:")
        print("-" * 80)
        
        category_total_plus = 0
        category_total_minus = 0
        
        for folder_name, counts in i_alone[agency_type].items():
            i_plus = counts['I+']
            i_minus = counts['I-']
            total = i_plus + i_minus
            
            category_total_plus += i_plus
            category_total_minus += i_minus
            
            if total > 0:
                plus_pct = (i_plus / total) * 100
                minus_pct = (i_minus / total) * 100
            else:
                plus_pct = minus_pct = 0
            
            # Determine if this matches expectation
            if agency_type == 'action':
                expected = "I+"
                matches = plus_pct > 50
            else:
                expected = "I-"
                matches = minus_pct > 50
            
            match_symbol = "✓" if matches else "✗"
            
            print(f"\n  {folder_name}:")
            print(f"    I+ count: {i_plus:4d} ({plus_pct:5.1f}%)")
            print(f"    I- count: {i_minus:4d} ({minus_pct:5.1f}%)")
            print(f"    Total:    {total:4d}")
            print(f"    Expected: {expected} dominates {match_symbol}")
        
        # Category totals
        category_total = category_total_plus + category_total_minus
        if category_total > 0:
            cat_plus_pct = (category_total_plus / category_total) * 100
            cat_minus_pct = (category_total_minus / category_total) * 100
        else:
            cat_plus_pct = cat_minus_pct = 0
        
        if agency_type == 'action':
            matches = cat_plus_pct > 50
        else:
            matches = cat_minus_pct > 50
        
        match_symbol = "✓" if matches else "✗"
        
        print(f"\n  {agency_type.upper()} AGGREGATE:")
        print(f"    I+ count: {category_total_plus:4d} ({cat_plus_pct:5.1f}%)")
        print(f"    I- count: {category_total_minus:4d} ({cat_minus_pct:5.1f}%)")
        print(f"    Total:    {category_total:4d}")
        print(f"    Validation: {match_symbol}")

def print_ci_joint_analysis(results):
    """
    Print C×I joint analysis: Does the combination capture the full 2×2 structure?
    
    This analysis validates the expected mapping:
      evitable_action → C+I+
      evitable_prevention → C+I-
      inevitable_action → C-I+
      inevitable_prevention → C-I-
    """
    print("\n\n" + "="*80)
    print("ANALYSIS 3: C×I JOINT (Full 2×2 Causal Structure)")
    print("="*80)
    print("\nHypothesis: C×I combinations should map to the 4 folder types")
    print("  - evitable_action_yes → C+I+ (active causation)")
    print("  - evitable_prevention_no → C+I- (causation by omission)")
    print("  - inevitable_action_yes → C-I+ (futile action)")
    print("  - inevitable_prevention_no → C-I- (no causation, no action)")
    print("="*80)
    
    ci_joint = results['ci_joint']
    
    # Expected mappings
    expected_mapping = {
        'cc_evitable_action_yes_stories': 'C+I+',
        'cc_evitable_prevention_no_stories': 'C+I-',
        'cc_inevitable_action_yes_stories': 'C-I+',
        'cc_inevitable_prevention_no_stories': 'C-I-'
    }
    
    for folder_name in sorted(ci_joint.keys()):
        counts = ci_joint[folder_name]
        
        # Calculate total
        total = sum([counts['C+I+'], counts['C+I-'], counts['C-I+'], counts['C-I-']])
        
        if total == 0:
            continue
        
        print(f"\n{folder_name}:")
        print("-" * 80)
        
        # Show all combinations
        for combo in ['C+I+', 'C+I-', 'C-I+', 'C-I-']:
            count = counts[combo]
            pct = (count / total) * 100 if total > 0 else 0
            
            # Mark if this is the expected combination
            expected = expected_mapping.get(folder_name, '')
            if combo == expected:
                marker = f" ← EXPECTED ✓" if pct > 50 else f" ← EXPECTED ✗"
            else:
                marker = ""
            
            print(f"  {combo}: {count:4d} ({pct:5.1f}%){marker}")
        
        # Show incomplete labels (for debugging)
        incomplete = counts['C_only'] + counts['I_only'] + counts['neither']
        if incomplete > 0:
            print(f"  [Incomplete labels: {incomplete}]")
        
        # Validation check
        expected = expected_mapping.get(folder_name, '')
        if expected:
            expected_count = counts[expected]
            expected_pct = (expected_count / total) * 100 if total > 0 else 0
            
            if expected_pct > 50:
                print(f"  ✓ Validation: {expected} dominates ({expected_pct:.1f}%)")
            else:
                print(f"  ✗ Validation: {expected} does NOT dominate ({expected_pct:.1f}%)")

def print_summary(results):
    """
    Print overall summary and interpretation.
    """
    print("\n\n" + "="*80)
    print("SUMMARY & INTERPRETATION")
    print("="*80)
    
    c_alone = results['c_alone']
    i_alone = results['i_alone']
    
    # Calculate overall C statistics
    evitable_c_plus = sum(c['C+'] for c in c_alone['evitable'].values())
    evitable_c_minus = sum(c['C-'] for c in c_alone['evitable'].values())
    evitable_c_total = evitable_c_plus + evitable_c_minus
    
    inevitable_c_plus = sum(c['C+'] for c in c_alone['inevitable'].values())
    inevitable_c_minus = sum(c['C-'] for c in c_alone['inevitable'].values())
    inevitable_c_total = inevitable_c_plus + inevitable_c_minus
    
    print("\n1. C-ALONE FINDINGS:")
    if evitable_c_total > 0:
        evit_c_plus_pct = (evitable_c_plus / evitable_c_total) * 100
        print(f"   Evitable scenarios: {evit_c_plus_pct:.1f}% are C+ (expected: >50%)")
    if inevitable_c_total > 0:
        inevit_c_minus_pct = (inevitable_c_minus / inevitable_c_total) * 100
        print(f"   Inevitable scenarios: {inevit_c_minus_pct:.1f}% are C- (expected: >50%)")
    
    # Calculate overall I statistics
    action_i_plus = sum(c['I+'] for c in i_alone.get('action', {}).values())
    action_i_minus = sum(c['I-'] for c in i_alone.get('action', {}).values())
    action_i_total = action_i_plus + action_i_minus
    
    prevention_i_plus = sum(c['I+'] for c in i_alone.get('prevention', {}).values())
    prevention_i_minus = sum(c['I-'] for c in i_alone.get('prevention', {}).values())
    prevention_i_total = prevention_i_plus + prevention_i_minus
    
    print("\n2. I-ALONE FINDINGS:")
    if action_i_total > 0:
        action_i_plus_pct = (action_i_plus / action_i_total) * 100
        print(f"   Action scenarios: {action_i_plus_pct:.1f}% are I+ (expected: >50%)")
    if prevention_i_total > 0:
        prevent_i_minus_pct = (prevention_i_minus / prevention_i_total) * 100
        print(f"   Prevention scenarios: {prevent_i_minus_pct:.1f}% are I- (expected: >50%)")
    
    # print("\n3. INTERPRETATION:")
    # print("   - C captures COUNTERFACTUAL CAUSALITY (difference-making)")
    # print("   - I captures AGENCY TYPE (active doing vs. passive allowing)")
    # print("   - C×I together capture the full 2×2 moral structure")
    # print("   - High validation = annotators understand causal structure")
    # print("   - Low validation = need to clarify annotation guidelines")
    
    print("\n" + "="*80 + "\n")

def print_results(results):
    """
    Master function to print all analyses.
    """
    print_c_alone_analysis(results)
    print_i_alone_analysis(results)
    print_ci_joint_analysis(results)
    print_summary(results)

# Main execution
if __name__ == "__main__":
    # Set your base path here
    # base_path = "franken_annotated_outputs/conditions_mild_harm_mild_good"
    base_path = "franken_annotated_outputs/conditions_severe_harm_very_good"
    
    print("="*80)
    print("CAUSALITY LABEL VALIDATION SCRIPT")
    print("="*80)
    print(f"\nBase path: {base_path}")
    print("\nThis script performs three analyses:")
    print("  1. C-ALONE: Does C track evitability? (evitable→C+, inevitable→C-)")
    print("  2. I-ALONE: Does I track agency type? (action→I+, prevention→I-)")
    print("  3. C×I JOINT: Do combinations map to the 4 folder types?")
    print("\n" + "="*80)
    
    results = analyze_causality_labels(base_path)
    print_results(results)