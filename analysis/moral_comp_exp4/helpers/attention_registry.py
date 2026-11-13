"""
Attention-check answers for moral_comp_exp4 human surveys.

build_answers() returns the {ImportId: rule} dict that clean_human_survey.clean_survey()
expects. It combines the fixed answers in this file with the outcome bank text file.
"""
import re
import unicodedata
from pathlib import Path

import pandas as pd

BANK_PATH = Path(__file__).with_name("attention_checks.txt")

# ---- Raw filename -> which survey this is ----
STEM_PATTERN = re.compile(
    r"(?P<scenario>[a-z_]+)_utility(?P<util>\d+)_deontology(?P<deon>\d+)_choice(?P<choice>\d+)",
    re.IGNORECASE,
)

def parse_stem(name):
    """'utility+-+brother_utility1_deontology3_choice1_Nov...' -> dict, or None if not a survey file."""
    m = STEM_PATTERN.search(name)
    if m is None:
        return None
    return {"scenario": m["scenario"].lower(), "util": int(m["util"]),
            "deon": int(m["deon"]), "choice": int(m["choice"])}

def stem_name(survey):
    return (f"{survey['scenario']}_utility{survey['util']}"
            f"_deontology{survey['deon']}_choice{survey['choice']}")

def variant_id(util, deon):
    """Scenario JSON layout: ids 1-3 = utility 3, 4-6 = utility 2, 7-9 = utility 1."""
    return (3 - util) * 3 + deon

# ---- Answers that are the same in every survey ----
CIK_ANSWER = "knew/intend/cause"
ANCHORS = [   # 1st anchor check (after outcome 3), 2nd anchor check (after outcome 6)
    "-100 is equal to very painful death(s) for the character/group.",
    "+100 is equal to perfect peace and happiness for the character/group.",
]

def _num(s):
    return pd.to_numeric(s, errors="coerce")

BOMB = lambda s: _num(s) != -100      # overall utility slider: anything except -100
TROLLEY = lambda s: _num(s) == -100   # character utility slider: exactly -100

# ---- Q0 comprehension check (once per survey, first check) ----
Q0_LEVEL = {   # which manipulation the Q0 answer depends on
    "brother": "util", "bully": "util", "giftcard": "util", "lifeboat_number": "util",
    "medication": "util", "robinhood": "util", "ropeladder": "util", "servicedog": "util",
    "endowment": "deon",
    "garden": None,   # same answer in all nine variants
}

Q0_ANSWERS = {
    "brother": {
        1: "Messages complaining about school",
        2: "Messages about feeling stressed and overwhelmed",
        3: "Extremely worrying messages about harming himself and feeling hopeless",
    },
    "bully": {
        1: "They had been pushed up against the lockers and looked very unhappy",
        2: "The other student was pulling at their hair and they looked very frightened",
        3: "They were being held in a chokehold and looked badly bruised",
    },
    "endowment": {   # keyed by DEONTOLOGY level
        1: "Murder",
        2: "Theft",
        3: "Jaywalking",
    },
    "garden": "A narrow length of tubing running from the main water source, bypassing the water meter",
    "giftcard": {
        1: "To buy a wedding gift for a friend's wedding that day",
        2: "To pay an electricity bill for her apartment that was due that day",
        3: "To pay a hospital bill for her child that was due that day",
    },
    "lifeboat_number": {
        1: "19", 
        2: "40", 
        3: "102",
    },
    "medication": {
        1: "Her next seizure would give her a severe headache",
        2: "Her next seizure would leave her with lasting brain damage",
        3: "Her next seizure would be fatal",
    },
    "robinhood": {
        1: "They will have to sell their second car",
        2: "They will have to take their eldest child out of college",
        3: "They will go bankrupt",
    },
    "ropeladder": {
        1: "5", 
        2: "10", 
        3: "20",
    },
    "servicedog": {
        1: "So the narrator can take the dog hiking upstate — the dog suffers from being cooped up",
        2: "To get the dog to the hospital for treatment of intense allergic reactions",
        3: "To get the dog to the hospital for treatment of life-threatening cancer",
    },
}

def q0_answer(survey):
    scenario = survey["scenario"]
    level = Q0_LEVEL[scenario]
    entry = Q0_ANSWERS[scenario]
    answer = entry if level is None else entry[survey[level]]
    if answer is None:
        raise ValueError(f"Q0 answer for {scenario} ({level}={survey.get(level)}) is not filled in yet")
    return answer

# ---- Outcome bank: parsed from the text file ----
_HEADER = re.compile(r"^(?P<scenario>[A-Za-z ]+?) - (?P<id>\d+), choice_(?P<choice>\d+)")
_OUTCOME = re.compile(r"^Outcome (?P<k>\d+)\b")
_CORRECT = re.compile(r"^\*\s*\(a\)\s*(?P<text>.+?)\s*✓\s*$")
_BANK_NAMES = {"Service Dog": "servicedog", "Lifeboat Number": "lifeboat_number"}

def parse_outcome_bank(path=BANK_PATH):
    """{(scenario, variant_id, choice): {outcome_number: correct_text}}"""
    bank, key, k = {}, None, None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if m := _HEADER.match(line):
            name = _BANK_NAMES.get(m["scenario"], m["scenario"].lower())
            key = (name, int(m["id"]), int(m["choice"]))
            if key in bank:
                raise ValueError(f"Duplicate block in outcome bank: {line}")
            bank[key] = {}
        elif m := _OUTCOME.match(line):
            k = int(m["k"])
        elif m := _CORRECT.match(line):
            bank[key][k] = m["text"]
    return bank

# ---- Comparing answers ----
def _norm(text):
    """Ignore case, extra spaces, trailing period and curly vs straight quotes."""
    text = unicodedata.normalize("NFKC", str(text))
    text = text.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    text = re.sub(r"\s+", " ", text).strip().rstrip(".").strip()
    return text.lower()

def text_rule(answer):
    target = _norm(answer)
    return lambda s: s.astype(str).map(_norm) == target

# ---- Order of checks in every survey ----
def check_sequence(n_outcomes):
    """Q0, bomb, trolley, then one check per outcome rotating outcome -> C/I/K -> anchor."""
    seq = ["q0", "bomb", "trolley"]
    n_anchor = 0
    for k in range(1, n_outcomes + 1):
        slot = (k - 1) % 3
        if slot == 0:
            seq.append(("outcome", k))
        elif slot == 1:
            seq.append(("cik", None))
        else:
            seq.append(("anchor", n_anchor))
            n_anchor += 1
    return seq

def build_answers(survey, structure, bank):
    """{ImportId: rule} for one survey export, with checks that the survey matches the template."""
    attention = structure["attention"]
    n_outcomes = len(structure["outcome_prob"])
    seq = check_sequence(n_outcomes)
    if len(seq) != len(attention):
        raise ValueError(f"{stem_name(survey)}: template expects {len(seq)} attention checks "
                         f"(3 + {n_outcomes} outcomes) but the survey has {len(attention)}")

    key = (survey["scenario"], variant_id(survey["util"], survey["deon"]), survey["choice"])
    if key not in bank:
        raise KeyError(f"No outcome-bank block for {key}")
    outcomes = bank[key]
    if len(outcomes) != n_outcomes:
        raise ValueError(f"{key}: bank lists {len(outcomes)} outcomes, survey has {n_outcomes}")

    rules = []
    for slot in seq:
        if slot == "q0":
            rules.append(text_rule(q0_answer(survey)))
        elif slot == "bomb":
            rules.append(BOMB)
        elif slot == "trolley":
            rules.append(TROLLEY)
        elif slot[0] == "outcome":
            rules.append(text_rule(outcomes[slot[1]]))
        elif slot[0] == "cik":
            rules.append(text_rule(CIK_ANSWER))
        else:  # anchor
            if slot[1] >= len(ANCHORS):
                raise ValueError(f"{stem_name(survey)}: more anchor checks than defined in ANCHORS")
            rules.append(text_rule(ANCHORS[slot[1]]))
    return dict(zip(attention, rules))