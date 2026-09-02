#!/usr/bin/env python3
"""
Walk all JSON files under scenarios_inputs/christensen and, in every scenario
block's "options" dict, replace the "2" sub-key's value from null to the
string "do nothing" (only when it is currently null).
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def fix_options(obj):
    """Recursively find "options" dicts with a null "2" key and fix them."""
    changed = 0
    if isinstance(obj, dict):
        if "options" in obj and isinstance(obj["options"], dict):
            options = obj["options"]
            if "2" in options and options["2"] is None:
                options["2"] = "do nothing"
                changed += 1
        for value in obj.values():
            changed += fix_options(value)
    elif isinstance(obj, list):
        for item in obj:
            changed += fix_options(item)
    return changed


def main():
    json_files = sorted(ROOT.rglob("*.json"))
    total_changed = 0
    for path in json_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        changed = fix_options(data)
        if changed:
            path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        print(f"{path.relative_to(ROOT)}: {changed} option(s) updated")
        total_changed += changed
    print(f"\nTotal: {total_changed} option(s) updated across {len(json_files)} file(s)")


if __name__ == "__main__":
    main()
