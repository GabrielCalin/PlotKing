# -*- coding: utf-8 -*-
# pipeline/steps/chapter_validator/llm.py
"""
LLM-only validator pentru un capitol: primește toate intrările ca argumente,
apelează modelul, și întoarce (result, details).
"""


import textwrap
from typing import List, Tuple
from provider import provider_manager




_VALIDATION_PROMPT = textwrap.dedent("""\
You are a balanced and analytical literary editor.

Task:
Evaluate whether the **current chapter (Chapter {chapter_number})** aligns with its own description inside the **Chapters Overview**, and whether it remains logically consistent with the story so far and the overall plot structure.

Inputs:
- Global Plot Summary (overall context of the story):
\"\"\"{expanded_plot}\"\"\"
- Chapters Overview (contains all chapter titles and descriptions, including the target one):
\"\"\"{chapters_overview}\"\"\"
- Previous Chapters (if any, may be empty):
\"\"\"{previous_chapters_summary}\"\"\"
- Current Chapter (to validate):
\"\"\"{current_chapter}\"\"\"
- GENRE (to guide tone, pacing, and atmosphere):
\"\"\"{genre}\"\"\"

Your job:
1. In the "Chapters Overview", **find the description that corresponds to Chapter {chapter_number}**.
2. Evaluate if the current chapter **matches that description** in tone, events, structure, and purpose.
3. Check for **logical continuity**:
   - It must align with previous chapters (characters, motivations, timeline, world state).
   - It must **NOT include or foreshadow content from future chapters**. If it does, the chapter is NOT OK.
   - Ensure there are no unjustified time jumps or contradictions.
4. Confirm that all **key elements from the chapter’s description** are present.
5. Verify that the chapter **advances the story** rather than stalling it.
6. Consider the **GENRE** when judging consistency of tone, pacing, and atmosphere.
7. Respond in one of the following strict formats:

If everything fits reasonably well:

RESULT: OK
REASONING: short explanation.

Otherwise:

RESULT: NOT OK
SUGGESTIONS:
- bullet-point list of fixes.

Keep the response concise and formatted exactly like shown above.
""").strip()


def _summarize_previous(previous_texts: List[str], max_chars: int = 1200) -> str:
    if not previous_texts:
        return "None"
    snippets = []
    total = 0
    for i, txt in enumerate(previous_texts):
        snippet = (txt or "")[:300].replace("\n", " ").strip()
        s = f"Chapter {i+1} excerpt: {snippet}..."
        total += len(s)
        if total > max_chars:
            break
        snippets.append(s)
    return "\n".join(snippets) if snippets else "None"


def call_llm_validate_chapter(
    expanded_plot: str,
    chapters_overview: str,
    previous_chapters: List[str],
    current_chapter: str,
    current_index: int,
    genre: str,
    *,
    api_url: str = None,
    model_name: str = None,
    timeout: int = 300,
) -> Tuple[str, str]:
    """
    Returnează:
      ("OK", details)        – când e valid
      ("NOT OK", details)    – când trebuie corectat
      ("UNKNOWN", raw)       – dacă formatul nu e recunoscut
      ("ERROR", message)     – dacă a eșuat requestul
    """

    previous_summary = _summarize_previous(previous_chapters or [])


    prompt = _VALIDATION_PROMPT.format(
        expanded_plot=expanded_plot or "",
        chapters_overview=chapters_overview or "",
        previous_chapters_summary=previous_summary,
        current_chapter=current_chapter or "",
        chapter_number=current_index,
        genre=genre or "unspecified",
    )

    messages = [
        {"role": "system", "content": "You are a balanced story structure and continuity validator."},
        {"role": "user", "content": prompt},
    ]

    try:
        content = provider_manager.get_llm_response(
            task_name="chapter_validator",
            messages=messages
        )
    except Exception as e:
        return ("ERROR", str(e))

    up = content.upper()
    if "RESULT: OK" in up:
        return ("OK", content)
    if "RESULT: NOT OK" in up:
        return ("NOT OK", content)
    return ("UNKNOWN", content)

