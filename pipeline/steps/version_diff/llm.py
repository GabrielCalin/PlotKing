# -*- coding: utf-8 -*-
# pipeline/steps/version_diff/llm.py
"""
LLM-only comparator pentru două versiuni ale unei secțiuni: primește toate intrările ca argumente,
apelează modelul, și întoarce (result, diff_details).
"""

import os
import textwrap
import requests
from typing import Tuple

LOCAL_API_URL = os.getenv("LMSTUDIO_API_URL", "http://127.0.0.1:1234/v1/chat/completions")
MODEL_NAME = os.getenv("LMSTUDIO_MODEL", "phi-3-mini-4k-instruct")

GEN_PARAMS = {
    "temperature": 0.3,
    "top_p": 0.9,
    "max_tokens": 2000,
}

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

3. **Output format**: You must respond in one of these exact formats:

If ONLY minor changes (spelling, punctuation, formatting) are detected:
RESULT: NO_CHANGES
MESSAGE: no major changes detected

If there are meaningful differences:
RESULT: MINOR_CHANGES
CHANGES:
- Brief description of change 1
- Brief description of change 2

If there are significant structural or content changes:
RESULT: MAJOR_CHANGES
CHANGES:
- Brief description of major change 1
- Brief description of major change 2

Keep the response concise. Focus only on describing what changed, not on what needs to be adapted.
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
) -> Tuple[str, str]:
    """
    Compară două versiuni ale unei secțiuni și returnează diferențele.
    
    Returnează:
      ("NO_CHANGES", message)      – doar modificări minore detectate
      ("MINOR_CHANGES", details)   – modificări minore dar cu impact
      ("MAJOR_CHANGES", details)   – modificări majore detectate
      ("UNKNOWN", raw)             – dacă formatul nu e recunoscut
      ("ERROR", message)           – dacă a eșuat requestul
    """
    url = api_url or LOCAL_API_URL
    model = model_name or MODEL_NAME

    prompt = _DIFF_PROMPT.format(
        section_type=section_type or "unknown",
        original_version=original_version or "",
        modified_version=modified_version or "",
        genre=genre or "unspecified",
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a precise text comparison system that identifies meaningful differences between document versions."},
            {"role": "user", "content": prompt},
        ],
        **GEN_PARAMS,
    }

    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        content = (
            data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
        )
    except Exception as e:
        return ("ERROR", str(e))

    up = content.upper()
    if "RESULT: NO_CHANGES" in up:
        return ("NO_CHANGES", content)
    if "RESULT: MINOR_CHANGES" in up:
        return ("MINOR_CHANGES", content)
    if "RESULT: MAJOR_CHANGES" in up:
        return ("MAJOR_CHANGES", content)
    return ("UNKNOWN", content)

