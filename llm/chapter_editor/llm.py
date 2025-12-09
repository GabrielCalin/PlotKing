# -*- coding: utf-8 -*-
# pipeline/steps/chapter_editor/llm.py
"""
LLM helper pentru editarea unui capitol bazat pe impact și diff.
"""


import textwrap
import json
from typing import List, Optional
from provider import provider_manager
from utils.json_utils import extract_json_from_response

_EDIT_CHAPTER_PROMPT = textwrap.dedent("""\
You are an expert fiction editor specializing in adapting chapters to maintain continuity after story changes.

Context:
A user made an edit to **{edited_section}**. This edit has been analyzed, and an impact was determined on Chapter {chapter_number}. The following sections have ALREADY been adapted to accommodate the changes:
- **Expanded Plot** (already modified according to the diff)
- **Chapters Overview** (already updated to reflect the changes)
- **Previously Written Chapters** (already adapted if needed)

Now, Chapter {chapter_number} needs to be adapted to:
- Continue naturally from the previous chapter (which has already been adapted)
- Respect the **Chapters Overview** (which has already been updated, including the description for Chapter {chapter_number})
- Align with the **Expanded Plot** (which has already been modified)
- Accommodate the CONSEQUENCES of the diff (the diff itself was already applied to the previous section; you need to adapt Chapter {chapter_number} to reflect the consequences of that change)
- Follow the **impact reason** instructions for how to accommodate those consequences

Inputs:
- **Global Story Summary (authoritative plot - already modified according to the diff):**
\"\"\"{expanded_plot}\"\"\"
- **Chapters Overview (titles + short descriptions of all chapters - already updated to reflect changes):**
\"\"\"{chapters_overview}\"\"\"
- **Previously Written Chapters (before this one - already adapted if needed):**
\"\"\"{previous_chapters_summary}\"\"\"
- **Current Chapter {chapter_number} (to be edited):**
\"\"\"{original_chapter}\"\"\"
- **CHANGES DETECTED IN USER'S EDIT (applied to {edited_section}, not Chapter {chapter_number}):**
\"\"\"{diff_summary}\"\"\"
- **IMPACT REASON (why Chapter {chapter_number} needs adaptation and how to accommodate the consequences):**
\"\"\"{impact_reason}\"\"\"
- **GENRE** (to guide tone, pacing, and atmosphere):
\"\"\"{genre}\"\"\"

IMPORTANT: 
- The diff refers to a PREVIOUS section that was already modified (not Chapter {chapter_number}). The diff itself has already been applied to that previous section.
- The Expanded Plot, Chapters Overview, and Previously Written Chapters provided above are ALREADY modified according to the diff. Do NOT compare against "original" versions that don't exist here.
- Your task is to adapt Chapter {chapter_number} to accommodate the CONSEQUENCES of that diff, following the impact_reason instructions, while maintaining coherence with the already-adapted sections (Expanded Plot, Chapters Overview, and previous chapters).

Examples:

Example 1: Chapter 4 (out of 7) was edited. User modified Chapter 4 so that Gary dies at the end (previously he survived). Now Chapter 5 needs to be adapted.
- BREAKING CHANGE: Yes (Gary's death requires major restructuring of Chapter 5)
- Chapter 5 adaptation: Follow the new Chapter 5 description from Chapters Overview (which has already been updated to reflect Gary's death). The chapter must account for Gary's absence. Characters react to his death, the story continues without him. Remove any references to Gary being alive. Adapt scenes that depended on Gary's presence. Preserve as much of the original Chapter 5 content as possible, but restructure to reflect the new reality and align with the updated Chapters Overview description.

Example 2: Chapter 3 (out of 5) was edited. User changed Susan's eye color from brown to green in Chapter 3. Chapter 5 also mentions Susan's eye color.
- BREAKING CHANGE: No (minor detail change)
- Chapter 5 adaptation: Make MINIMAL modification - only change the eye color reference from "brown" to "green" wherever it appears. Preserve all other content unchanged. This is a simple find-and-replace type change.

Example 3: Chapter 4 (out of 5) was edited. User modified Chapter 4 so that John decides to embark on an adventure to Mount Everest the next day (previously Chapter 4 ended with John at home). Now Chapter 5 needs to be adapted.
- BREAKING CHANGE: Yes (major plot development requires significant adaptation)
- Chapter 5 adaptation: Follow the new Chapter 5 description from Chapters Overview (which has already been updated to reflect John's Everest adventure). Chapter 5 must reflect that John is embarking on his Everest adventure, not continuing from the home scene. Adapt the opening to show John preparing for or beginning his journey to Everest. Restructure scenes to account for the new setting and circumstances. Preserve character development and themes from the original Chapter 5, but adapt the plot to continue naturally from John's decision to embark on the Everest adventure and align with the updated Chapters Overview description.

Example 4: Expanded Plot was edited. Character name "Robert" was changed to "Michael" throughout. Chapter 3 contains references to Robert.
- BREAKING CHANGE: No (simple name replacement)
- Chapter 3 adaptation: Make MINIMAL modifications - replace all instances of "Robert" with "Michael". Preserve all other content unchanged. This is a straightforward name replacement.

Example 5: Chapters Overview was edited. Original Chapter 6 description was "The journey continues peacefully." Modified description is "The journey builds toward a violent confrontation with enemies." Chapter 6 (out of 7) needs to be adapted to reflect this change.
- BREAKING CHANGE: Yes (fundamental change to story direction requires major adaptation)
- Chapter 6 adaptation: Adapt Chapter 6 to build toward the violent confrontation ending. Introduce tension, conflict, and foreshadowing of the confrontation. Adapt scenes to align with the new story direction while preserving the chapter's role in the story arc. Maintain coherence with the modified Chapters Overview description for Chapter 6.

Task:
1. First, analyze the impact and changes to determine if this is a BREAKING CHANGE:
   - A BREAKING CHANGE means the modifications require significant restructuring, contradict established facts, or fundamentally alter the story's direction. Major modifications are allowed, but preserve as much of the original chapter content as possible. Only change what is necessary to address the breaking change while maintaining coherence with the Expanded Plot, Chapters Overview, and previous chapters.
   - A NON-BREAKING CHANGE means the changes can be accommodated with minimal modifications. Make MINIMAL modifications — only what is strictly necessary. Preserve the vast majority of the original chapter text unchanged.

2. Then, adapt Chapter {chapter_number} accordingly:
   - If BREAKING CHANGE: Significant modifications are allowed, but preserve as much of the original chapter content as possible. The priority is coherence with Expanded Plot, Chapters Overview, and previous chapters. Only change what is necessary to address the breaking change.
   - If NON-BREAKING CHANGE: Make MINIMAL modifications — only what is strictly necessary to accommodate the difference and impact. Preserve the vast majority of the original chapter text unchanged.

Specific Instructions:
1. Locate in the Chapters Overview the exact description that corresponds to **Chapter {chapter_number}**.
   - Use its **title exactly as written** at the start of the chapter, formatted as a **Markdown H2 heading** (`##`).
   - Do **not** invent or alter the title in any way.
2. Review the original chapter text and identify what needs to change based on the impact reason. The diff shows what was changed in a previous section; you need to adapt Chapter {chapter_number} to accommodate the consequences of that change, not apply the diff itself.
3. Maintain **logical continuity**:
   - Ensure smooth continuation from the **previous chapter** (which has already been adapted)
   - Keep consistency with the **Chapters Overview** (which has already been updated, including the description for Chapter {chapter_number})
   - Align with the **Expanded Plot** (which has already been modified)
   - Accommodate the **consequences** of the diff (as explained in impact_reason) while maintaining coherence with the Chapters Overview description for Chapter {chapter_number}
   - Do **not** include or foreshadow events that explicitly belong to future chapters
4. Preserve the chapter's role, purpose, and position in the story arc as defined in the Chapters Overview.
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
    edited_section: str = "",
    genre: str = "",
    anpc: Optional[int] = None,
    *,
    # Deprecated args kept for signature compatibility but ignored (or mapped if useful)
    api_url: Optional[str] = None,
    model_name: Optional[str] = None,
    timeout: int = 3600,
) -> str:
    """
    Editează un capitol bazat pe impact și diff.
    AI-ul determină dacă e breaking change și adaptează în consecință.
    """
    prev_joined = _join_previous_chapters(previous_chapters or [])

    prompt_text = _EDIT_CHAPTER_PROMPT.format(
        expanded_plot=expanded_plot or "",
        chapters_overview=chapters_overview or "",
        previous_chapters_summary=prev_joined,
        original_chapter=original_chapter or "",
        diff_summary=diff_summary or "",
        impact_reason=impact_reason or "",
        edited_section=edited_section or "a previous section",
        genre=genre or "unspecified",
        chapter_number=chapter_index,
    )
    
    messages = [
        {"role": "system", "content": "You are a precise fiction editor that adapts chapters while preserving as much original content as possible. You must output only valid JSON."},
        {"role": "user", "content": prompt_text},
    ]

    try:
        content = provider_manager.get_llm_response(
            task_name="chapter_editor",
            messages=messages,
            timeout=timeout,
            temperature=0.8,
            top_p=0.95,
            max_tokens=8000
        )
        
        # Parse JSON response (suportă atât JSON pur cât și wrappat în tag-uri)
        try:
            result = extract_json_from_response(content)
            return result.get("adapted_chapter", content)
        except (json.JSONDecodeError, ValueError):
            # Fallback dacă nu e JSON valid
            return content
    except Exception as e:
        return f"Error during chapter editing: {e}"


