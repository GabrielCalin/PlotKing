# -*- coding: utf-8 -*-
import os
import textwrap
import json
import requests

LOCAL_API_URL = os.environ.get("LMSTUDIO_API_URL", "http://127.0.0.1:1234/v1/chat/completions")

DEFAULT_PARAMS = {
    "temperature": 0.6,
    "top_p": 0.9,
    "max_tokens": 1000,
}

PROMPT_TEMPLATE = textwrap.dedent("""
You are a story structure analyst.
Your task is to verify if a list of proposed chapters is coherent and consistent with the story described below.

Be moderately critical: ignore minor inconsistencies in style or small overlaps, but identify clear contradictions or missing logic.

Instructions:
1. Compare both the "Initial Story Requirements" and the "Expanded Plot Summary" with the proposed chapters.
2. Prioritize consistency with the Expanded Plot, but also ensure that the Initial Requirements are not contradicted.
3. If the chapters align well with the story, answer exactly: "OK".
4. If there are issues, answer:
   "NOT OK"
   and provide a concise list of high-level corrections or suggestions (max 5 sentences) focused ONLY on improving the chapters (not rewriting the plot).

---

INITIAL STORY REQUIREMENTS:
\"\"\"{initial_plot}\"\"\"

EXPANDED PLOT SUMMARY:
\"\"\"{expanded_plot}\"\"\"

CHAPTERS PROPOSAL:
\"\"\"{chapters}\"\"\"
""")

def validate_chapters(initial_plot, expanded_plot, chapters, iteration=1, local_api_url=None, params=None):
    """
    Validate if the proposed chapters fit the expanded plot (main source)
    and are still aligned with the user's initial story idea.
    Returns:
        ("OK", None) if valid,
        ("NOT OK", suggestions) otherwise,
        ("ERROR", msg) on request failure.
    """
    params = params or DEFAULT_PARAMS
    url = local_api_url or LOCAL_API_URL

    payload = {
        "model": "phi-3-mini-4k-instruct",
        "messages": [
            {"role": "system", "content": "You are a logical story structure validator."},
            {
                "role": "user",
                "content": PROMPT_TEMPLATE.format(
                    initial_plot=initial_plot,
                    expanded_plot=expanded_plot,
                    chapters=chapters
                ),
            },
        ],
        **params,
    }

    try:
        r = requests.post(url, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return ("ERROR", f"Validation request failed: {e}")

    if content.upper().startswith("OK"):
        return ("OK", None)
    elif content.upper().startswith("NOT OK"):
        suggestions = content.split("\n", 1)[1].strip() if "\n" in content else "(no details provided)"
        return ("NOT OK", suggestions)
    else:
        return ("UNKNOWN", content)
