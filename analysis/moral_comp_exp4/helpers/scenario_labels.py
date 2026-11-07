"""
scenario_labels.py -- the single source of entity/outcome labels, matched provably.

Reference: qualtrics_<name>.json in annotated_outputs/moral_comp_exp4/  (what the
survey was built from) -- {scenario, scenario_idx, choice, entities, outcomes}.

The cleaned df's char_/outcome_ columns are positional. To label them we read what
each survey QUESTION was about and confirm it against the reference:

  - outcomes: for each outcome block, find which reference-outcome string appears in
    that block's question text (containment -- no dependence on a fixed format), as a
    bijection: exactly one outcome per block, every outcome used once.
  - entities: read the ' - <entity>' each grid column carries and confirm it is one of
    the reference entities.

Anything that doesn't match raises, so a column can never be silently mislabelled.
resolve_labels() runs at CLEAN time (raw export present) and returns a Labels, which
is saved next to the clean CSV and read back for plotting.
"""
import json
import re
import unicodedata
from dataclasses import dataclass
from html import unescape
from pathlib import Path
from typing import Dict, List, Optional

# helpers/ -> moral_comp_exp4 -> analysis -> repo root; the JSONs are at repo-root/annotated_outputs
ANNOT_DIR = Path(__file__).resolve().parents[3] / "annotated_outputs" / "moral_comp_exp4"


def _norm(s: str) -> str:
    s = unescape(str(s))
    s = unicodedata.normalize("NFKC", s).replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", s).strip().casefold()


def entity_from_text(text: str) -> Optional[str]:
    """A utility grid column's text ends with ' - <entity>'."""
    text = str(text).strip()
    return text.rsplit(" - ", 1)[1].strip() if " - " in text else None


def read_spec(name: str) -> dict:
    """The qualtrics_<name>.json reference record."""
    path = ANNOT_DIR / f"qualtrics_{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"No qualtrics spec for '{name}': {path}")
    spec = json.loads(path.read_text())
    if not isinstance(spec, list) or len(spec) != 1:
        raise ValueError(f"{name}: expected a 1-element qualtrics list")
    return spec[0]


@dataclass(frozen=True)
class Labels:
    """entities[i] labels char_(i+1); outcomes[j] labels outcome_(j+1)."""
    entities: List[str]
    outcomes: List[str]

    def column_labels(self) -> Dict[str, str]:
        """Cleaned column -> readable label, for a display-only rename of the df."""
        m = {}
        for c, e in enumerate(self.entities, 1):
            m[f"char_{c}_utility"] = f"{e} (utility)"
            for o, _ in enumerate(self.outcomes, 1):
                m[f"char_{c}_outcome_{o}"] = f"{e} | outcome {o}"
        for o, t in enumerate(self.outcomes, 1):
            m[f"outcome_prob_{o}"] = f"P(outcome {o}: {t})"
        return m

    def table(self):
        """Tidy matching table: kind / index / label."""
        import pandas as pd
        rows = ([("entity", i, e) for i, e in enumerate(self.entities, 1)] +
                [("outcome", j, t) for j, t in enumerate(self.outcomes, 1)])
        return pd.DataFrame(rows, columns=["kind", "index", "label"])

    def save(self, path) -> None:
        Path(path).write_text(json.dumps({"entities": self.entities, "outcomes": self.outcomes},
                                         indent=1, ensure_ascii=False))

    @classmethod
    def load(cls, path) -> "Labels":
        d = json.loads(Path(path).read_text())
        return cls(entities=d["entities"], outcomes=d["outcomes"])


def _match_outcomes(block_text: Dict[int, str], outcomes: List[str]) -> Dict[int, int]:
    """block index -> reference-outcome index. Each reference outcome must appear in
    exactly one block, and each block must match exactly one outcome."""
    out, used = {}, set()
    for o, text in block_text.items():
        hits = [i for i, s in enumerate(outcomes) if _norm(s) in text]
        if len(hits) != 1:
            raise ValueError(f"outcome block {o + 1} matched {len(hits)} reference outcomes "
                             f"(need exactly 1): {[outcomes[i] for i in hits]}")
        i = hits[0]
        if i in used:
            raise ValueError(f"reference outcome #{i + 1} matched two blocks")
        out[o] = i
        used.add(i)
    missing = set(range(len(outcomes))) - used
    if missing:
        raise ValueError(f"reference outcomes never found in any block: "
                         f"{[outcomes[i] for i in sorted(missing)]}")
    return out


def resolve_labels(name: str, codebook, structure) -> Labels:
    """
    Build the matching table for one survey: label every char_/outcome_ column from the
    qualtrics reference, proven against the survey's own question text. Raises on any
    mismatch. Run at clean time, where the raw export's question text is available.
    """
    spec = read_spec(name)
    text_by_qid = dict(zip(codebook["qid"], codebook["text"]))

    # --- entities: read each grid column's ' - <entity>', confirm it's in the reference ---
    ref_entities = _norm(spec["entities"])            # comma-joined reference string
    entities, seen = [], set()
    for q in structure["char_utility"]:
        e = entity_from_text(text_by_qid[q])
        if e is None:
            raise ValueError(f"char column {q}: no ' - <entity>' in text:\n  {text_by_qid[q][:140]!r}")
        if _norm(e) not in ref_entities:
            raise ValueError(f"char column {q}: entity {e!r} not in qualtrics entities {spec['entities']!r}")
        if _norm(e) in seen:
            raise ValueError(f"entity {e!r} appears in two char columns")
        seen.add(_norm(e))
        entities.append(e)

    # --- outcomes: find which reference outcome each block's text contains (bijection) ---
    out_cols = list(structure["outcome_prob"])
    block_text = {}
    for o in range(len(out_cols)):
        qids = [out_cols[o]] + list(structure["outcome_utility"][o]) + list(structure["outcome_causal"][o])
        block_text[o] = _norm(" \n ".join(str(text_by_qid[q]) for q in qids))
    omap = _match_outcomes(block_text, list(spec["outcomes"]))
    outcomes = [spec["outcomes"][omap[o]] for o in range(len(out_cols))]

    return Labels(entities=entities, outcomes=outcomes)
