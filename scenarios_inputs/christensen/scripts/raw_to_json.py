#!/usr/bin/env python3
"""
Convert scenario .txt files into structured .json files.

Usage:
    python convert_scenarios.py path/to/file1.txt path/to/file2.txt ...
"""

import json
import os
import re
import sys


def parse_filename(txt_path):
    """Extract beneficial_to and evitability from the filename."""
    base = os.path.basename(txt_path)
    name, _ = os.path.splitext(base)
    parts = name.split("_")

    if len(parts) < 3:
        raise ValueError(
            f"Filename '{base}' does not match the expected "
            "'<ben>_<evit>_scenarios' pattern."
        )

    ben_token, evit_token = parts[0].lower(), parts[1].lower()

    ben_map = {"ob": "other", "sb": "self"}
    evit_map = {"ev": "evitable", "inev": "inevitable"}

    if ben_token not in ben_map:
        raise ValueError(f"Unrecognized beneficial token '{ben_token}' in '{base}'.")
    if evit_token not in evit_map:
        raise ValueError(f"Unrecognized evitability token '{evit_token}' in '{base}'.")

    return ben_map[ben_token], evit_map[evit_token]


def parse_line0(line0):
    """Extract personal_force and intentionality from the header line."""
    if ")" not in line0:
        raise ValueError(f"Expected a scenario header line containing ')': {line0!r}")

    lower = line0.lower()

    if "impersonal" in lower:
        personal_force = "impersonal"
    elif "personal" in lower:
        personal_force = "personal"
    else:
        raise ValueError(f"Could not find 'personal'/'impersonal' in line: {line0!r}")

    if "accidental" in lower:
        intentionality = "side_effect"
    elif "instrumental" in lower:
        intentionality = "means"
    else:
        raise ValueError(f"Could not find 'accidental'/'instrumental' in line: {line0!r}")

    return personal_force, intentionality


def parse_option_1(line3):
    """Extract the option-1 text from the question line (before the comma)."""
    if "," not in line3:
        raise ValueError(f"Expected a comma in line3: {line3!r}")

    before_comma = line3.split(",", 1)[0]
    cleaned = re.sub(r"^\s*do you\s+", "", before_comma, flags=re.IGNORECASE)
    return cleaned.strip()


def group_lines(lines):
    """Filter out blank lines and group the remainder into 4-line chunks."""
    non_empty = [ln.strip() for ln in lines if ln.strip()]

    if len(non_empty) % 4 != 0:
        raise ValueError(
            f"Expected a multiple of 4 non-empty lines, got {len(non_empty)}. "
            "Check the file formatting for a malformed or partial scenario."
        )

    return [non_empty[i:i + 4] for i in range(0, len(non_empty), 4)]


def convert_file(txt_path):
    beneficial_to, evitability = parse_filename(txt_path)

    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    scenarios = []
    for i, (line0, line1, line2, line3) in enumerate(group_lines(lines)):
        personal_force, intentionality = parse_line0(line0)
        option_1 = parse_option_1(line3)

        scenarios.append({
            "id": i,
            "beneficial_to": beneficial_to,
            "evitability": evitability,
            "personal_force": personal_force,
            "intentionality": intentionality,
            "text": f"{line1} {line2}",
            "options": {
                "1": option_1,
                "2": None,
            },
        })

    out_path = os.path.splitext(txt_path)[0] + ".json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(scenarios, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(scenarios)} scenarios to {out_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_scenarios.py file1.txt [file2.txt ...]")
        sys.exit(1)

    for txt_path in sys.argv[1:]:
        convert_file(txt_path)


if __name__ == "__main__":
    main()