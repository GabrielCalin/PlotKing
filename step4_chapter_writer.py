# -*- coding: utf-8 -*-
"""
step4_chapter_writer.py

Provides generate_chapter_text(expanded_plot, chapters_overview, chapter_index)
which returns the full text of the requested chapter as a single string.

This implementation assumes LM Studio (OpenAI-compatible) at LOCAL_API_URL.
Adjust MODEL_NAME and LOCAL_API_URL via environment variables if needed.
"""

import os
import textwrap
import requests

LOCAL_API_URL = os.getenv("LMSTUDIO_API_URL", "http://127.0.0.1:1234/v1/chat/completions")
MODEL_NAME = os.getenv("LMSTUDIO_MODEL", "phi-3-mini-4k-instruct")

# Generation params - adjust if your local model needs different keys
GEN_PARAMS = {
    "temperature": 0.8,
    "top_p": 0.95,
    "max_tokens": 4000,   # may need tuning per model; corresponds roughly to desired length
}


CHAPTER_PROMPT_TEMPLATE = textwrap.dedent("""
You are an expert long-form fiction writer tasked with producing one complete chapter.

Context:
- Expanded story summary (the authoritative plot):
\"\"\"{expanded_plot}\"\"\"

- Chapter list / overview (titles + short descriptions):
\"\"\"{chapters_overview}\"\"\"

- Chapters already written (if any, truncated):
\"\"\"{previous_chapters_summary}\"\"\"

Task:
Write the complete text for Chapter {chapter_number}: "{chapter_title}".
Requirements:
- Write in a neutral, clear narrative style (avoid ornate metaphors and extended lyrical passages).
- The chapter must logically follow the provided plot and previously written chapters.
- Target length: long-form (approx. 2500–5000 words). If your model cannot produce that many tokens in one call, produce the maximum coherent text possible that completes a clear chapter arc.
- Finish the chapter with a natural chapter ending (not mid-sentence or mid-scene).
- Do not include section headers or meta commentary — only story text.

Begin writing the chapter text now.
""").lstrip()


def _build_previous_summary(previous_texts, max_chars=1000):
    if not previous_texts:
        return "None"
    # Provide a short context summary: titles + first ~300 chars of each existing chapter
    parts = []
    for idx, txt in enumerate(previous_texts):
        snippet = txt[:300].replace("\n", " ").strip()
        parts.append(f"Chapter {idx+1} excerpt: {snippet}...")
        if sum(len(p) for p in parts) > max_chars:
            break
    return "\n".join(parts)


def generate_chapter_text(expanded_plot: str, chapters_overview: str, chapter_index: int, previous_chapters=None, local_api_url=None, model_name=None, feedback=None):
    """
    Generate the full text for chapter `chapter_index` (1-based index).
    - expanded_plot: the two-page plot summary (string)
    - chapters_overview: the chapters list string (as returned by step2)
    - chapter_index: integer (1-based)
    - previous_chapters: optional list of full chapter texts already generated (strings)
    Returns: str (chapter text) or an error message starting with "Error:"
    """
    try:
        chapter_idx_zero_based = int(chapter_index) - 1
        if chapter_idx_zero_based < 0:
            return "Error: chapter_index must be >= 1"
    except Exception:
        return "Error: invalid chapter_index"

    # Resolve endpoints / model
    url = local_api_url or LOCAL_API_URL
    model = model_name or MODEL_NAME

    # Extract chapter title from overview:
    # Try to find the line corresponding to the requested chapter.
    lines = [ln.strip() for ln in chapters_overview.splitlines() if ln.strip()]
    # naive heuristic: look for "Chapter N:" or the N-th item in a numbered list
    title = f"Chapter {chapter_index}"
    chapter_title_found = None
    # First search for a line starting with "Chapter {N}:" or "Chapter {N} -"
    for ln in lines:
        low = ln.lower()
        if low.startswith(f"chapter {chapter_index}:") or low.startswith(f"chapter {chapter_index} -") or low.startswith(f"{chapter_index}. "):
            # parse after colon or dash
            if ":" in ln:
                chapter_title_found = ln.split(":", 1)[1].strip()
            elif "-" in ln:
                chapter_title_found = ln.split("-", 1)[1].strip()
            else:
                chapter_title_found = ln.split(maxsplit=1)[1].strip() if len(ln.split())>1 else ln
            break
    # fallback: if there's a numbered list where titles are every other line, try nth chunk
    if chapter_title_found is None:
        # try grouping by numbered headings "Chapter 1:" etc
        for ln in lines:
            if ln.lower().startswith("chapter"):
                parts = ln.split(":", 1)
                if len(parts) == 2:
                    # collect titles in order
                    pass
        # last fallback: use the first 6-8 words of the Nth non-empty line
        if chapter_idx_zero_based < len(lines):
            candidate = lines[chapter_idx_zero_based]
            # keep up to 8 words
            chapter_title_found = " ".join(candidate.split()[:8])
        else:
            chapter_title_found = title

    previous_summary = _build_previous_summary(previous_chapters or [], max_chars=1200)

    feedback_section = ""
    if feedback:
        feedback_section = f"\n\nAdditional reviewer feedback to address:\n\"\"\"{feedback}\"\"\"\n"

    prompt = CHAPTER_PROMPT_TEMPLATE.format(
        expanded_plot=expanded_plot,
        chapters_overview=chapters_overview,
        previous_chapters_summary=previous_summary,
        chapter_number=chapter_index,
        chapter_title=chapter_title_found
    ) + feedback_section

    # Build payload in OpenAI chat-completions style (LM Studio compatible)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an expert long-form fiction generator that writes coherent novel chapters."},
            {"role": "user", "content": prompt}
        ],
        "temperature": GEN_PARAMS.get("temperature", 0.8),
        "top_p": GEN_PARAMS.get("top_p", 0.95),
        "max_tokens": GEN_PARAMS.get("max_tokens", 4000),
    }

    try:
        r = requests.post(url, json=payload, timeout=600)
        r.raise_for_status()
        data = r.json()
        # standard OpenAI-like parsing
        if "choices" in data and data["choices"]:
            content = data["choices"][0].get("message", {}).get("content") or data["choices"][0].get("text")
            if content is None:
                return "Error: model returned empty content"
            return content.strip()
        # fallback
        return str(data)
    except Exception as e:
        return f"Error during chapter generation: {e}"
