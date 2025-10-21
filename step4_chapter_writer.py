# -*- coding: utf-8 -*-
"""
step4_chapter_writer.py

Generates the full text for a specific chapter based on:
- Expanded Plot
- Chapters Overview
- Previously written chapters (if any)
- Current Chapter Number

The model will identify the correct chapter description from the overview
based on the chapter number, and write that chapter only.
"""

import os
import textwrap
import requests

LOCAL_API_URL = os.getenv("LMSTUDIO_API_URL", "http://127.0.0.1:1234/v1/chat/completions")
MODEL_NAME = os.getenv("LMSTUDIO_MODEL", "phi-3-mini-4k-instruct")

GEN_PARAMS = {
    "temperature": 0.8,
    "top_p": 0.95,
    "max_tokens": 4000,
}


CHAPTER_PROMPT_TEMPLATE = textwrap.dedent("""
You are an expert long-form fiction writer.

Task:
Write **only** Chapter {chapter_number} of the story, using the following materials.

Inputs:
- Global Story Summary (the authoritative plot):
\"\"\"{expanded_plot}\"\"\"

- Chapters Overview (titles + short descriptions of all chapters):
\"\"\"{chapters_overview}\"\"\"

- Previously Written Chapters (if any, may be empty):
\"\"\"{previous_chapters_summary}\"\"\"

Your job:
1. Locate in the chapters overview the description that corresponds to **Chapter {chapter_number}**.
2. Write the **complete text** for that chapter, following its description exactly in tone, purpose, and key events.
3. Ensure logical continuity with previous chapters (characters, timeline, motivations).  
   - If there are no previous chapters, start naturally from the story’s beginning.
4. Maintain a clear and structured prose style, but allow natural dialogue and occasional expressive language where it enhances the scene.
5. Target length: long-form (approx. 2500–5000 words). If the model cannot produce that many tokens, create the most coherent chapter possible within limits.
6. End with a natural chapter conclusion (not mid-scene or mid-sentence).
7. Do not include chapter headers, outlines, or meta commentary — only the story text itself.

{feedback_section}

Begin writing Chapter {chapter_number} now.
""").strip()


def _join_previous_chapters(previous_texts):
    """Concatenate all previous chapters in full for model context."""
    if not previous_texts:
        return "None"
    joined = []
    for idx, txt in enumerate(previous_texts):
        joined.append(f"Chapter {idx+1}:\n{txt.strip()}\n")
    return "\n\n".join(joined)


def generate_chapter_text(expanded_plot: str,
                          chapters_overview: str,
                          chapter_index: int,
                          previous_chapters=None,
                          local_api_url=None,
                          model_name=None,
                          feedback=None):
    """
    Generates the full text for chapter `chapter_index` (1-based index).
    - expanded_plot: the full 2-page story summary
    - chapters_overview: chapter titles + descriptions
    - chapter_index: integer index (1-based)
    - previous_chapters: list of strings (optional)
    - feedback: optional feedback string to guide regeneration
    """
    url = local_api_url or LOCAL_API_URL
    model = model_name or MODEL_NAME

    previous_joined = _join_previous_chapters(previous_chapters or [])
    feedback_section = ""
    if feedback:
        feedback_section = f"\n\nAdditional reviewer feedback to address:\n\"\"\"{feedback}\"\"\"\n"

    prompt = CHAPTER_PROMPT_TEMPLATE.format(
        expanded_plot=expanded_plot,
        chapters_overview=chapters_overview,
        previous_chapters_summary=previous_joined,
        chapter_number=chapter_index,
        feedback_section=feedback_section
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a professional fiction ghostwriter creating coherent novel chapters."},
            {"role": "user", "content": prompt}
        ],
        "temperature": GEN_PARAMS.get("temperature", 0.8),
        "top_p": GEN_PARAMS.get("top_p", 0.95),
        "max_tokens": GEN_PARAMS.get("max_tokens", 4000),
    }

    try:
        r = requests.post(url, json=payload, timeout=3600)
        r.raise_for_status()
        data = r.json()

        if "choices" in data and data["choices"]:
            content = (
                data["choices"][0].get("message", {}).get("content")
                or data["choices"][0].get("text")
            )
            if not content:
                return "Error: model returned empty content"
            return content.strip()
        return str(data)
    except Exception as e:
        return f"Error during chapter generation: {e}"
