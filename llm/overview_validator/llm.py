# -*- coding: utf-8 -*-
# pipeline/steps/overview_validator/llm.py

import textwrap
from typing import Tuple
from provider import provider_manager
from state.settings_manager import settings_manager

PROMPT_TEMPLATE = textwrap.dedent("""
You are a story structure analyst.
Your task is to verify if a list of proposed chapters is coherent and consistent with the story described below.

Be moderately critical: ignore minor inconsistencies in style or small overlaps, but identify clear contradictions, missing logic, or structural imbalance.

Instructions:
1. Compare both the "Initial Story Requirements" and the "Expanded Plot Summary" with the proposed chapters.
2. Prioritize consistency with the Expanded Plot, but also ensure that the Initial Requirements are not contradicted.
3. Consider the GENRE described below when judging tone, pacing, and structure.
4. Additionally, verify that:
   - The chapter distribution follows a balanced story structure (Setup and Inciting events early, most chapters in Developments/Escalation, followed by a clear Climax and Resolution).
   - All major events and turning points from the Expanded Plot Summary are represented — none should be omitted or contradicted.
   - The chapters follow a logical cause–effect progression with consistent timeline and smooth transitions.
   - The main characters’ roles, motivations, and relationships remain consistent with their portrayal in the Expanded Plot Summary.
   - The tone and pacing fit the specified GENRE, and each chapter adds meaningful narrative value without redundancy or filler.
5. Do **not** suggest changing the **number of chapters** — only evaluate and comment on their internal coherence, logic, and alignment.
6. If the chapters align well with the story, answer exactly: "OK".
7. If there are issues, answer:
   "NOT OK"
   and provide a concise list of high-level corrections or suggestions (max 5 sentences) focused ONLY on improving the chapters (not rewriting the plot).

---

INITIAL STORY REQUIREMENTS:
\"\"\"{initial_plot}\"\"\"


EXPANDED PLOT SUMMARY:
\"\"\"{expanded_plot}\"\"\"


GENRE:
\"\"\"{genre}\"\"\"


CHAPTERS PROPOSAL:
\"\"\"{chapters}\"\"\" 
""")

def call_llm_validate_overview(
    initial_plot: str,
    expanded_plot: str,
    chapters: str,
    genre: str,
    *,
    api_url: str = None,
    model: str = "phi-3-mini-4k-instruct",
    params: dict = None,
    timeout: int = 120,
) -> Tuple[str, str]:
    """
    LLM-only validator for the chapter overview.
    Returns:
        ("OK", None) on pass
        ("NOT OK", suggestions) on fail
        ("ERROR", message) on request or parsing error
        ("UNKNOWN", raw_content) if the model's format is unexpected
    """
    messages = [
        {"role": "system", "content": "You are a logical story structure validator."},
        {
            "role": "user",
            "content": PROMPT_TEMPLATE.format(
                initial_plot=initial_plot,
                expanded_plot=expanded_plot,
                chapters=chapters,
                genre=genre,
            ),
        },
    ]

    task_params = settings_manager.get_task_params("overview_validator")
    retries = task_params.get("retries", 3)
    if retries is None:
        retries = 3
    retries = max(0, int(retries))

    last_error = None
    last_content = None

    for attempt in range(retries + 1):
        try:
            content = provider_manager.get_llm_response(
                task_name="overview_validator",
                messages=messages
            )
            last_content = content
        except Exception as e:
            last_error = str(e)
            if attempt < retries:
                continue
            return ("ERROR", f"Validation request failed: {last_error}")

        up = content.upper()
        if up.startswith("OK"):
            return ("OK", None)
        if up.startswith("NOT OK"):
            suggestions = content.split("\n", 1)[1].strip() if "\n" in content else "(no details provided)"
            return ("NOT OK", suggestions)

        if attempt < retries:
            continue

    return ("UNKNOWN", last_content or "(no response)")

