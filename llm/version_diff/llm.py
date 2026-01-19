# -*- coding: utf-8 -*-
# pipeline/steps/version_diff/llm.py
"""
LLM-only comparator pentru două versiuni ale unei secțiuni: primește toate intrările ca argumente,
apelează modelul, și întoarce (result, diff_details).
"""


import json
import textwrap
from typing import Tuple, Dict, Any
from provider import provider_manager


_DIFF_PROMPT = textwrap.dedent("""\
You are an analytical text comparison system designed to identify meaningful differences between two versions of the same section.

Task:
Compare the ORIGINAL VERSION and MODIFIED VERSION of a section and identify all significant differences. Your output will be used by another system to determine if other sections need to be adapted.

Section Type: {section_type}
Genre: {genre}

ORIGINAL VERSION:
\"\"\"{original_version}\"\"\"

MODIFIED VERSION:
\"\"\"{modified_version}\"\"\"

Instructions:
1. **Ignore minor changes**: Spelling corrections, punctuation fixes, minor word substitutions that don't change meaning, formatting changes, and cosmetic edits should be completely ignored.

2. **Identify major changes**: Focus on changes that could impact other sections:
   - Changes to plot points, story events, or narrative structure
   - Changes to character descriptions, motivations, or relationships
   - Changes to chapter descriptions or summaries (in chapters overview)
   - Changes to chapter content that affect continuity (in individual chapters)
   - Changes to world-building elements, settings, or timeline
   - Additions or removals of significant content
   - Changes to tone, pacing, or genre elements

3. **Output format (strict JSON)**: You must respond with a single JSON object and nothing else.

If ONLY minor changes (spelling, punctuation, formatting) are detected, respond exactly like this:
{{
  "result": "NO_CHANGES",
  "message": "no major changes detected"
}}

If there are meaningful differences, respond exactly like this:
{{
  "result": "CHANGES_DETECTED",
  "changes": [
    "Brief description of change 1",
    "Brief description of change 2"
  ]
}}

- The JSON must include only the keys shown above.
- The `changes` array must contain natural-language bullet descriptions of each significant change.
- Do not add any extra text before or after the JSON.
""").strip()


def call_llm_version_diff(
    section_type: str,
    original_version: str,
    modified_version: str,
    genre: str = "",
    *,
    api_url: str = None,
    model_name: str = None,
    timeout: int = 300,
) -> Tuple[str, Dict[str, Any]]:
    """
    Compară două versiuni ale unei secțiuni și returnează diferențele.
    
    Returnează:
      ("NO_CHANGES", data)      – doar modificări minore detectate (data conține cheia "message")
      ("CHANGES_DETECTED", data) – modificări semnificative detectate (data conține cheia "changes")
      ("UNKNOWN", {"raw": content})              – dacă formatul nu e recunoscut
      ("ERROR", {"error": message})            – dacă a eșuat requestul
    """


    prompt = _DIFF_PROMPT.format(
        section_type=section_type or "unknown",
        original_version=original_version or "",
        modified_version=modified_version or "",
        genre=genre or "unspecified",
    )


    messages = [
        {"role": "system", "content": "You are a precise text comparison system that identifies meaningful differences between document versions."},
        {"role": "user", "content": prompt},
    ]

    try:
        content = provider_manager.get_llm_response(
            task_name="version_diff",
            messages=messages
        )
    except Exception as e:
        return ("ERROR", {"error": str(e)})

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return ("UNKNOWN", {"raw": content})

    result = parsed.get("result")
    if result in {"NO_CHANGES", "CHANGES_DETECTED"}:
        if result == "NO_CHANGES" and "message" not in parsed:
            parsed["message"] = "no major changes detected"
        if result == "CHANGES_DETECTED" and "changes" not in parsed:
            parsed["changes"] = []
        return (result, parsed)

    return ("UNKNOWN", {"raw": content})


