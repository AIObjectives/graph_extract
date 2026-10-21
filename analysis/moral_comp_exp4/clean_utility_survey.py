"""
Clean Qualtrics exports from the moral annotator utility-validation surveys.

The survey layout (characters, outcomes, causal questions, attention checks) is
detected from the Qualtrics short-name header row, so the same code works for any
scenario built from the same survey template, whatever its number of characters
and outcomes. Only the attention-check answers and manual exclusions are
scenario-specific and must be passed in.

Template assumptions (short names in the first header row of the export):
    Sentience                   sentience check (free text)
    entity_q / other_entities   character identification questions
    attention_q                 comprehension checks (any column whose text
                                contains "Comprehension Check" also counts)
    utility_q*                  utility sliders; before the first outcome block:
                                overall utility, then one per character
    outcome_q*                  outcome likelihood; starts a new outcome block
    causal_q*                   causal ratings (knew / intended / caused)
                                for the current outcome block
    utility_q*                  inside an outcome block: one per character
"""

import json
import re
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Union

import pandas as pd

# An attention-check rule is either the exact correct option text,
# or a function that takes the response column and returns True/False per row
AnswerRule = Union[str, Callable[[pd.Series], pd.Series]]

NOT_SENTIENT_PATTERN = r"^no\b|not sentient"


@dataclass
class CleanResult:
    clean: pd.DataFrame              # one row per kept participant, renamed columns
    exclusions: pd.DataFrame         # response_id, reason for every dropped response
    structure: dict                  # detected survey layout (see detect_structure)
    attention_checks: pd.DataFrame   # True/False per check, before the attention cutoff


def load_qualtrics(csv_path: Union[str, Path]) -> tuple:
    """
    Load a Qualtrics CSV export (3 header rows: short name, question text, ImportId).
    Returns (df, codebook): responses with ImportIds as column names, and a
    codebook with one row per column (qid, name, text).
    """
    header = pd.read_csv(csv_path, header=None, nrows=3)
    qids = [json.loads(x)["ImportId"] for x in header.iloc[2]]
    if len(set(qids)) != len(qids):
        raise ValueError("ImportIds are not unique; is this a standard Qualtrics export?")

    codebook = pd.DataFrame({"qid": qids, "name": header.iloc[0], "text": header.iloc[1]})
    df = pd.read_csv(csv_path, header=None, skiprows=3, names=qids)
    return df, codebook


def _single_qid(codebook: pd.DataFrame, name: str) -> str:
    """Return the ImportId of the one column with this short name."""
    matches = codebook.loc[codebook["name"] == name, "qid"].tolist()
    if len(matches) != 1:
        raise ValueError(f"Expected exactly 1 column named '{name}', found {len(matches)}")
    return matches[0]


def _char_label(text: str) -> Union[str, None]:
    """
    Extract the character name from a utility grid column's text, if present.
    Qualtrics ends every grid column's text with " - <character>": the first column
    carries the full question text before it, the others just "utility_q".
    """
    text = str(text).strip()
    return text.rsplit(" - ", 1)[1].strip() if " - " in text else None


def _outcome_label(text: str) -> Union[str, None]:
    """
    Extract the outcome description from the first utility column of an outcome block,
    whose text ends with the line "Outcome: <description> - <character>".
    """
    lines = str(text).strip().splitlines()
    if not lines or not lines[-1].strip().startswith("Outcome:"):
        return None
    return lines[-1].strip()[len("Outcome:"):].rsplit(" - ", 1)[0].strip()


def detect_structure(codebook: pd.DataFrame) -> dict:
    """
    Walk the survey columns in order and group the ImportIds by role.
    Returns a dict with keys:
        sentience, entity, other_entities, overall_utility   single ImportIds
        char_utility       [char_1, ..., char_n]
        outcome_utility    [[char_1, ..., char_n] per outcome]
        outcome_prob       [outcome_1, ..., outcome_m]
        outcome_causal     [[causal_1, ..., causal_k] per outcome]
        attention          [ImportIds of every attention check, in survey order]
        char_labels        [character name per char, None if not in the header]
        outcome_labels     [outcome description per outcome, None if not in the header]
    """
    structure = {
        "sentience": _single_qid(codebook, "Sentience"),
        "entity": _single_qid(codebook, "entity_q"),
        "other_entities": _single_qid(codebook, "other_entities"),
    }

    attention = []
    pre_outcome_utility = []
    outcomes = []   # one dict per outcome block: prob, causal, utility

    for qid, name, text in codebook[["qid", "name", "text"]].itertuples(index=False):
        name = str(name)
        if name.startswith("attention_q") or "Comprehension Check" in str(text):
            attention.append(qid)
        elif name.startswith("outcome_q"):
            outcomes.append({"prob": qid, "causal": [], "utility": []})
        elif name.startswith("causal_q"):
            if not outcomes:
                raise ValueError(f"Causal question {qid} appears before any outcome_q")
            outcomes[-1]["causal"].append(qid)
        elif name.startswith("utility_q"):
            (outcomes[-1]["utility"] if outcomes else pre_outcome_utility).append(qid)

    if len(pre_outcome_utility) < 2:
        raise ValueError("Expected an overall utility and at least 1 character utility "
                         f"before the first outcome, found {len(pre_outcome_utility)} sliders")
    if not outcomes:
        raise ValueError("No outcome_q columns found")

    structure["overall_utility"] = pre_outcome_utility[0]
    structure["char_utility"] = pre_outcome_utility[1:]
    n_chars = len(structure["char_utility"])
    n_causal = len(outcomes[0]["causal"])

    # Every outcome block must rate every character and ask the same causal questions
    for o, block in enumerate(outcomes, start=1):
        if len(block["utility"]) != n_chars:
            raise ValueError(f"Outcome {o} has {len(block['utility'])} character utilities, "
                             f"expected {n_chars}: {block['utility']}")
        if len(block["causal"]) != n_causal:
            raise ValueError(f"Outcome {o} has {len(block['causal'])} causal questions, "
                             f"expected {n_causal}: {block['causal']}")

    structure["outcome_prob"] = [block["prob"] for block in outcomes]
    structure["outcome_causal"] = [block["causal"] for block in outcomes]
    structure["outcome_utility"] = [block["utility"] for block in outcomes]
    structure["attention"] = attention

    text_by_qid = dict(zip(codebook["qid"], codebook["text"]))
    structure["char_labels"] = [_char_label(text_by_qid[qid]) for qid in structure["char_utility"]]
    structure["outcome_labels"] = [_outcome_label(text_by_qid[block[0]])
                                   for block in structure["outcome_utility"]]

    return structure


def describe_structure(structure: dict, codebook: pd.DataFrame) -> None:
    """Print the detected layout, to check it before cleaning a new scenario."""
    text_by_qid = dict(zip(codebook["qid"], codebook["text"].astype(str)))

    print(f"Characters: {len(structure['char_utility'])}")
    for c, label in enumerate(structure["char_labels"], start=1):
        print(f"  char_{c}: {label or '(name not in header; check Qualtrics)'}")
    print(f"Outcomes: {len(structure['outcome_prob'])}")
    for o, label in enumerate(structure["outcome_labels"], start=1):
        print(f"  outcome_{o}: {label or '(description not in header; check Qualtrics)'}")
    print(f"Causal questions per outcome: {len(structure['outcome_causal'][0])}")
    print(f"Attention checks: {len(structure['attention'])}")
    for a, qid in enumerate(structure["attention"], start=1):
        # Last non-empty line of the question text is the actual check question
        lines = [line.strip() for line in text_by_qid[qid].splitlines() if line.strip()]
        print(f"  attention_{a} ({qid}): {lines[-1][:90]}")


def build_rename_map(structure: dict) -> Dict[str, str]:
    """Map ImportIds to clean column names; the dict order is the output column order."""
    rename_map = {
        structure["sentience"]: "Sentience",
        structure["entity"]: "entity",
        structure["other_entities"]: "other_entities",
        structure["overall_utility"]: "overall_utility",
    }
    for c, qid in enumerate(structure["char_utility"], start=1):
        rename_map[qid] = f"char_{c}_utility"
    for c in range(len(structure["char_utility"])):
        for o, block in enumerate(structure["outcome_utility"], start=1):
            rename_map[block[c]] = f"char_{c+1}_outcome_{o}"
    for o, (prob, causal) in enumerate(zip(structure["outcome_prob"],
                                           structure["outcome_causal"]), start=1):
        rename_map[prob] = f"outcome_prob_{o}"
        for k, qid in enumerate(causal, start=1):
            rename_map[qid] = f"causal_{k}_outcome_{o}"
    for a, qid in enumerate(structure["attention"], start=1):
        rename_map[qid] = f"attention_{a}"
    return rename_map


def score_attention(df: pd.DataFrame, answers: Dict[str, AnswerRule],
                    attention_qids: List[str]) -> pd.DataFrame:
    """
    Score each attention check as True/False per participant.
    answers maps every attention ImportId to its rule: the correct option text,
    or a function of the response column (e.g. lambda v: v == -100).
    """
    missing = [qid for qid in attention_qids if qid not in answers]
    unknown = [qid for qid in answers if qid not in attention_qids]
    if missing or unknown:
        raise ValueError(f"Attention answers don't match the survey. "
                         f"Missing rules for: {missing}. Not attention checks: {unknown}")

    checks = pd.DataFrame(index=df.index)
    for qid in attention_qids:
        rule = answers[qid]
        if callable(rule):
            checks[qid] = rule(df[qid])
        else:
            checks[qid] = df[qid].astype(str).str.strip() == rule.strip()

    return checks


def clean_survey(csv_path: Union[str, Path], attention_answers: Dict[str, AnswerRule],
                 excluded_ids: Iterable[str] = (), min_attention_correct: int = 7,
                 not_sentient_pattern: str = NOT_SENTIENT_PATTERN) -> CleanResult:
    """
    Full cleaning pipeline for one survey export:
        1. keep finished responses
        2. drop blank or "not sentient" sentience answers
        3. drop hard-coded response IDs (excluded_ids)
        4. drop participants with fewer than min_attention_correct attention checks right
        5. select and rename the survey columns, add Subject numbers
    """
    df, codebook = load_qualtrics(csv_path)
    structure = detect_structure(codebook)
    exclusions = []

    def drop(df, mask, reason):
        """Drop rows where mask is True, logging their response IDs."""
        exclusions.extend({"response_id": rid, "reason": reason}
                          for rid in df.loc[mask, "_recordId"])
        return df[~mask]

    finished = df["finished"].astype(str).str.strip().str.lower() == "true"
    df = drop(df, ~finished, "not finished")

    sentience = df[structure["sentience"]].fillna("").astype(str).str.strip()
    df = drop(df, sentience == "", "sentience blank")
    sentience = sentience[df.index]
    df = drop(df, sentience.str.contains(not_sentient_pattern, case=False, regex=True),
              "not sentient")

    excluded_ids = list(excluded_ids)
    not_found = set(excluded_ids) - set(df["_recordId"]) - {e["response_id"] for e in exclusions}
    if not_found:
        warnings.warn(f"Excluded IDs not found in the data: {sorted(not_found)}")
    df = drop(df, df["_recordId"].isin(excluded_ids), "manual exclusion")

    checks = score_attention(df, attention_answers, structure["attention"])
    df = df.assign(attention_correct=checks.sum(axis=1))
    df = drop(df, df["attention_correct"] < min_attention_correct,
              f"fewer than {min_attention_correct} attention checks correct")

    rename_map = build_rename_map(structure)
    clean = df[list(rename_map) + ["attention_correct"]].rename(columns=rename_map)
    clean = clean.reset_index(drop=True)
    clean.insert(0, "Subject", range(len(clean)))

    return CleanResult(clean=clean,
                       exclusions=pd.DataFrame(exclusions, columns=["response_id", "reason"]),
                       structure=structure,
                       attention_checks=checks)
