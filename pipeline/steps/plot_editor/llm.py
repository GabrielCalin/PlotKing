# -*- coding: utf-8 -*-
# pipeline/steps/plot_editor/llm.py
"""
LLM helper pentru editarea Expanded Plot bazat pe impact și diff.
"""

import os
import textwrap
import requests
import json
from utils.json_utils import extract_json_from_response

LOCAL_API_URL = os.getenv("LMSTUDIO_API_URL", "http://127.0.0.1:1234/v1/chat/completions")
MODEL_NAME = os.getenv("LMSTUDIO_MODEL", "phi-3-mini-4k-instruct")

GEN_PARAMS = {
    "temperature": 0.7,
    "top_p": 0.95,
    "max_tokens": 4096,
}

_EDIT_PLOT_PROMPT = textwrap.dedent("""\
You are an expert story editor specializing in adapting story blueprints to maintain continuity after changes.

Context:
A user made an edit to a section of the story. This edit has been analyzed, and the Expanded Plot needs to be updated to reflect the impact of that change.

ORIGINAL EXPANDED PLOT:
\"\"\"{original_plot}\"\"\"

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

2. Then, adapt the Expanded Plot accordingly:
   - If BREAKING CHANGE: Significant modifications are allowed, but preserve as much of the original story as possible. Only change what is necessary to address the breaking change.
   - If NON-BREAKING CHANGE: Make MINIMAL modifications — only what is strictly necessary. Preserve the vast majority of the original text unchanged.

Output Requirements:
- Maintain the same Markdown structure as the original (Title, Key Characters, World/Setting Overview, Plot Summary)
- Preserve all sections that are not affected by the changes
- Update only the parts that need to change based on the impact
- Keep the same tone, style, and level of detail as the original
- Ensure the adapted plot remains coherent and logically consistent

You must output a JSON object with the following structure:
{{
  "is_breaking_change": true/false,
  "adapted_plot": "the complete adapted Expanded Plot in Markdown format"
}}

Output ONLY the JSON object, no other text or explanations.
""").strip()


def call_llm_edit_plot(
    original_plot: str,
    impact_reason: str,
    diff_summary: str,
    genre: str = "",
    *,
    api_url: str = None,
    model_name: str = None,
    timeout: int = 300,
) -> str:
    """
    Editează Expanded Plot bazat pe impact și diff.
    AI-ul determină dacă e breaking change și adaptează în consecință.
    
    Args:
        original_plot: Expanded Plot existent
        impact_reason: Motivul pentru care trebuie adaptat
        diff_summary: Rezumatul modificărilor detectate
        genre: Genul poveștii
    """
    url = api_url or LOCAL_API_URL
    model = model_name or MODEL_NAME

    prompt = _EDIT_PLOT_PROMPT.format(
        original_plot=original_plot or "",
        diff_summary=diff_summary or "",
        impact_reason=impact_reason or "",
        genre=genre or "unspecified",
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a precise story continuity editor that adapts story blueprints while preserving as much original content as possible. You must output only valid JSON."},
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
            return result.get("adapted_plot", content)
        except (json.JSONDecodeError, ValueError):
            # Fallback dacă nu e JSON valid
            return content
    except Exception as e:
        return f"Error during plot editing: {e}"

