"""
Qualtrics Survey Manager
- Import a QSF file to create a new survey
- Inspect and edit individual questions
"""

import json
import os
import sys
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Configuration — set these as environment variables or hard-code for testing
# ---------------------------------------------------------------------------
API_TOKEN = os.environ.get("QUALTRICS_API_TOKEN", "")
DATA_CENTER = os.environ.get("QUALTRICS_DATA_CENTER", "")  # e.g. "ca1", "iad1", "fra1"

BASE_URL = f"https://{DATA_CENTER}.qualtrics.com/API/v3"
HEADERS = {
    "X-API-TOKEN": API_TOKEN,
    "Content-Type": "application/json",
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _check_config():
    if not API_TOKEN or not DATA_CENTER:
        sys.exit(
            "ERROR: Set QUALTRICS_API_TOKEN and QUALTRICS_DATA_CENTER environment variables.\n"
            "  export QUALTRICS_API_TOKEN='your-token'\n"
            "  export QUALTRICS_DATA_CENTER='iad1'   # find this in Account Settings > Qualtrics IDs"
        )


def _raise_for_status(resp: requests.Response):
    if not resp.ok:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise RuntimeError(f"Qualtrics API error {resp.status_code}: {detail}")


# ---------------------------------------------------------------------------
# Survey import
# ---------------------------------------------------------------------------

def import_survey(qsf_path: str, survey_name: str | None = None) -> str:
    """
    Import a QSF file and return the new survey ID.

    survey_name overrides the name embedded in the QSF (optional).
    """
    _check_config()
    qsf_file = Path(qsf_path)
    if not qsf_file.exists():
        raise FileNotFoundError(qsf_file)

    payload = qsf_file.read_text(encoding="utf-8")

    # Optionally override the survey name before import
    if survey_name:
        data = json.loads(payload)
        data["SurveyEntry"]["SurveyName"] = survey_name
        payload = json.dumps(data)

    resp = requests.post(
        f"{BASE_URL}/surveys",
        headers={"X-API-TOKEN": API_TOKEN},
        files={"file": (qsf_file.name, payload.encode("utf-8"), "application/vnd.qualtrics.survey.qsf")},
    )
    _raise_for_status(resp)
    result = resp.json()
    survey_id = result["result"]["id"]
    print(f"Survey imported successfully. New Survey ID: {survey_id}")
    return survey_id


# ---------------------------------------------------------------------------
# Survey inspection
# ---------------------------------------------------------------------------

def get_survey(survey_id: str) -> dict:
    """Return the full survey definition (blocks, flow, questions, etc.)."""
    _check_config()
    resp = requests.get(
        f"{BASE_URL}/survey-definitions/{survey_id}",
        headers=HEADERS,
    )
    _raise_for_status(resp)
    return resp.json()["result"]


def list_questions(survey_id: str) -> dict:
    """Return a dict mapping QuestionID -> brief question info."""
    _check_config()
    resp = requests.get(
        f"{BASE_URL}/survey-definitions/{survey_id}/questions",
        headers=HEADERS,
    )
    _raise_for_status(resp)
    elements = resp.json()["result"]["elements"]
    return {q["QuestionID"]: q for q in elements}


def get_question(survey_id: str, question_id: str) -> dict:
    """Return the full payload for a single question."""
    _check_config()
    resp = requests.get(
        f"{BASE_URL}/survey-definitions/{survey_id}/questions/{question_id}",
        headers=HEADERS,
    )
    _raise_for_status(resp)
    return resp.json()["result"]


# ---------------------------------------------------------------------------
# Question editing
# ---------------------------------------------------------------------------

def update_question(survey_id: str, question_id: str, updates: dict) -> dict:
    """
    Merge `updates` into the existing question payload and PUT it back.

    Example:
        update_question(survey_id, "QID14", {
            "QuestionText": "New instructions here..."
        })
    """
    _check_config()
    question = get_question(survey_id, question_id)
    question.update(updates)

    resp = requests.put(
        f"{BASE_URL}/survey-definitions/{survey_id}/questions/{question_id}",
        headers=HEADERS,
        json=question,
    )
    _raise_for_status(resp)
    print(f"Question {question_id} updated.")
    return resp.json().get("result", {})


def update_question_text(survey_id: str, question_id: str, new_text: str) -> dict:
    """Convenience wrapper to change only the QuestionText of a question."""
    return update_question(survey_id, question_id, {"QuestionText": new_text})


def update_loop_fields(survey_id: str, block_id: str, rows: dict) -> dict:
    """
    Replace the Static loop rows for a Loop & Merge block.

    `rows` should be a dict like the Qualtrics LoopingOptions.Static format:
        {
            "1": {"1": "scenario text", "2": "action choice", ...},
            "2": {"1": "...", ...},
        }

    Note: This updates the block options, which requires getting the full
    survey definition and PUTting the modified block back.
    """
    _check_config()
    survey = get_survey(survey_id)

    # Find the block in the survey definition
    blocks = survey.get("Blocks", {})
    if block_id not in blocks:
        raise KeyError(f"Block {block_id!r} not found. Available: {list(blocks.keys())}")

    block = blocks[block_id]
    block.setdefault("Options", {}).setdefault("LoopingOptions", {})["Static"] = rows

    resp = requests.put(
        f"{BASE_URL}/survey-definitions/{survey_id}/blocks/{block_id}",
        headers=HEADERS,
        json=block,
    )
    _raise_for_status(resp)
    print(f"Block {block_id} loop fields updated.")
    return resp.json().get("result", {})


# ---------------------------------------------------------------------------
# Block helpers
# ---------------------------------------------------------------------------

def list_blocks(survey_id: str) -> dict:
    """Return a dict mapping block ID -> block description/type."""
    _check_config()
    survey = get_survey(survey_id)
    blocks = survey.get("Blocks", {})
    return {bid: {"Description": b.get("Description", ""), "Type": b.get("Type", "")}
            for bid, b in blocks.items()}


# ---------------------------------------------------------------------------
# Scenario / entity parsing
# ---------------------------------------------------------------------------

def _extract_beings_recursive(obj: object, found: list[str] | None = None) -> list[str]:
    """
    Recursively walk a parsed JSON object and collect entity labels where:
      - a dict has "kind" == "being"  -> take its "label" value
      - a dict has a literal key "being"  -> take that value directly
    Both patterns are handled so the function is robust to structural variations.
    """
    if found is None:
        found = []
    if isinstance(obj, dict):
        if obj.get("kind") == "being" and "label" in obj:
            found.append(str(obj["label"]))
        if "being" in obj:
            found.append(str(obj["being"]))
        for v in obj.values():
            _extract_beings_recursive(v, found)
    elif isinstance(obj, list):
        for item in obj:
            _extract_beings_recursive(item, found)
    return found


def load_choice_entities(choice_path: str) -> list[str]:
    """
    Parse a nie_scenarios_{id}_choice_{n}.json (JSONL - one JSON object per line)
    and return the ordered, deduplicated list of entity labels, excluding 'i'.
    """
    seen: set[str] = set()
    entities: list[str] = []
    for line in Path(choice_path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        for label in _extract_beings_recursive(obj):
            if label != "i" and label not in seen:
                seen.add(label)
                entities.append(label)
    return entities


def load_scenarios(scenarios_path: str) -> list[dict]:
    """Parse nie_scenario_example.json and return the list of scenario dicts."""
    return json.loads(Path(scenarios_path).read_text(encoding="utf-8"))


def build_loop_rows(
    scenarios: list[dict],
    choices_dir: str,
    choice_file_pattern: str = "nie_scenarios_{id}_choice_{choice}.json",
) -> tuple[dict, int]:
    """
    Build the Loop & Merge Static rows dict from scenario + choice JSONs.

    Field mapping per row:
      Field/1  = scenario text
      Field/2  = action choice text
      Field/3+ = entity names (padded with "" up to max_entities across all rows)

    Returns (rows_dict, max_entities).
    """
    choices_dir_path = Path(choices_dir)
    raw_rows: list[tuple[str, str, list[str]]] = []

    for scenario in scenarios:
        sid = scenario["id"]
        text = scenario["text"].strip()
        for choice_num, action_text in scenario["options"].items():
            fname = choice_file_pattern.format(id=sid, choice=choice_num)
            choice_path = choices_dir_path / fname
            if not choice_path.exists():
                raise FileNotFoundError(f"Expected choice file not found: {choice_path}")
            entities = load_choice_entities(str(choice_path))
            raw_rows.append((text, action_text.strip(), entities))

    max_entities = max((len(r[2]) for r in raw_rows), default=0)

    rows: dict = {}
    for i, (text, action, entities) in enumerate(raw_rows, start=1):
        padded = entities + [""] * (max_entities - len(entities))
        row: dict[str, str] = {"1": text, "2": action}
        for j, entity in enumerate(padded, start=3):
            row[str(j)] = entity
        rows[str(i)] = row

    return rows, max_entities


# ---------------------------------------------------------------------------
# Survey builder - wires everything together
# ---------------------------------------------------------------------------

# IDs of the three entity harm questions already in Block B, mapped to the
# loop fields they should reference (Field/3, Field/4, Field/5).
_EXISTING_ENTITY_QUESTIONS = [
    ("QID59", 3),
    ("QID63", 4),
    ("QID64", 5),
]

_BLOCK_B_ID = "BL_8ChWTYR6noJG5WS"


def _make_entity_question_payload(field_num: int, template: dict) -> dict:
    """Clone the template entity question and retarget it to a new field number."""
    import copy
    q = copy.deepcopy(template)
    q.pop("QuestionID", None)
    q.pop("DisplayLogic", None)
    entity_ref = "${lm://Field/" + str(field_num) + "}"
    q["QuestionText"] = "How much harm/benefit is done to " + entity_ref + " from Ziv's action?"
    q["QuestionDescription"] = "How much harm/benefit is done to " + entity_ref + " from Ziv's action?"
    q["DataExportTag"] = "Other-Harm-Entity" + str(field_num - 2)
    return q


def build_survey(
    survey_id: str,
    scenarios_path: str,
    choices_dir: str,
    block_id: str = _BLOCK_B_ID,
    choice_file_pattern: str = "nie_scenarios_{id}_choice_{choice}.json",
):
    """
    Full pipeline - run this after importing the QSF.

    Steps:
      1. Parse scenario + choice JSONs -> build loop rows
      2. Fix QID61 text (drop old Field/3 outcome reference)
      3. Update exactly max_entities entity questions with correct field refs
      4. If max_entities > 3, create extra entity questions via the API
      5. Rebuild block's BlockElements to include only the needed entity questions
      6. Upload loop rows to the block

    Why no display logic: lm://Field/N works as piped text inside question bodies,
    but Qualtrics does not resolve it as an embedded-data variable in display-logic
    conditions at runtime - NotEmpty always evaluates false and hides the question.
    The fix is to include exactly max_entities entity questions in the block so
    nothing needs to be hidden. If entity counts vary across loop rows, questions
    with empty entity names will appear for shorter rows; keep counts consistent
    across all scenarios to avoid this.
    """
    print("Loading scenarios and building loop rows...")
    scenarios = load_scenarios(scenarios_path)
    rows, max_entities = build_loop_rows(scenarios, choices_dir, choice_file_pattern)
    print("  " + str(len(rows)) + " loop rows, " + str(max_entities) + " max entities per row")

    # Warn if entity counts vary across rows
    counts = [
        sum(1 for fi in range(3, max_entities + 3) if row.get(str(fi), ""))
        for row in rows.values()
    ]
    if len(set(counts)) > 1:
        print("  WARNING: entity counts vary across rows: " + str(counts) + ". "
              "Questions with empty entity names will appear for shorter rows.")

    # Step 2 - fix QID61: show scenario + action choice only, no outcome field
    print("Fixing QID61 (scenario redisplay before intention/causation questions)...")
    update_question(survey_id, "QID61", {
        "QuestionText": (
            "Consider the following scenario:"
            "<br><br>${lm://Field/1}<br><br>${lm://Field/2}<br>"
        ),
        "QuestionDescription": "Consider the following scenario: ${lm://Field/1} ${lm://Field/2}",
    })

    # Steps 3 & 4 - update/create exactly max_entities entity questions (no display logic)
    entity_qids: list[str] = []

    for i, (qid, field_num) in enumerate(_EXISTING_ENTITY_QUESTIONS):
        if i >= max_entities:
            break
        entity_ref = "${lm://Field/" + str(field_num) + "}"
        update_question(survey_id, qid, {
            "QuestionText": "How much harm/benefit is done to " + entity_ref + " from Ziv's action?",
            "QuestionDescription": "How much harm/benefit is done to " + entity_ref + " from Ziv's action?",
        })
        entity_qids.append(qid)
        print("  Updated " + qid + " -> Field/" + str(field_num))

    if max_entities > 3:
        template = get_question(survey_id, "QID64")
        # entity 4 -> Field/6, entity 5 -> Field/7, ...
        for field_num in range(6, max_entities + 3):
            payload = _make_entity_question_payload(field_num, template)
            resp = requests.post(
                f"{BASE_URL}/survey-definitions/{survey_id}/questions",
                headers=HEADERS,
                json=payload,
            )
            _raise_for_status(resp)
            new_qid = resp.json()["result"]["QuestionID"]
            entity_qids.append(new_qid)
            print("  Created " + new_qid + " -> Field/" + str(field_num) + " (entity " + str(field_num - 2) + ")")

    # Step 5 - rebuild BlockElements with exactly the right entity questions
    print("Rebuilding block elements with " + str(len(entity_qids)) + " entity question(s)...")
    survey_def = get_survey(survey_id)
    blocks = survey_def.get("Blocks", {})
    if block_id not in blocks:
        raise KeyError(f"Block {block_id!r} not found. Available: {list(blocks.keys())}")
    block = blocks[block_id]
    block["BlockElements"] = (
        [{"Type": "Question", "QuestionID": "QID60"},
         {"Type": "Question", "QuestionID": "QID57"}]
        + [{"Type": "Question", "QuestionID": q} for q in entity_qids]
        + [{"Type": "Page Break"}]
        + [{"Type": "Question", "QuestionID": "QID61"},
           {"Type": "Question", "QuestionID": "QID58"},
           {"Type": "Question", "QuestionID": "QID62"}]
    )
    resp = requests.put(
        f"{BASE_URL}/survey-definitions/{survey_id}/blocks/{block_id}",
        headers=HEADERS,
        json=block,
    )
    _raise_for_status(resp)
    print("Block " + block_id + " updated.")

    # Step 6 - upload loop rows
    print("Uploading loop rows to block...")
    update_loop_fields(survey_id, block_id, rows)

    print("Done. Survey is ready.")
    return rows


# ---------------------------------------------------------------------------
# Survey activation helpers
# ---------------------------------------------------------------------------

def activate_survey(survey_id: str):
    """Set survey status to Active."""
    _check_config()
    resp = requests.put(
        f"{BASE_URL}/surveys/{survey_id}",
        headers=HEADERS,
        json={"isActive": True},
    )
    _raise_for_status(resp)
    print(f"Survey {survey_id} activated.")


def deactivate_survey(survey_id: str):
    """Set survey status to Inactive."""
    _check_config()
    resp = requests.put(
        f"{BASE_URL}/surveys/{survey_id}",
        headers=HEADERS,
        json={"isActive": False},
    )
    _raise_for_status(resp)
    print(f"Survey {survey_id} deactivated.")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Qualtrics survey manager")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # import
    p_import = sub.add_parser("import", help="Import a QSF file as a new survey")
    p_import.add_argument("qsf", help="Path to the .qsf file")
    p_import.add_argument("--name", help="Override survey name", default=None)

    # list-questions
    p_list = sub.add_parser("list-questions", help="Print all question IDs and descriptions")
    p_list.add_argument("survey_id")

    # get-question
    p_get = sub.add_parser("get-question", help="Print full payload for one question")
    p_get.add_argument("survey_id")
    p_get.add_argument("question_id")

    # update-text
    p_upd = sub.add_parser("update-text", help="Update the QuestionText of a question")
    p_upd.add_argument("survey_id")
    p_upd.add_argument("question_id")
    p_upd.add_argument("text", help="New question text (HTML allowed)")

    # list-blocks
    p_lblocks = sub.add_parser("list-blocks", help="Print all block IDs and descriptions")
    p_lblocks.add_argument("survey_id")

    # build-survey
    p_build = sub.add_parser(
        "build-survey",
        help="Parse scenario JSONs and fully populate the imported survey",
    )
    p_build.add_argument("survey_id")
    p_build.add_argument("--scenarios", default="nie_scenario_example.json",
                         help="Path to scenarios JSON file (default: nie_scenario_example.json)")
    p_build.add_argument("--choices-dir", default=".",
                         help="Directory containing nie_scenarios_*_choice_*.json files (default: .)")
    p_build.add_argument("--block-id", default=_BLOCK_B_ID,
                         help=f"Loop & Merge block ID (default: {_BLOCK_B_ID})")

    args = parser.parse_args()

    if args.cmd == "import":
        import_survey(args.qsf, args.name)

    elif args.cmd == "list-questions":
        questions = list_questions(args.survey_id)
        for qid, q in sorted(questions.items()):
            desc = q.get("QuestionDescription", "")[:80]
            qtype = q.get("QuestionType", "")
            print(f"{qid:10s}  [{qtype:8s}]  {desc}")

    elif args.cmd == "get-question":
        q = get_question(args.survey_id, args.question_id)
        print(json.dumps(q, indent=2))

    elif args.cmd == "update-text":
        update_question_text(args.survey_id, args.question_id, args.text)

    elif args.cmd == "list-blocks":
        blocks = list_blocks(args.survey_id)
        for bid, info in blocks.items():
            print(f"{bid}  [{info['Type']:10s}]  {info['Description']}")

    elif args.cmd == "build-survey":
        build_survey(
            args.survey_id,
            scenarios_path=args.scenarios,
            choices_dir=args.choices_dir,
            block_id=args.block_id,
        )
