# -*- coding: utf-8 -*-
import os
import textwrap
import json
import requests

LOCAL_API_URL = os.environ.get("LMSTUDIO_API_URL", "http://127.0.0.1:1234/v1/chat/completions")

DEFAULT_PARAMS = {
    "temperature": 0.6,
    "top_p": 0.9,
    "max_tokens": 800,
}

PROMPT_TEMPLATE = textwrap.dedent("""
You are a story structure analyst. 
Your task is to verify if a list of proposed chapters is coherent and consistent with the story described below. 
Be moderately critical: ignore minor inconsistencies in style or small overlaps, but identify clear contradictions or missing logic.

Instructions:
1. Compare the provided "Plot Summary" and "Chapters Proposal".
2. If the chapters align well with the plot, simply answer: "OK".
3. If there are issues, answer:
   "NOT OK" 
   and provide a short list of corrections or high-level suggestions (maximum 5 sentences) focused ONLY on improving the chapters (not the plot summary).

---

PLOT SUMMARY:
\"\"\"{plot}\"\"\"

CHAPTERS PROPOSAL:
\"\"\"{chapters}\"\"\"
""")

def validate_chapters(plot, chapters, iteration=1, local_api_url=None, params=None):
    """Validate if chapters fit the plot; return ('OK', None) or ('NOT OK', suggestions)."""
    params = params or DEFAULT_PARAMS
    url = local_api_url or LOCAL_API_URL

    payload = {
        "model": "phi-3-mini-4k-instruct",
        "messages": [
            {"role": "system", "content": "You are a logical story structure validator."},
            {"role": "user", "content": PROMPT_TEMPLATE.format(plot=plot, chapters=chapters)}
        ],
        **params
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
        # Extract suggestions (everything after the "NOT OK" line)
        suggestions = content.split("\n", 1)[1].strip() if "\n" in content else "(no details provided)"
        return ("NOT OK", suggestions)
    else:
        return ("UNKNOWN", content)
