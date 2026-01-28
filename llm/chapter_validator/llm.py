# -*- coding: utf-8 -*-
# pipeline/steps/chapter_validator/llm.py
"""
LLM-only validator pentru un capitol: primește toate intrările ca argumente,
apelează modelul, și întoarce (result, details).
"""


import textwrap
from typing import List, Tuple, Optional, Dict, Any
from provider import provider_manager
from state.settings_manager import settings_manager




def _format_transition_validation(transition: Optional[Dict[str, Any]], chapter_number: int) -> str:
    """
    Generate validation rules for checking transition contract adherence.
    Returns empty string if no transition provided.
    """
    if not transition:
        return ""
    
    t_type = transition.get("transition_type", "direct")
    entry = transition.get("entry_constraints", {})
    exit_p = transition.get("exit_payload", {})
    anchor = transition.get("anchor", {})
    
    lines = ["\n**Transition Contract (verify adherence):**"]
    
    # Type line
    if chapter_number == 1:
        type_line = "    - Type: `first_chapter` — verify it establishes world/characters naturally before action"
    elif t_type == "direct":
        type_line = "    - Type: `direct` — verify it continues smoothly from previous chapter"
    elif t_type == "return":
        resume_from = anchor.get("resume_from_chapter")
        if resume_from:
            type_line = f"    - Type: `{t_type}` — verify it continues from Chapter {resume_from} (NOT previous chapter)"
        else:
            type_line = f"    - Type: `{t_type}` — verify it returns properly from flashback/parallel thread"
    elif t_type == "flashback":
        trigger = anchor.get("trigger")
        if trigger:
            type_line = f"    - Type: `{t_type}` — verify time shift is clear and triggered by: {trigger}"
        else:
            type_line = f"    - Type: `{t_type}` — verify time shift is clearly established at start"
    elif t_type in ("parallel", "pov_switch"):
        type_line = f"    - Type: `{t_type}` — verify POV/location differs appropriately from previous chapter"
    else:
        type_line = f"    - Type: `{t_type}`"
    lines.append(type_line)
    
    # Entry validation
    lines.append("    - **Entry checks:**")
    if entry.get("temporal_context"):
        lines.append(f"      * Temporal context matches: {entry['temporal_context']}")
    if entry.get("pov"):
        lines.append(f"      * POV character is: {entry['pov']}")
    if entry.get("narrative_person"):
        lines.append(f"      * Narrative person is: {entry['narrative_person']} person — verify chapter is written in this person")
    if entry.get("pickup_state"):
        lines.append(f"      * Chapter reaches the core starting situation: {entry['pickup_state']}")
        lines.append(f"        (May have brief intro before, but should reach this point)")
    do_not_explain = entry.get("do_not_explain", [])
    if do_not_explain:
        lines.append(f"      * Does NOT redundantly explain: {', '.join(do_not_explain)}")
    
    # Exit validation
    lines.append("    - **Exit checks:**")
    if exit_p.get("last_beat"):
        lines.append(f"      * Chapter reaches the core ending situation: {exit_p['last_beat']}")
        lines.append(f"        (This should be the final story beat; only atmospheric closure may follow, no new events)")
    carryover = exit_p.get("carryover_facts", [])
    if carryover:
        lines.append(f"      * Establishes these facts: {', '.join(carryover)}")
    open_threads = exit_p.get("open_threads", [])
    if open_threads:
        lines.append(f"      * Leaves these threads open (verify they are NOT explicitly stated): {', '.join(open_threads)}")
    
    # Characters validation
    characters = transition.get("characters", {})
    new_chars = characters.get("new", [])
    if new_chars:
        lines.append("    - **Character introduction checks:**")
        lines.append(f"      * NEW characters are introduced naturally (not abruptly named): {', '.join(new_chars)}")
        lines.append(f"        (Verify they have brief introduction, not just mentioned by name)")
    
    return "\n".join(lines) + "\n"


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
{transition_validation}

Your job:
1. In the "Chapters Overview", **find the description that corresponds to Chapter {chapter_number}**.
2. Evaluate if the current chapter **matches that description** in tone, events, structure, and purpose.
3. Check for **logical continuity**:
   - It must align with previous chapters (characters, motivations, timeline, world state).
   - It must **NOT include or foreshadow content from future chapters**. If it does, the chapter is NOT OK.
   - Ensure there are no unjustified time jumps or contradictions.
4. Confirm that all **key elements from the chapter's description** are present.
5. Verify that the chapter **advances the story** rather than stalling it.
6. Consider the **GENRE** when judging consistency of tone, pacing, and atmosphere.
7. **CRITICAL: Check for meta-language violations:**
   - The chapter must NOT contain phrases like "The chapter ends with...", "This chapter explores...", "The next chapter would ask..."
   - The chapter must NOT explicitly state open questions or themes — they should emerge naturally.
   - The chapter must NOT refer to "the reader", "the story", "the chapter", or narrative structure.
   - If any meta-language is found, mark as NOT OK.
{transition_checks}
{response_instruction}

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
    transition: Optional[Dict[str, Any]] = None,
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

    transition_validation = _format_transition_validation(transition, current_index)
    transition_checks = "8. **Verify Transition Contract adherence** (if provided above)." if transition else ""
    response_instruction = "9. Respond in one of the following strict formats:" if transition else "8. Respond in one of the following strict formats:"

    prompt = _VALIDATION_PROMPT.format(
        expanded_plot=expanded_plot or "",
        chapters_overview=chapters_overview or "",
        previous_chapters_summary=previous_summary,
        current_chapter=current_chapter or "",
        chapter_number=current_index,
        genre=genre or "unspecified",
        transition_validation=transition_validation,
        transition_checks=transition_checks,
        response_instruction=response_instruction,
    )

    messages = [
        {"role": "system", "content": "You are a balanced story structure and continuity validator."},
        {"role": "user", "content": prompt},
    ]

    task_params = settings_manager.get_task_params("chapter_validator")
    retries = task_params.get("retries", 3)
    if retries is None:
        retries = 3
    retries = max(0, int(retries))

    last_error = None
    last_content = None

    for attempt in range(retries + 1):
        try:
            content = provider_manager.get_llm_response(
                task_name="chapter_validator",
                messages=messages
            )
            last_content = content
        except Exception as e:
            last_error = str(e)
            if attempt < retries:
                continue
            return ("ERROR", str(last_error))

        up = content.upper()
        if "RESULT: OK" in up:
            return ("OK", content)
        if "RESULT: NOT OK" in up:
            return ("NOT OK", content)

        if attempt < retries:
            continue

    return ("UNKNOWN", last_content or "(no response)")

