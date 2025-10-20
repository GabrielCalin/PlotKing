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
You are a balanced and analytical literary editor.

Task:
Evaluate whether the **Current Chapter** aligns with its intended description inside the **Chapters Overview**, and whether it remains logically consistent with the story so far.

Inputs:
- Global Plot Summary (overall context of the story):
\"\"\"{expanded_plot}\"\"\"

- Chapters Overview (contains all chapter titles and descriptions, including the target one):
\"\"\"{chapters_overview}\"\"\"

- Previous Chapters (if any, may be empty):
\"\"\"{previous_chapters_summary}\"\"\"

- Current Chapter (to validate):
\"\"\"{current_chapter}\"\"\"

Your job:
1. Locate in the chapters overview the description corresponding to this chapter (match by its number or title).
2. Evaluate if the current chapter **matches that description** in tone, structure, and main events.
3. Check for **logical continuity** with previous chapters (characters, world state, timeline).  
   - If no previous chapters exist, skip this check.
4. Small stylistic or pacing deviations are acceptable.
5. Respond exactly in one of the following formats:

If everything fits reasonably well:

RESULT: OK
REASONING: brief explanation.

Otherwise:

RESULT: NOT OK
SUGGESTIONS:
- bullet-point list of improvements or adjustments needed for better alignment.

Keep your answer concise and strictly formatted as above.
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
