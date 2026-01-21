# -*- coding: utf-8 -*-
# pipeline/steps/chapter_writer/llm.py
"""
LLM-only helpers pentru scrierea/revizuirea unui capitol.
Nu au dependențe de runner sau context; primesc totul ca argumente.
"""


import textwrap
import random
from typing import List, Optional
from provider import provider_manager


_CHAPTER_PROMPT = textwrap.dedent("""\
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
   - To reach this length, expand creatively within the scope of this chapter’s description. Add realistic detail, dialogue, atmosphere, and depth that make sense for the story and characters.  
   - **Do not include or borrow content from later chapters** to increase word count. All expansion must remain consistent with this chapter’s overview and the global plot.
10. Output **only** the final story text — no explanations, meta commentary, or outline notes.

Begin writing **Chapter {chapter_number}** now.
""").strip()

_REVISION_PROMPT = textwrap.dedent("""\
You are an expert **fiction editor and ghostwriter** specializing in long-form narrative revision.

Task:
You previously wrote **Chapter {chapter_number}** of the story.  
You must now **revise and improve** it according to reviewer feedback — maintaining the chapter’s title and role in the story,
but you may adjust its internal flow, tone, and events as needed to satisfy the feedback.

---

### Reference Materials

- **Global Story Summary (authoritative plot):**
\"\"\"{expanded_plot}\"\"\"

- **Chapters Overview (titles + short descriptions of all chapters):**
\"\"\"{chapters_overview}\"\"\"

- **Previously Written Chapters (before this one):**
\"\"\"{previous_chapters_summary}\"\"\"

- **Current Draft of Chapter {chapter_number}:**
\"\"\"{previous_output}\"\"\"

- **Reviewer Feedback:**
\"\"\"{feedback}\"\"\"

- **GENRE (to guide tone, pacing, and atmosphere):**
\"\"\"{genre}\"\"\"

---

### Revision Instructions

1. **Locate** in the Chapters Overview the description corresponding to **Chapter {chapter_number}**, and study it carefully.  
   - You must preserve the **chapter title exactly as written** (Markdown H2 format, `## <Title>`).  
   - The events and tone of this chapter must remain consistent with its overview description and position in the overall story arc.

2. **Revise the existing draft**, focusing on the feedback provided.  
   - You may **modify or expand events, dialogue, or pacing** as long as they align with the chapter’s purpose in the overview.  
   - Ensure all story logic, character motivations, and world details remain consistent with previous chapters.  
   - Do **not** move, merge, or remove this chapter; its place in the story and title must remain fixed.

3. Maintain full **continuity**:
   - Respect everything that has already happened in previous chapters.  
   - Do not include or foreshadow content that explicitly belongs to future chapters.  
   - Do not contradict the global summary or previously established facts.

4. Keep prose **immersive, cohesive, and natural**, as if this were the final, polished version.  
   - Smooth transitions, expressive narration, realistic dialogue, and sensory details are encouraged.  
   - You may restructure paragraphs or add short connective sentences if it helps the flow.

5. **Length & format**:
   - The revised chapter should be approximately the same length as before (±10% of {word_target} words).  
   - Do **not** produce a summary or outline — write the full narrative text.  
   - Output only the story content in Markdown format (no notes or explanations).

---

Begin revising **Chapter {chapter_number}** now.
""").strip()


def _join_previous_chapters(previous_texts: Optional[List[str]]) -> str:
    if not previous_texts:
        return "None"
    parts = []
    for idx, txt in enumerate(previous_texts):
        parts.append(f"Chapter {idx+1}:\n{(txt or '').strip()}\n")
    return "\n\n".join(parts)


def _compute_word_target(anpc: Optional[int]) -> int:
    if anpc and anpc > 0:
        base_words = anpc * 500
        return int(random.uniform(base_words * 0.75, base_words * 1.25))
    return random.randint(2500, 3500)



def call_llm_generate_chapter(
    expanded_plot: str,
    chapters_overview: str,
    chapter_index: int,
    previous_chapters: Optional[List[str]] = None,
    *,
    genre: Optional[str] = None,
    anpc: Optional[int] = None,
    api_url: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout: int = 3600,
) -> str:
    """
    Generează textul pentru un singur capitol (fără feedback).
    Returnează conținutul Markdown sau mesaj de eroare.
    """
    word_target = _compute_word_target(anpc)
    prev_joined = _join_previous_chapters(previous_chapters or [])

    prompt = _CHAPTER_PROMPT.format(
        expanded_plot=expanded_plot or "",
        chapters_overview=chapters_overview or "",
        previous_chapters_summary=prev_joined,
        genre=genre or "unspecified",
        chapter_number=chapter_index,
        word_target=word_target,
    )

    messages = [
        {"role": "system", "content": "You are a professional fiction ghostwriter ensuring perfect narrative coherence."},
        {"role": "user", "content": prompt},
    ]

    try:
        content = provider_manager.get_llm_response(
            task_name="chapter_writer",
            messages=messages
        )
        if not content:
            return "Error: model returned empty content"
        return content.strip()
    except Exception as e:
        return f"Error during chapter generation: {e}"


def call_llm_revise_chapter(
    expanded_plot: str,
    chapters_overview: str,
    chapter_index: int,
    previous_chapters: Optional[List[str]],
    previous_output: str,
    feedback: str,
    *,
    genre: Optional[str] = None,
    anpc: Optional[int] = None,
    api_url: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout: int = 3600,
) -> str:
    """
    Revizuiește un capitol existent pe baza feedback-ului.
    Returnează conținutul Markdown sau mesaj de eroare.
    """
    word_target = _compute_word_target(anpc)
    prev_joined = _join_previous_chapters(previous_chapters or [])

    prompt = _REVISION_PROMPT.format(
        expanded_plot=expanded_plot or "",
        chapters_overview=chapters_overview or "",
        previous_chapters_summary=prev_joined,
        previous_output=previous_output or "",
        feedback=feedback or "",
        genre=genre or "unspecified",
        chapter_number=chapter_index,
        word_target=word_target,
    )

    messages = [
        {"role": "system", "content": "You are a professional fiction ghostwriter ensuring perfect narrative coherence."},
        {"role": "user", "content": prompt},
    ]

    try:
        content = provider_manager.get_llm_response(
            task_name="chapter_writer",
            messages=messages
        )
        if not content:
            return "Error: model returned empty content"
        return content.strip()
    except Exception as e:
        return f"Error during chapter revision: {e}"

