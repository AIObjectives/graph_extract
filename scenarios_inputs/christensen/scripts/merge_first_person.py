#!/usr/bin/env python3
"""
Merge the four "*_first_person.json" scenario files under
scenarios_inputs/christensen into a single mega-list, in the fixed order:

    sb_ev -> sb_inev -> ob_ev -> ob_inev

Each source file's blocks have "id" values starting at 0. In the merged
output, "id" is renumbered sequentially from 0 across the whole mega-list
(so file 2, 3, 4's ids are offset by the running total).
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "christensen_first_person_all.json"

# Fixed merge order, keyed by the filename prefix.
ORDER = ["sb_ev", "sb_inev", "ob_ev", "ob_inev"]


def find_first_person_files():
    """Map each ORDER prefix to its "*_first_person.json" file path."""
    candidates = sorted(ROOT.rglob("*_first_person.json"))
    by_prefix = {}
    for path in candidates:
        prefix = next((p for p in ORDER if path.name.startswith(p + "_")), None)
        if prefix is None:
            raise ValueError(f"File does not match any known prefix {ORDER}: {path}")
        if prefix in by_prefix:
            raise ValueError(
                f"Multiple files match prefix '{prefix}': {by_prefix[prefix]} and {path}"
            )
        by_prefix[prefix] = path
    missing = [p for p in ORDER if p not in by_prefix]
    if missing:
        raise ValueError(f"Missing first_person file(s) for prefix(es): {missing}")
    return [by_prefix[p] for p in ORDER]


def main():
    files = find_first_person_files()

    merged = []
    next_id = 0
    for path in files:
        blocks = json.loads(path.read_text(encoding="utf-8"))
        for block in blocks:
            block["id"] = next_id
            next_id += 1
            merged.append(block)
        print(f"{path.relative_to(ROOT)}: {len(blocks)} block(s) added")

    OUTPUT_PATH.write_text(
        json.dumps(merged, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"\nWrote {len(merged)} total block(s) to {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
