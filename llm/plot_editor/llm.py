# -*- coding: utf-8 -*-
# pipeline/steps/plot_editor/llm.py
"""
LLM helper pentru editarea Expanded Plot bazat pe impact și diff.
"""


import textwrap
import json
from utils.json_utils import extract_json_from_response
from provider import provider_manager


_EDIT_PLOT_PROMPT = textwrap.dedent("""\
You are an expert story editor specializing in adapting story blueprints to maintain continuity after changes.

Context:
A user made an edit to **{edited_section}**. This edit has been analyzed, and the Expanded Plot needs to be updated to reflect the impact of that change.

ORIGINAL EXPANDED PLOT:
\"\"\"{original_plot}\"\"\"

CHANGES DETECTED IN USER'S EDIT (applied to {edited_section}):
\"\"\"{diff_summary}\"\"\"

IMPACT REASON (why Expanded Plot needs adaptation and how to accommodate the changes):
\"\"\"{impact_reason}\"\"\"

GENRE:
\"\"\"{genre}\"\"\"

IMPORTANT:
- Follow the instructions in impact_reason for how to adapt the Expanded Plot
- The adaptation must be NATURAL and seamless — write the plot as if it has always been this way after the diff
- Do NOT add special headers, prefixes, or phrases like "new plot development", "updated section", or "changes include"
- Do NOT mention chapter numbers or which chapter the changes occurred in (e.g., avoid "Chapter 4", "in Chapter 5"). Focus on the story events and developments themselves, not their chapter placement
- Simply integrate the changes naturally into the existing plot structure
- The adapted plot should read as if it was written this way from the beginning, incorporating the changes seamlessly

Examples:

Example 1: Chapter 4 (out of 7) was edited. User modified Chapter 4 so that Gary dies at the end (previously he survived). Expanded Plot needs to be adapted.
- BREAKING CHANGE: Yes (Gary's death contradicts the survival mentioned in Expanded Plot)
- Expanded Plot adaptation: Use CREATIVITY to accommodate this change. Update the plot to reflect Gary's death. Remove references to Gary surviving. Adapt the story arc creatively to account for Gary's absence in subsequent events — find creative ways to continue the story without him. Try to preserve what can be preserved from the original plot, but major creative modifications are accepted. Write it naturally as if Gary's death was always part of the plot. Do NOT add phrases like "Gary now dies" or "Updated: Gary dies" — simply write the plot with Gary's death integrated naturally.

Example 2: Chapter 4 (out of 5) was edited. User modified Chapter 4 so that John decides to embark on an adventure to Mount Everest the next day (previously Chapter 4 ended with John at home). This major plot development is not mentioned in Expanded Plot.
- BREAKING CHANGE: Yes (major new plot development needs to be integrated)
- Expanded Plot adaptation: Use CREATIVITY to accommodate this change. Integrate John's Everest adventure into the plot summary creatively. Update the relevant sections to include this development naturally, finding creative ways to weave it into the existing story structure. Try to preserve what can be preserved, but major creative modifications are accepted. Write it as if John's Everest adventure was always part of the story arc. Do NOT add markers like "New development:" or "Added:" — simply weave it into the existing plot structure seamlessly.

Example 3: Chapters Overview was edited. Original Chapter 6 description was "The journey continues peacefully." Modified description is "The journey builds toward a violent confrontation with enemies." Expanded Plot needs to be adapted to reflect this change.
- BREAKING CHANGE: Yes (fundamental change to story direction)
- Expanded Plot adaptation: Use CREATIVITY to accommodate this change. Update the plot summary to reflect the violent confrontation ending. Adapt the climax and resolution sections creatively to include the confrontation, finding ways to build tension and conflict naturally. Try to preserve what can be preserved from the original peaceful journey elements, but major creative modifications are accepted. Write it naturally as if the violent confrontation was always the intended ending. Integrate tension and conflict buildup throughout the plot naturally.

Example 4: Chapter 2 (out of 5) was edited. User changed the location where the main event takes place from "Springfield" to "Riverside". Expanded Plot mentions "Springfield" as the location.
- BREAKING CHANGE: No (simple location name replacement)
- Expanded Plot adaptation: Make MINIMAL modification - replace "Springfield" with "Riverside" wherever the location is mentioned in the plot. Preserve all other content unchanged. Write it naturally as if the events always took place in Riverside.

Example 5: Chapters Overview was edited. Character name "Robert" was changed to "Michael" in Chapter 2 and Chapter 4 descriptions. Expanded Plot mentions Robert throughout.
- BREAKING CHANGE: No (simple name replacement)
- Expanded Plot adaptation: Make MINIMAL modification - replace all instances of "Robert" with "Michael" throughout the plot. Preserve all other content unchanged. Write it naturally as if the character was always named Michael.

Task:
1. First, analyze the impact and changes to determine if this is a BREAKING CHANGE:
   - A BREAKING CHANGE means the modifications require significant restructuring, contradict established facts, or fundamentally alter the story's direction. Use CREATIVITY to accommodate the changes as best as possible. Try to preserve what can be preserved, but major creative modifications are accepted and encouraged when necessary to address the breaking change.
   - A NON-BREAKING CHANGE means the changes can be accommodated with minimal modifications. Make MINIMAL modifications — only what is strictly necessary. Preserve the vast majority of the original text unchanged.

2. Then, adapt the Expanded Plot accordingly:
   - Follow the instructions in impact_reason
   - If BREAKING CHANGE: Use CREATIVITY to accommodate the changes as best as possible. Try to preserve as much of the original story as possible, but major creative modifications are accepted and encouraged when necessary. Write the adapted plot naturally, as if it has always been this way. Be creative in finding solutions that maintain coherence while accommodating the breaking change.
   - If NON-BREAKING CHANGE: Make MINIMAL modifications — only what is strictly necessary. Preserve the vast majority of the original text unchanged. Integrate changes seamlessly.

Output Requirements:
- Maintain the same Markdown structure as the original (Title, Key Characters, World/Setting Overview, Plot Summary)
- Preserve all sections that are not affected by the changes
- Update only the parts that need to change based on the impact and impact_reason instructions
- Keep the same tone, style, and level of detail as the original
- Ensure the adapted plot remains coherent and logically consistent
- Write naturally — the plot should read as if it was always written this way, with changes seamlessly integrated

You must output a JSON object with the following structure:
{{
  "is_breaking_change": true/false,
  "adapted_plot": "the complete adapted Expanded Plot in Markdown format"
}}

Output ONLY the JSON object, no other text or explanations.
""").strip()


def call_llm_edit_plot(
    original_plot: str,
    impact_reason: str,
    diff_summary: str,
    edited_section: str = "",
    genre: str = "",
    *,
    api_url: str = None,
    model_name: str = None,
    timeout: int = 300,
) -> str:
    """
    Editează Expanded Plot bazat pe impact și diff.
    AI-ul determină dacă e breaking change și adaptează în consecință.
    
    Args:
        original_plot: Expanded Plot existent
        impact_reason: Motivul pentru care trebuie adaptat
        diff_summary: Rezumatul modificărilor detectate
        genre: Genul poveștii
    """



    prompt = _EDIT_PLOT_PROMPT.format(
        original_plot=original_plot or "",
        diff_summary=diff_summary or "",
        impact_reason=impact_reason or "",
        edited_section=edited_section or "a section",
        genre=genre or "unspecified",
    )

    messages = [
        {"role": "system", "content": "You are a precise story continuity editor that adapts story blueprints while preserving as much original content as possible. You must output only valid JSON."},
        {"role": "user", "content": prompt},
    ]

    try:
        content = provider_manager.get_llm_response(
            task_name="plot_editor",
            messages=messages,
            timeout=timeout,
            temperature=0.7,
            top_p=0.95,
            max_tokens=8192
        )
        
        # Parse JSON response (suportă atât JSON pur cât și wrappat în tag-uri)
        try:
            result = extract_json_from_response(content)
            return result.get("adapted_plot", content)
        except (json.JSONDecodeError, ValueError):
            # Fallback dacă nu e JSON valid
            return content
    except Exception as e:
        return f"Error during plot editing: {e}"


