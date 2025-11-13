# -*- coding: utf-8 -*-
# pipeline/steps/chapter_editor/llm.py
"""
LLM helper pentru editarea unui capitol bazat pe impact și diff.
"""

import os
import textwrap
import requests
import json
from typing import List, Optional

LOCAL_API_URL = os.getenv("LMSTUDIO_API_URL", "http://127.0.0.1:1234/v1/chat/completions")
MODEL_NAME = os.getenv("LMSTUDIO_MODEL", "phi-3-mini-4k-instruct")

GEN_PARAMS = {
    "temperature": 0.8,
    "top_p": 0.95,
    "max_tokens": 8000,
}

_EDIT_CHAPTER_PROMPT = textwrap.dedent("""\
You are an expert fiction editor specializing in adapting chapters to maintain continuity after story changes.

Context:
A user made an edit to a section of the story. This edit has been analyzed, and Chapter {chapter_number} needs to be updated to reflect the impact of that change.

Inputs:
- **Global Story Summary (authoritative plot):**
\"\"\"{expanded_plot}\"\"\"
- **Chapters Overview (titles + short descriptions of all chapters):**
\"\"\"{chapters_overview}\"\"\"
- **Previously Written Chapters (before this one):**
\"\"\"{previous_chapters_summary}\"\"\"
- **Current Chapter {chapter_number} (to be edited):**
\"\"\"{original_chapter}\"\"\"
- **CHANGES DETECTED IN USER'S EDIT:**
\"\"\"{diff_summary}\"\"\"
- **IMPACT REASON (why this chapter needs adaptation):**
\"\"\"{impact_reason}\"\"\"
- **GENRE** (to guide tone, pacing, and atmosphere):
\"\"\"{genre}\"\"\"

Task:
1. First, analyze the impact and changes to determine if this is a BREAKING CHANGE:
   - A breaking change requires significant restructuring, contradicts established facts, or fundamentally alters the story's direction
   - A non-breaking change can be accommodated with minimal modifications while preserving most of the original content

2. Then, adapt Chapter {chapter_number} accordingly:
   - If BREAKING CHANGE: Significant modifications are allowed, but preserve as much of the original chapter content as possible. Only change what is necessary to address the breaking change.
   - If NON-BREAKING CHANGE: Make MINIMAL modifications — only what is strictly necessary. Preserve the vast majority of the original chapter text unchanged.

Specific Instructions:
1. Locate in the Chapters Overview the exact description that corresponds to **Chapter {chapter_number}**.
   - Use its **title exactly as written** at the start of the chapter, formatted as a **Markdown H2 heading** (`##`).
   - Do **not** invent or alter the title in any way.
2. Review the original chapter text and identify what needs to change based on the impact reason.
3. Maintain **logical continuity**:
   - Keep consistency with **previous chapters** (characters, setting, timeline, motivations, tone).
   - Ensure smooth transition to the **next chapter**.
   - Do **not** include or foreshadow events that explicitly belong to future chapters.
4. Preserve the chapter's role, purpose, and position in the story arc.
5. Maintain a clear, engaging, and immersive prose style appropriate for long-form fiction.
6. Adapt writing style, pacing, and atmosphere to match the **GENRE** conventions.
7. Target length: approximately the same as the original chapter (±10%).

You must output a JSON object with the following structure:
{{
  "is_breaking_change": true/false,
  "adapted_chapter": "the complete adapted Chapter {chapter_number} text in Markdown format"
}}

Output ONLY the JSON object, no other text or explanations.
""").strip()


def _join_previous_chapters(previous_texts: Optional[List[str]]) -> str:
    if not previous_texts:
        return "None"
    parts = []
    for idx, txt in enumerate(previous_texts):
        parts.append(f"Chapter {idx+1}:\n{(txt or '').strip()}\n")
    return "\n\n".join(parts)


def call_llm_edit_chapter(
    expanded_plot: str,
    chapters_overview: str,
    chapter_index: int,
    previous_chapters: Optional[List[str]],
    original_chapter: str,
    impact_reason: str,
    diff_summary: str,
    genre: str = "",
    anpc: Optional[int] = None,
    *,
    api_url: Optional[str] = None,
    model_name: Optional[str] = None,
    timeout: int = 3600,
) -> str:
    """
    Editează un capitol bazat pe impact și diff.
    AI-ul determină dacă e breaking change și adaptează în consecință.
    """
    url = api_url or LOCAL_API_URL
    model = model_name or MODEL_NAME
    prev_joined = _join_previous_chapters(previous_chapters or [])

    prompt = _EDIT_CHAPTER_PROMPT.format(
        expanded_plot=expanded_plot or "",
        chapters_overview=chapters_overview or "",
        previous_chapters_summary=prev_joined,
        original_chapter=original_chapter or "",
        diff_summary=diff_summary or "",
        impact_reason=impact_reason or "",
        genre=genre or "unspecified",
        chapter_number=chapter_index,
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a precise fiction editor that adapts chapters while preserving as much original content as possible. You must output only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        **GEN_PARAMS,
    }

    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        
        # Parse JSON response
        try:
            result = json.loads(content)
            return result.get("adapted_chapter", content)
        except json.JSONDecodeError:
            # Fallback dacă nu e JSON valid
            return content
    except Exception as e:
        return f"Error during chapter editing: {e}"

