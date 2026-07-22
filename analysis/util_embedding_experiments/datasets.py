"""Simple loaders for every dataset used in the util embedding experiments.
Each function returns plain pandas DataFrame(s) - no embedding, no filtering to specific
subsets, just tidy access to what's on disk. Run as a script to sanity-check all of them.
"""
import csv, glob, json, re
from collections import defaultdict
from pathlib import Path
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
HD = REPO / "human_data"
SI = REPO / "scenarios_inputs"


def load_ethics() -> dict:
    """{category: {split: DataFrame}} for all 5 ETHICS categories."""
    root = HD / "ethics"
    out = {}
    for cat, splits, cols in [
        ("utilitarianism", ["train", "test", "test_hard"], ["more_pleasant", "less_pleasant"]),
        ("commonsense", ["train", "test", "test_hard"], None),
        ("deontology", ["train", "test", "test_hard"], None),
        ("justice", ["train", "test", "test_hard"], None),
        ("virtue", ["train", "test", "test_hard"], None),
    ]:
        prefix = {"utilitarianism": "util", "commonsense": "cm", "deontology": "deontology",
                  "justice": "justice", "virtue": "virtue"}[cat]
        out[cat] = {}
        for split in splits:
            p = root / cat / f"{prefix}_{split}.csv"
            if cols:  # utilitarianism has no header
                out[cat][split] = pd.read_csv(p, header=None, names=cols)
            else:
                out[cat][split] = pd.read_csv(p)
    # cm_ambig.csv is a special case: no label, single free-text column, no header
    out["commonsense"]["ambig"] = pd.read_csv(root / "commonsense" / "cm_ambig.csv", header=None, names=["text"])
    return out


def load_holmes_rahe() -> pd.DataFrame:
    return pd.read_csv(HD / "holmes_rahe" / "holmes_rahe.csv")


def load_gbd() -> pd.DataFrame:
    return pd.read_csv(HD / "gbd" / "gbd2013_clean.csv")


<<<<<<< HEAD
=======
def load_virtue_words() -> dict:
    """{system: (good_df, bad_df)} good vs bad virtue-word lists (cols: word, definition).
    Each virtue system contrasts a set of virtue words against its anti-value words
    (for aristotle, the two vices - deficiency and excess - are pooled as 'bad')."""
    VW = HD / "virtue_words"
    read = lambda name: pd.read_csv(VW / f"{name}.csv", header=None, names=["word", "definition"])
    return {
        "aristotle": (read("aristotle_virtues"),
                      pd.concat([read("aristotle_deficiency"), read("aristotle_excess")], ignore_index=True)),
        "seligman_1": (read("seligman_values_1"), read("seligman_anti_values_1")),
        "seligman_2": (read("seligman_values_2"), read("seligman_anti_values_2")),
    }


def load_dillion() -> pd.DataFrame:
    """463 situations with a continuous human moral rating (Dillion 2023 compilation)."""
    return pd.read_csv(HD / "dillion" / "dillion_2023.csv")


def load_seong() -> pd.DataFrame:
    """Moral-judgment sentences (Seong): item, morality_level (1=moral, 2=neutral, 3=immoral),
    syntax_level (1=natural, 2-4=degraded grammar)."""
    return pd.read_csv(HD / "seong" / "seong_68.csv")


>>>>>>> v4
def load_franken() -> tuple:
    """(exp1_df, exp2_df): harm-vs-good rating, permissibility/intention rating."""
    exp1 = pd.DataFrame(json.load(open(HD / "franken" / "exp1_harm-vs-good-rating" / "exp1_unique_stimuli.json")))

    E2 = HD / "franken" / "exp2_moralperm-intent-rating"
    stim = {}
    for f in sorted(glob.glob(str(E2 / "batch_*.json"))):
        for x in json.load(open(f)):
            key = (x["scenario_id"], x["condition"])
            if key in stim:
                continue
            text = " ".join(s for s in [x.get("context"), x.get("opportunity"),
                                         x.get("structure_sentence"), x.get("evitability_sentence"),
                                         x.get("action_sentence")] if s and s.strip())
            parts = x["condition"].split("_")
            stim[key] = dict(scenario_id=x["scenario_id"], condition=x["condition"], text=text,
                              causal_structure=0 if parts[0] == "cc" else 1,
                              action=0 if parts[2] == "action" else 1,
                              evitability=1 if parts[1] == "inevitable" else 0)

    ratings = defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open(E2 / "data_long_format.csv")):
        key = (int(r["scenario_id"]), int(r["causal_structure"]), int(r["action"]), int(r["evitability"]))
        for m in ("permissibility_rating", "intention_rating"):
            try:
                ratings[key][m].append(float(r[m]))
            except (KeyError, ValueError):
                pass

    rows = []
    for s in stim.values():
        key = (s["scenario_id"], s["causal_structure"], s["action"], s["evitability"])
        r = ratings.get(key)
        if not r:
            continue
        rows.append({**s,
                     "avg_permissibility_rating": sum(r["permissibility_rating"]) / len(r["permissibility_rating"]),
                     "avg_intention_rating": sum(r["intention_rating"]) / len(r["intention_rating"]),
                     "n_ratings": len(r["permissibility_rating"])})
    exp2 = pd.DataFrame(rows)
    return exp1, exp2


def load_nie() -> pd.DataFrame:
    """acceptability (P(Yes)) + 4 design factors, per scenario."""
    scen = {s["id"]: s for s in json.load(open(SI / "nie" / "nie_scenarios.json"))}
    pyes = {}
    for f in glob.glob(str(SI / "nie" / "source" / "story_*.txt")):
        sid = int(re.search(r"story_(\d+)", f).group(1))
        m = re.search(r"P\(Yes\), P\(No\):\s*\[([\d.]+)", open(f).read())
        if m:
            pyes[sid] = float(m.group(1))
    fac = lambda i, key: scen[i].get("factors", {}).get("1", {}).get(key)
    rows = []
    for i in scen:
        if i not in pyes:
            continue
        rows.append(dict(id=i, text=scen[i]["text"], p_yes=pyes[i],
                          causal_role=fac(i, "Causal Role"), personal_force=fac(i, "Personal Force"),
                          evitability=fac(i, "Evitability"), beneficiary=fac(i, "Beneficiary")))
    return pd.DataFrame(rows)


def load_aita() -> pd.DataFrame:
    """Per-outcome: utility (-100..100) + likelihood + Cause/Intend/Expect ratings."""
    rec = defaultdict(dict)
    A = HD / "AITA"
    for f in glob.glob(str(A / "*_outcomes.csv")):
        for r in csv.DictReader(open(f)):
            if r.get("outcome"):
                rec[r["outcome"]]["likelihood"] = float(r["mean"])
    for f in glob.glob(str(A / "*_outcome_utilities.csv")):
        for r in csv.DictReader(open(f)):
            if r.get("outcome"):
                try:
                    rec[r["outcome"]].setdefault("_u", []).append(float(r["subj_means"]))
                except ValueError:
                    pass
    for f in glob.glob(str(A / "*_outcome_links.csv")):
        for r in csv.DictReader(open(f)):
            if r.get("outcome_name") and r.get("link_type") in ("Cause", "Intend", "Expect"):
                try:
                    rec[r["outcome_name"]][r["link_type"]] = float(r["subj_mean"])
                except ValueError:
                    pass
    rows = []
    for outcome, d in rec.items():
        if "_u" not in d:
            continue
        utility = sum(d["_u"]) / len(d["_u"])
        rows.append(dict(outcome=outcome, utility=utility, likelihood=d.get("likelihood"),
                          cause=d.get("Cause"), intend=d.get("Intend"), expect=d.get("Expect")))
    return pd.DataFrame(rows)