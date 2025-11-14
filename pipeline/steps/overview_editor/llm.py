# -*- coding: utf-8 -*-
# pipeline/steps/overview_editor/llm.py
"""
LLM helper pentru editarea Chapters Overview bazat pe impact și diff.
"""

import os
import textwrap
import requests
import json
from utils.json_utils import extract_json_from_response

LOCAL_API_URL = os.getenv("LMSTUDIO_API_URL", "http://127.0.0.1:1234/v1/chat/completions")
MODEL_NAME = os.getenv("LMSTUDIO_MODEL", "phi-3-mini-4k-instruct")

GEN_PARAMS = {
    "temperature": 0.6,
    "top_p": 0.95,
    "max_tokens": 4096,
}

_EDIT_OVERVIEW_PROMPT = textwrap.dedent("""\
You are an expert book structure editor specializing in adapting chapter overviews to maintain continuity after changes.

Context:
A user made an edit to a section of the story. This edit has been analyzed, and the Chapters Overview needs to be updated to reflect the impact of that change.

ORIGINAL CHAPTERS OVERVIEW:
\"\"\"{original_overview}\"\"\"

EXPANDED PLOT (reference):
\"\"\"{expanded_plot}\"\"\"

CHANGES DETECTED IN USER'S EDIT:
\"\"\"{diff_summary}\"\"\"

IMPACT REASON (why this section needs adaptation):
\"\"\"{impact_reason}\"\"\"

GENRE:
\"\"\"{genre}\"\"\"

Task:
1. First, analyze the impact and changes to determine if this is a BREAKING CHANGE:
   - A breaking change requires significant restructuring, contradicts established facts, or fundamentally alters the story's direction
   - A non-breaking change can be accommodated with minimal modifications while preserving most of the original content

2. Then, adapt the Chapters Overview accordingly:
   - If BREAKING CHANGE: Significant modifications are allowed, but preserve as much of the original overview as possible. Only change what is necessary to address the breaking change.
   - If NON-BREAKING CHANGE: Make MINIMAL modifications — only what is strictly necessary. Preserve the vast majority of the original text unchanged.

Output Requirements:
- Maintain the same Markdown format as the original (#### Chapter N: *Title* followed by **Description:**)
- Preserve the same number of chapters
- Keep chapter titles unchanged unless the impact requires title updates
- Preserve all chapter descriptions that are not affected by the changes
- Update only the parts that need to change based on the impact
- Ensure the adapted overview remains coherent with the Expanded Plot

You must output a JSON object with the following structure:
{{
  "is_breaking_change": true/false,
  "adapted_overview": "the complete adapted Chapters Overview in Markdown format"
}}

Output ONLY the JSON object, no other text or explanations.
""").strip()


def call_llm_edit_overview(
    original_overview: str,
    impact_reason: str,
    diff_summary: str,
    expanded_plot: str,
    genre: str = "",
    *,
    api_url: str = None,
    model_name: str = None,
    timeout: int = 300,
) -> str:
    """
    Editează Chapters Overview bazat pe impact și diff.
    AI-ul determină dacă e breaking change și adaptează în consecință.
    """
    url = api_url or LOCAL_API_URL
    model = model_name or MODEL_NAME

    prompt = _EDIT_OVERVIEW_PROMPT.format(
        original_overview=original_overview or "",
        expanded_plot=expanded_plot or "",
        diff_summary=diff_summary or "",
        impact_reason=impact_reason or "",
        genre=genre or "unspecified",
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a precise story structure editor that adapts chapter overviews while preserving as much original content as possible. You must output only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        **GEN_PARAMS,
    }

    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        
        # Parse JSON response (suportă atât JSON pur cât și wrappat în tag-uri)
        try:
            result = extract_json_from_response(content)
            return result.get("adapted_overview", content)
        except (json.JSONDecodeError, ValueError):
            # Fallback dacă nu e JSON valid
            return content
    except Exception as e:
        return f"Error during overview editing: {e}"

