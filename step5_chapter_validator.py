# -*- coding: utf-8 -*-
"""
step5_chapter_validator.py

Validates each generated chapter against the expanded plot and previous chapters.
"""

import os
import textwrap
import requests

LOCAL_API_URL = os.getenv("LMSTUDIO_API_URL", "http://127.0.0.1:1234/v1/chat/completions")
MODEL_NAME = os.getenv("LMSTUDIO_MODEL", "phi-3-mini-4k-instruct")

GEN_PARAMS = {
    "temperature": 0.3,
    "top_p": 0.9,
    "max_tokens": 1000,
}

VALIDATION_PROMPT = textwrap.dedent("""
You are a critical but balanced literary editor.
Task: Evaluate the newly written chapter against the global story plan.

Inputs:
- Expanded Plot (the 2-page summary that defines the entire story):
\"\"\"{expanded_plot}\"\"\"

- Chapters Overview (titles + short descriptions):
\"\"\"{chapters_overview}\"\"\"

- Previous Chapters (if any):
\"\"\"{previous_chapters_summary}\"\"\"

- Current Chapter (to validate):
\"\"\"{current_chapter}\"\"\"

Your task:
1. Check if the current chapter fits the global plot and its designated description.
2. Check for logical consistency with earlier chapters (characters, tone, events, timeline).
3. Be fair: minor stylistic or pacing differences are acceptable.
4. If everything fits reasonably well, respond with:

RESULT: OK
REASONING: short explanation.

Otherwise, respond with:

RESULT: NOT OK
SUGGESTIONS: bullet-point improvements or corrections that should be applied when regenerating the chapter.

Keep the format strictly like this:
RESULT: <OK / NOT OK>
<REASONING or SUGGESTIONS...>
""").strip()


def _summarize_previous(previous_texts, max_chars=1200):
    if not previous_texts:
        return "None"
    snippets = []
    for i, txt in enumerate(previous_texts):
        snippet = txt[:300].replace("\n", " ").strip()
        snippets.append(f"Chapter {i+1} excerpt: {snippet}...")
        if sum(len(s) for s in snippets) > max_chars:
            break
    return "\n".join(snippets)


def validate_chapter(expanded_plot, chapters_overview, previous_chapters, current_chapter, current_index, local_api_url=None):
    url = local_api_url or LOCAL_API_URL
    previous_summary = _summarize_previous(previous_chapters or [])

    prompt = VALIDATION_PROMPT.format(
        expanded_plot=expanded_plot,
        chapters_overview=chapters_overview,
        previous_chapters_summary=previous_summary,
        current_chapter=current_chapter,
    )

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are a story structure and consistency validator."},
            {"role": "user", "content": prompt},
        ],
        **GEN_PARAMS,
    }

    try:
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        if "RESULT: OK" in content.upper():
            return "OK", content
        elif "RESULT: NOT OK" in content.upper():
            return "NOT OK", content
        else:
            return "UNKNOWN", content
    except Exception as e:
        return "ERROR", str(e)
