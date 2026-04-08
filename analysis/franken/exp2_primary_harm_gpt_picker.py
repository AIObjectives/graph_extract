import os
import ast
import logging
import pandas as pd
from openai import OpenAI
from dotenv import dotenv_values
from dotenv import load_dotenv

# --- Config ---
INPUT_CSV = "exp2matched_annotator_megadf_final.csv"
OUTPUT_CSV = "exp2matched_annotator_megadf_final_gpt5mini_picked.csv"
MODEL = "gpt-5-mini"
MAX_TOKENS = 1024

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

load_dotenv()  # Load environment variables from .env file
client = OpenAI(api_key=os.getenv("OAI2"))


def parse_events(raw: str) -> list[tuple]:
    """Parse the events_cik_utilities string into a list of tuples."""
    return ast.literal_eval(raw)


def build_prompt(scenario_text: str, event_descriptions: list[str]) -> str:
    numbered = "\n".join(f"{i+1}. {desc}" for i, desc in enumerate(event_descriptions))
    return f"""You are simulating the judgment of a regular person with no special expertise.

A person is given the following scenario and asked: "Consider the implications of the negative outcome."

SCENARIO:
{scenario_text}

Below is a list of possible events associated with this scenario. Your job is to pick the single event that best matches what a typical person would intuitively identify as "the negative outcome" when reading this scenario.

POSSIBLE EVENTS:
{numbered}

Rules:
- Pick exactly one event from the list above.
- Base your choice purely on the scenario text and common human intuition. Do not apply any specialized ethical or philosophical reasoning.
- Respond with ONLY the number of your chosen event (e.g. "3"). No explanation, no punctuation, nothing else."""


def select_event(scenario_text: str, events: list[tuple]) -> tuple:
    """Call the API and return the selected event tuple."""
    descriptions = [e[0] for e in events]
    prompt = build_prompt(scenario_text, descriptions)

    msg = client.chat.completions.create(
        model=MODEL,
        max_completion_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}]
    )

    raw_response = msg.choices[0].message.content.strip()
    chosen_idx = int(raw_response) - 1  # Convert to 0-based index

    if not (0 <= chosen_idx < len(events)):
        raise ValueError(f"Model returned out-of-range index: {raw_response}")

    return events[chosen_idx]


def main():
    # df = pd.read_csv(INPUT_CSV)
    df = pd.read_csv(INPUT_CSV)
    log.info(f"Loaded {len(df)} rows from {INPUT_CSV}")

    results = []
    failed_rows = []

    for i, row in df.iterrows():
        row_num = i + 2  # +2 accounts for 0-index and header row, so matches CSV line number
        try:
            events = parse_events(row["events_cik_utilities"])
            selected = select_event(row["scenario_text"], events)
            result_row = row.to_dict()
            result_row["selected_event"] = str(selected)
            results.append(result_row)
            log.info(f"Row {row_num}: OK → {selected[0][:60]}...")

        except Exception as e:
            log.error(f"Row {row_num}: FAILED — {e}")
            failed_rows.append(row_num)

    out_df = pd.DataFrame(results)
    out_df.to_csv(OUTPUT_CSV, index=False)

    log.info(f"\nDone. {len(results)} rows saved to {OUTPUT_CSV}")
    if failed_rows:
        log.warning(f"Failed rows (CSV line numbers): {failed_rows}")
    else:
        log.info("No failures.")


if __name__ == "__main__":
    main()