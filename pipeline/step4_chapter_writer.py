# -*- coding: utf-8 -*-
"""
step4_chapter_writer.py

Generates the full text for a specific chapter based on:
- Expanded Plot
- Chapters Overview
- Previously written chapters (if any)
- Current Chapter Number
- Genre (influences style, tone, and pacing)

The model will identify the correct chapter description from the overview
based on the chapter number, and write that chapter only.
"""

import os
import textwrap
import requests
import random

LOCAL_API_URL = os.getenv("LMSTUDIO_API_URL", "http://127.0.0.1:1234/v1/chat/completions")
MODEL_NAME = os.getenv("LMSTUDIO_MODEL", "phi-3-mini-4k-instruct")

GEN_PARAMS = {
    "temperature": 0.8,
    "top_p": 0.95,
    "max_tokens": 8000,
}

CHAPTER_PROMPT_TEMPLATE = textwrap.dedent("""
You are an expert **long-form fiction writer**.

Task:
Write **only** Chapter {chapter_number} of the story, using the following materials and strict continuity rules.

Inputs:
- **Global Story Summary (authoritative plot):**
\"\"\"{expanded_plot}\"\"\"

- **Chapters Overview (titles + short descriptions of all chapters):**
\"\"\"{chapters_overview}\"\"\"

- **Previously Written Chapters (if any, may be empty):**
\"\"\"{previous_chapters_summary}\"\"\"

- **GENRE** (to guide tone, pacing, and atmosphere):
\"\"\"{genre}\"\"\"

---

### Your job
1. Before writing, mentally review the Global Story Summary and Chapters Overview to fully understand the story’s logic and timeline.
2. Locate in the Chapters Overview the exact description that corresponds to **Chapter {chapter_number}**.  
   - Use its **title exactly as written** at the start of the chapter, formatted as a **Markdown H2 heading** (`##`).  
   - Do **not** invent or alter the title in any way.
3. Write the **complete narrative text** for that chapter, following its description precisely in tone, purpose, and key events.  
   - Maintain smooth internal flow between moments without subdividing the text into numbered or titled scenes.
4. Ensure **logical continuity**.  
   - Maintain consistency with **previous chapters** (characters, setting, timeline, motivations, tone).  
   - Anticipate what will happen in the **next chapter**, ensuring seamless transition.  
   - Do **not** include or foreshadow events that explicitly belong to future chapters.  
   - Do not include flashbacks, summaries of previous events, or visions of future ones unless explicitly stated in this chapter’s overview.
5. Preserve internal continuity of all details (locations, time of day, physical states, objects, tone) introduced so far.  
   - Balance action, dialogue, and narration so that external events drive the story forward.
6. Maintain a clear, engaging, and immersive prose style appropriate for long-form fiction.  
   - Natural dialogue, expressive narration, and sensory details are encouraged.  
   - You may use **Markdown elements** (e.g., `---` for scene breaks, *italics*, or **bold**) if they enhance structure or readability, but do not label or number scenes.
7. Adapt writing style, pacing, and atmosphere to match the **GENRE** conventions (e.g., suspense rhythm for thrillers, sensory prose for romance, measured clarity for sci-fi).
8. End the chapter appropriately for its position in the book.  
   - If it is **not the final chapter**, close with a natural sense of transition or anticipation — a pause that leads smoothly into the next chapter.  
   - If it **is the final chapter**, conclude the story in a way that aligns with the **Chapters Overview** and **Global Story Summary**, providing resolution without adding new material beyond the planned ending.  
   - Do **not** comment on the chapter itself or describe that it “ends”; simply write the story up to its natural stopping point.
9. Target length: around **{word_target} words**.
10. Output **only** the final story text — no explanations, meta commentary, or outline notes.

{feedback_section}

---

Begin writing **Chapter {chapter_number}** now.
""").strip()


def _join_previous_chapters(previous_texts):
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
                          genre: str = None,
                          anpc: int = None,
                          local_api_url=None,
                          model_name=None,
                          feedback=None):
    url = local_api_url or LOCAL_API_URL
    model = model_name or MODEL_NAME

    previous_joined = _join_previous_chapters(previous_chapters or [])
    feedback_section = ""
    if feedback:
        feedback_section = f"\n\nAdditional reviewer feedback to address:\n\"\"\"{feedback}\"\"\"\n"

    if anpc and anpc > 0:
        base_words = anpc * 500
        word_target = int(random.uniform(base_words * 0.75, base_words * 1.25))
    else:
        word_target = random.randint(2500, 3500)

    prompt = CHAPTER_PROMPT_TEMPLATE.format(
        expanded_plot=expanded_plot,
        chapters_overview=chapters_overview,
        previous_chapters_summary=previous_joined,
        genre=genre or "unspecified",
        chapter_number=chapter_index,
        word_target=word_target,
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
