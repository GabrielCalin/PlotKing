# -*- coding: utf-8 -*-
# pipeline/steps/chapter_writer/llm.py
"""
LLM-only helpers pentru scrierea/revizuirea unui capitol.
Nu au dependențe de runner sau context; primesc totul ca argumente.
"""


import textwrap
import random
from typing import List, Optional, Dict, Any
from provider import provider_manager


def _format_transition_block(transition: Optional[Dict[str, Any]], chapter_number: int) -> str:
    """
    Format transition contract for inclusion in prompt.
    Returns empty string if no transition provided.
    """
    if not transition:
        return ""
    
    t_type = transition.get("transition_type", "direct")
    entry = transition.get("entry_constraints", {})
    exit_p = transition.get("exit_payload", {})
    anchor = transition.get("anchor", {})
    
    lines = [f"\n- **Transition Contract for Chapter {chapter_number}:**"]
    lines.append(f"  - Type: `{t_type}`")
    
    if t_type == "return":
        resume_from = anchor.get("resume_from_chapter")
        if resume_from:
            lines.append(f"  - Continues from: Chapter {resume_from} (NOT from chapter {chapter_number - 1})")
    elif t_type == "flashback":
        trigger = anchor.get("trigger")
        if trigger:
            lines.append(f"  - Triggered by: {trigger}")
    elif t_type in ("parallel", "pov_switch"):
        lines.append(f"  - This is a {t_type.replace('_', ' ')} — may have different POV/location than previous chapter")
    
    if entry.get("temporal_context"):
        lines.append(f"  - When: {entry['temporal_context']}")
    if entry.get("pov"):
        lines.append(f"  - POV: {entry['pov']}")
    if entry.get("pickup_state"):
        lines.append(f"  - Start with: {entry['pickup_state']}")
    
    do_not_explain = entry.get("do_not_explain", [])
    if do_not_explain:
        lines.append(f"  - DO NOT re-explain: {', '.join(do_not_explain)}")
    
    if exit_p.get("last_beat"):
        lines.append(f"  - End with: {exit_p['last_beat']}")
    
    return "\n".join(lines)


def _format_transition_rules(transition: Optional[Dict[str, Any]]) -> str:
    """
    Generate additional rules for following the transition contract.
    Returns empty string if no transition provided.
    """
    if not transition:
        return ""
    
    t_type = transition.get("transition_type", "direct")
    entry = transition.get("entry_constraints", {})
    exit_p = transition.get("exit_payload", {})
    
    rules = ["\n11. **Follow the Transition Contract strictly:**"]
    
    if entry.get("pickup_state"):
        rules.append(f"    - Your opening scene must connect to: \"{entry['pickup_state']}\"")
    
    do_not_explain = entry.get("do_not_explain", [])
    if do_not_explain:
        rules.append(f"    - Do NOT re-explain or restate: {', '.join(do_not_explain)}")
    
    if exit_p.get("last_beat"):
        rules.append(f"    - Your closing scene must deliver: \"{exit_p['last_beat']}\"")
    
    if t_type == "return":
        rules.append("    - This chapter returns from a flashback/parallel thread — resume the main story naturally")
    elif t_type == "flashback":
        rules.append("    - This is a flashback — establish the time shift clearly at the start")
    
    return "\n".join(rules) + "\n"


_CHAPTER_PROMPT = textwrap.dedent("""\
You are an expert **long-form fiction writer**.

Task:
Write **only** Chapter {chapter_number} of the story, using the following materials and strict continuity rules.

Inputs:
- **Global Story Summary (authoritative plot):**
\"\"\"{expanded_plot}\"\"\"
{chapter_context_block}
- **Previously Written Chapters (if any, may be empty):**
\"\"\"{previous_chapters_summary}\"\"\"
- **GENRE** (to guide tone, pacing, and atmosphere):
\"\"\"{genre}\"\"\"{transition_block}

---

### Your job
1. Before writing, mentally review the Global Story Summary to fully understand the story's logic and timeline.
{chapter_identification_instruction}
3. Write the **complete narrative text** for that chapter, following its description precisely in tone, purpose, and key events.  
   - Maintain smooth internal flow between moments without subdividing the text into numbered or titled scenes.
4. Ensure **logical continuity**.  
   - Maintain consistency with **previous chapters** (characters, setting, timeline, motivations, tone).  
   - Anticipate what will happen in the **next chapter**, ensuring seamless transition.  
   - Do **not** include or foreshadow events that explicitly belong to future chapters.  
   - Do not include flashbacks, summaries of previous events, or visions of future ones unless explicitly stated in this chapter's description.
5. Preserve internal continuity of all details (locations, time of day, physical states, objects, tone) introduced so far.  
   - Balance action, dialogue, and narration so that external events drive the story forward.
6. Maintain a clear, engaging, and immersive prose style appropriate for long-form fiction.  
   - Natural dialogue, expressive narration, and sensory details are encouraged.  
   - You may use **Markdown elements** (e.g., `---` for scene breaks, *italics*, or **bold**) if they enhance structure or readability, but do not label or number scenes.
7. Adapt writing style, pacing, and atmosphere to match the **GENRE** conventions (e.g., suspense rhythm for thrillers, sensory prose for romance, measured clarity for sci-fi).
8. End the chapter appropriately for its position in the book.  
   - If it is **not the final chapter**, close with a natural sense of transition or anticipation — a pause that leads smoothly into the next chapter.  
   - If it **is the final chapter**, conclude the story in a way that aligns with the chapter description and **Global Story Summary**, providing resolution without adding new material beyond the planned ending.  
   - Do **not** comment on the chapter itself or describe that it "ends"; simply write the story up to its natural stopping point.
9. Target length: around **{word_target} words**.  
   - To reach this length, expand creatively within the scope of this chapter's description. Add realistic detail, dialogue, atmosphere, and depth that make sense for the story and characters.  
   - **Do not include or borrow content from later chapters** to increase word count. All expansion must remain consistent with this chapter's description and the global plot.
10. Output **only** the final story text — no explanations, meta commentary, or outline notes.
{transition_rules}
Begin writing **Chapter {chapter_number}** now.
""").strip()

_REVISION_PROMPT = textwrap.dedent("""\
You are an expert **fiction editor and ghostwriter** specializing in long-form narrative revision.

Task:
You previously wrote **Chapter {chapter_number}** of the story.  
You must now **revise and improve** it according to reviewer feedback — maintaining the chapter's title and role in the story,
but you may adjust its internal flow, tone, and events as needed to satisfy the feedback.

---

### Reference Materials

- **Global Story Summary (authoritative plot):**
\"\"\"{expanded_plot}\"\"\"
{chapter_context_block}
- **Previously Written Chapters (before this one):**
\"\"\"{previous_chapters_summary}\"\"\"

- **Current Draft of Chapter {chapter_number}:**
\"\"\"{previous_output}\"\"\"

- **Reviewer Feedback:**
\"\"\"{feedback}\"\"\"

- **GENRE (to guide tone, pacing, and atmosphere):**
\"\"\"{genre}\"\"\"{transition_block}

---

### Revision Instructions

{revision_identification_instruction}

2. **Revise the existing draft**, focusing on the feedback provided.  
   - You may **modify or expand events, dialogue, or pacing** as long as they align with the chapter's purpose.  
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
{transition_rules}
---

Begin revising **Chapter {chapter_number}** now.
""").strip()


def _build_chapter_context_block(
    chapter_description: Optional[str],
    chapters_overview: str,
    chapter_number: int
) -> tuple:
    """
    Build the context block and identification instruction for the prompts.
    
    Returns:
        Tuple of (chapter_context_block, chapter_identification_instruction, revision_identification_instruction)
    """
    if chapter_description:
        context_block = f"""- **Chapter {chapter_number} Description (what this chapter should contain):**
\"\"\"{chapter_description}\"\"\""""
        
        chapter_id_instruction = f"""2. Use the **Chapter {chapter_number} Description** provided above as your guide.  
   - Use its **title exactly as written** at the start of the chapter, formatted as a **Markdown H2 heading** (`##`).  
   - Do **not** invent or alter the title in any way."""
        
        revision_id_instruction = f"""1. Study the **Chapter {chapter_number} Description** provided above carefully.  
   - You must preserve the **chapter title exactly as written** (Markdown H2 format, `## <Title>`).  
   - The events and tone of this chapter must remain consistent with its description and position in the overall story arc."""
    else:
        context_block = f"""- **Chapters Overview (titles + short descriptions of all chapters):**
\"\"\"{chapters_overview}\"\"\""""
        
        chapter_id_instruction = f"""2. Locate in the Chapters Overview the exact description that corresponds to **Chapter {chapter_number}**.  
   - Use its **title exactly as written** at the start of the chapter, formatted as a **Markdown H2 heading** (`##`).  
   - Do **not** invent or alter the title in any way."""
        
        revision_id_instruction = f"""1. **Locate** in the Chapters Overview the description corresponding to **Chapter {chapter_number}**, and study it carefully.  
   - You must preserve the **chapter title exactly as written** (Markdown H2 format, `## <Title>`).  
   - The events and tone of this chapter must remain consistent with its overview description and position in the overall story arc."""
    
    return context_block, chapter_id_instruction, revision_id_instruction


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
    chapter_description: Optional[str] = None,
    transition: Optional[Dict[str, Any]] = None,
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
    
    Args:
        chapter_description: If provided, uses this specific chapter description instead of
                           requiring the LLM to locate it in chapters_overview.
        transition: If provided, includes transition contract for continuity guidance.
    """
    word_target = _compute_word_target(anpc)
    prev_joined = _join_previous_chapters(previous_chapters or [])
    
    context_block, chapter_id_instruction, _ = _build_chapter_context_block(
        chapter_description, chapters_overview or "", chapter_index
    )
    
    transition_block = _format_transition_block(transition, chapter_index)
    transition_rules = _format_transition_rules(transition)

    prompt = _CHAPTER_PROMPT.format(
        expanded_plot=expanded_plot or "",
        chapter_context_block=context_block,
        previous_chapters_summary=prev_joined,
        genre=genre or "unspecified",
        chapter_number=chapter_index,
        chapter_identification_instruction=chapter_id_instruction,
        word_target=word_target,
        transition_block=transition_block,
        transition_rules=transition_rules,
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
    chapter_description: Optional[str] = None,
    transition: Optional[Dict[str, Any]] = None,
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
    
    Args:
        chapter_description: If provided, uses this specific chapter description instead of
                           requiring the LLM to locate it in chapters_overview.
        transition: If provided, includes transition contract for continuity guidance.
    """
    word_target = _compute_word_target(anpc)
    prev_joined = _join_previous_chapters(previous_chapters or [])
    
    context_block, _, revision_id_instruction = _build_chapter_context_block(
        chapter_description, chapters_overview or "", chapter_index
    )
    
    transition_block = _format_transition_block(transition, chapter_index)
    transition_rules = _format_transition_rules(transition)

    prompt = _REVISION_PROMPT.format(
        expanded_plot=expanded_plot or "",
        chapter_context_block=context_block,
        previous_chapters_summary=prev_joined,
        previous_output=previous_output or "",
        feedback=feedback or "",
        genre=genre or "unspecified",
        chapter_number=chapter_index,
        revision_identification_instruction=revision_id_instruction,
        word_target=word_target,
        transition_block=transition_block,
        transition_rules=transition_rules,
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
