# -*- coding: utf-8 -*-
import json
import textwrap
from typing import Tuple, Dict, Any
from provider import provider_manager
from state.settings_manager import settings_manager

_VALIDATOR_PROMPT = textwrap.dedent("""\
You are a chapters overview validator. Your task is to check for structural issues in an edited Chapters Overview.

EDITED CHAPTERS OVERVIEW:
\"\"\"{new_overview}\"\"\"

SUMMARY OF CHANGES (from version diff):
\"\"\"{diff_summary}\"\"\"

Instructions:
1. **Numbering check**: Examine the chapter numbers in the edited overview. Verify that:
   - Chapters start at 1
   - Each subsequent chapter increments by exactly 1 (no gaps, no duplicates)
   - Example of valid: Chapter 1, Chapter 2, Chapter 3
   - Example of invalid: Chapter 1, Chapter 3 (gap), or Chapter 1, Chapter 1 (duplicate), or Chapter 0, Chapter 1 (doesn't start at 1)

2. **Deletion check**: Based on the SUMMARY OF CHANGES, determine if any chapters were removed/deleted from the overview. Look for mentions of removed chapters, decreased chapter count, or deleted content.

3. **Addition check**: Based on the SUMMARY OF CHANGES, determine if any new chapters were added to the overview. Look for mentions of added chapters, increased chapter count, or new chapter content.

Output format (strict JSON):
Respond with a single JSON object and nothing else:

{{
  "numbering": {{
    "valid": true or false,
    "reason": "Brief explanation if invalid, or empty string if valid"
  }},
  "deleted": {{
    "detected": true or false,
    "reason": "Brief explanation if detected, or empty string if not"
  }},
  "added": {{
    "detected": true or false,
    "reason": "Brief explanation if detected, or empty string if not"
  }}
}}

- Do not add any extra text before or after the JSON.
- If numbering is valid, set "valid": true and "reason": ""
- If no deletion detected, set "detected": false and "reason": ""
- If no addition detected, set "detected": false and "reason": ""
- When writing the "reason" fields, write them naturally as if you observed the issue directly from the overview. Do not mention that you deduced it from the SUMMARY OF CHANGES or reference the summary in your explanation.
""").strip()


def call_llm_overview_validator_after_edit(
    new_overview: str,
    diff_summary: str,
    timeout: int = 120,
) -> Tuple[str, Dict[str, Any]]:
    """
    Validate Chapters Overview after edit using LLM.
    
    Returns:
        ("OK", {}) - no issues found
        ("ISSUES", {"numbering": {...}, "deleted": {...}}) - issues found
        ("ERROR", {"error": message}) - request failed
        ("UNKNOWN", {"raw": content}) - invalid response format after retries
    """
    prompt = _VALIDATOR_PROMPT.format(
        new_overview=new_overview or "(empty)",
        diff_summary=diff_summary or "(no changes)",
    )

    messages = [
        {"role": "system", "content": "You are a precise chapters overview validator. Output valid JSON only."},
        {"role": "user", "content": prompt},
    ]

    task_params = settings_manager.get_task_params("overview_validator_after_edit")
    retries = task_params.get("retries", 3)
    if retries is None:
        retries = 3
    retries = max(0, int(retries))

    last_error = None
    last_raw = None

    for attempt in range(retries + 1):
        try:
            content = provider_manager.get_llm_response(
                task_name="overview_validator_after_edit",
                messages=messages
            )
        except Exception as e:
            last_error = str(e)
            if attempt < retries:
                continue
            return ("ERROR", {"error": str(last_error)})

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            last_raw = content
            if attempt < retries:
                continue
            return ("UNKNOWN", {"raw": last_raw or "(no response)"})

        numbering = parsed.get("numbering", {})
        deleted = parsed.get("deleted", {})
        added = parsed.get("added", {})

        if not isinstance(numbering, dict) or not isinstance(deleted, dict) or not isinstance(added, dict):
            last_raw = content
            continue

        numbering_valid = numbering.get("valid", True)
        deleted_detected = deleted.get("detected", False)
        added_detected = added.get("detected", False)

        if numbering_valid and not deleted_detected and not added_detected:
            return ("OK", {})

        return ("ISSUES", {
            "numbering": numbering,
            "deleted": deleted,
            "added": added,
        })

    if last_error:
        return ("ERROR", {"error": last_error})

    return ("UNKNOWN", {"raw": last_raw or "(no response)"})

