"""
Reconstruct qualtrics_*.json files from annotated graph json files.

The graph json files don't contain the original scenario text, so the scenarios_inputs file path must be passed in explicitly; entries are matched to graph files by id == <n> in the filename.

Usage:
    python -m qualtrics_json_maker.py <annotator_outputs_dir> <scenarios_inputs_file>
Examples:
    1. python qualtrics_json_maker.py ../annotated_outputs/moral_comp_exp4/servicedog/ ../scenarios_inputs/moral_comp_exp4/servicedog.json
    2. python qualtrics_json_maker.py ../annotated_outputs/christensen/ ../scenarios_inputs/christensen/christensen_first_person_all_titled.json

Writes qualtrics_<family>_<n>_choice_<c>.json files into a sibling directory named qualtrics_<input_dir basename>.
"""

import argparse
import glob
import json
import os
import re

FNAME_RE = re.compile(r"_(?P<sid>\d+)_choice_(?P<cn>\d+)\.json$")


def read_graph_nodes(path):
    nodes = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if "node" in obj:
                nodes.append(obj)
    return nodes


def convert_one(graph_path, scenarios_by_id, out_dir):
    fname = os.path.basename(graph_path)
    m = FNAME_RE.search(fname)
    if not m:
        raise ValueError("filename doesn't match <...>_<n>_choice_<c>.json")

    sid = m.group("sid")

    nodes = read_graph_nodes(graph_path)
    if not nodes or nodes[0]["node"].get("kind") != "action_choice":
        raise ValueError("expected first node to be kind=action_choice")

    action_label = nodes[0]["node"]["label"]
    being_labels = [n["node"]["label"] for n in nodes if n["node"]["kind"] == "being"]
    event_labels = [n["node"]["label"] for n in nodes if n["node"]["kind"] == "event"]

    entry = scenarios_by_id.get(sid)
    if entry is None:
        raise KeyError(f"no scenario entry with id {sid} found in the scenarios file")

    qualtrics_obj = {
        "scenario": entry["text"],
        "scenario_idx": int(sid),
        "choice": "I decide to " + action_label,
        # graph labels are always lowercased on write, so original casing (e.g. "I" vs "i") can't be recovered here
        "entities": ",".join(being_labels),
        "outcomes": event_labels,
    }

    out_path = os.path.join(out_dir, "qualtrics_" + fname)
    with open(out_path, "w") as f:
        f.write(json.dumps([qualtrics_obj]))

    return out_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("annotator_outputs_dir", help="Directory containing <family>_<n>_choice_<c>.json graph files")
    parser.add_argument("scenarios_inputs_file", help="scenarios_inputs json file these graph files were generated from")
    args = parser.parse_args()

    input_dir = os.path.abspath(args.annotator_outputs_dir)
    parent_dir = os.path.dirname(input_dir)
    out_dir = os.path.join(parent_dir, "qualtrics_" + os.path.basename(input_dir))
    os.makedirs(out_dir, exist_ok=True)

    with open(args.scenarios_inputs_file) as f:
        scenarios_by_id = {str(e["id"]): e for e in json.load(f)}

    graph_files = sorted(
        f
        for f in glob.glob(os.path.join(input_dir, "*.json"))
        if not os.path.basename(f).startswith("qualtrics_")
    )
    if not graph_files:
        raise SystemExit(f"No graph json files found in {input_dir}")

    written, skipped = 0, 0
    for gf in graph_files:
        try:
            out_path = convert_one(gf, scenarios_by_id, out_dir)
            print(f"wrote {out_path}")
            written += 1
        except Exception as e:
            print(f"SKIP {gf}: {e}")
            skipped += 1

    print(f"\nDone. {written} written, {skipped} skipped. Output dir: {out_dir}")


if __name__ == "__main__":
    main()