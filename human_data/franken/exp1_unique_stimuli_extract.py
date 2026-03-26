import csv
import json
import ast
import sys
from pathlib import Path

# Fields to exclude when checking uniqueness (human ratings)
EXCLUDE_FIELDS = {"likertResponses"}
# Columns to skip entirely
SKIP_COLUMNS = {"workerid", "proliferate.condition", "error"}


def normalize_trial(raw: str) -> dict | None:
    """Parse a trial JSON string, returning the full dict including ratings."""
    if not raw or not raw.strip():
        return None
    try:
        d = ast.literal_eval(raw)  # handles single-quoted dicts from Python reprs
    except Exception:
        try:
            d = json.loads(raw)
        except Exception:
            return None
    if not isinstance(d, dict):
        return None
    return d


def make_key(d: dict) -> str:
    """Stable hashable key from a dict (sorted keys, JSON serialized)."""
    return json.dumps(d, sort_keys=True, ensure_ascii=False)


def extract_likert_ratings(raw_trial: dict) -> list[float]:
    """Pull all numeric likert values out of a trial's likertResponses."""
    ratings = []
    likert = raw_trial.get("likertResponses", {})
    if isinstance(likert, dict):
        for v in likert.values():
            try:
                ratings.append(float(v))
            except (TypeError, ValueError):
                pass
    return ratings


def extract_unique_stimuli(input_path: str, output_path: str) -> None:
    seen: dict[str, dict] = {}       # key -> stimulus dict
    ratings: dict[str, list[float]] = {}  # key -> all collected likert values

    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for col, value in row.items():
                if col in SKIP_COLUMNS:
                    continue
                if not col.startswith("trial"):
                    continue
                # Parse the full trial (including likertResponses)
                raw = normalize_trial(value)  # normalize_trial strips nothing here
                if raw is None:
                    continue

                # Build the stimulus (no ratings) for dedup key
                stimulus = {k: v for k, v in raw.items() if k not in EXCLUDE_FIELDS}
                key = make_key(stimulus)

                if key not in seen:
                    seen[key] = stimulus
                    ratings[key] = []

                ratings[key].extend(extract_likert_ratings(raw))

    stimuli_list = []
    for key, stimulus in seen.items():
        r = ratings[key]
        stimulus["avg_likert_rating"] = round(sum(r) / len(r), 4) if r else None
        stimulus["n_likert_ratings"] = len(r)
        # skip the "scenario_id" field if it exists, since it's not meaningful for uniqueness
        if "scenario_id" in stimulus:
            del stimulus["scenario_id"]
        stimuli_list.append(stimulus)


    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(stimuli_list, f, indent=2, ensure_ascii=False)

    print(f"Done. {len(stimuli_list)} unique stimuli written to: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_unique_stimuli.py <input.csv> [output.json]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "unique_stimuli.json"

    if not Path(input_path).exists():
        print(f"Error: file not found: {input_path}")
        sys.exit(1)

    extract_unique_stimuli(input_path, output_path)