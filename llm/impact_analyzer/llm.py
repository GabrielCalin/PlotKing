# -*- coding: utf-8 -*-
# pipeline/steps/impact_analyzer/llm.py
"""
LLM helper pentru analiza impactului unui diff asupra altor secțiuni.
"""


import json
import textwrap
from typing import List, Tuple, Dict, Any
from provider import provider_manager


_IMPACT_PROMPT = textwrap.dedent("""\
You are a continuity analyst that identifies which story sections need updates after a change and provides detailed instructions for other AI editors (plot editor, overview editor, chapter editor) on how to adapt those sections.

Inputs you receive:
- SECTION EDITED: {section_name}
- IS INFILL: {is_infill}
- EDITED SECTION CONTENT (after modification):
\"\"\"{edited_section_content}\"\"\"
- SUMMARY OF CHANGES:
\"\"\"{diff_summary}\"\"\"
- POTENTIAL IMPACTED SECTIONS ({candidate_count}):
{candidate_sections}
- POTENTIALLY IMPACTED SECTION NAMES (use only these exact names in references): {candidate_names}

Impact Expectations:

**Expanded Plot changes**: Impact occurs if the change contradicts existing content or breaks continuity with other sections. All sections may be affected. **IMPORTANT**: When providing instructions for Expanded Plot adaptation, do NOT mention specific chapter numbers (e.g., "Chapter 4", "Chapter 5"). Instead, refer to events or developments in a chapter-agnostic way (e.g., "the event where Gary dies", "John's Everest adventure"). This keeps the Expanded Plot focused on the story arc rather than chapter structure.

**Chapters Overview changes**: Impact occurs if the change contradicts existing content or breaks continuity. If continuity is broken, all following chapters need adaptation and should be marked as impacted. When marking Chapters Overview as impacted, you must clearly specify which chapters from Chapters Overview need adaptation in the reason.
{infill_rule}

**Chapter changes**: Impact occurs if the change:
1. Contradicts something (even minor details not mentioned in Expanded Plot or Chapters Overview)
2. Breaks continuity with following sections
3. Introduces a major new event or plot development that affects the story's direction
{infill_chapter_rule}

For major new events: You must check continuity between the EDITED SECTION CONTENT and the following sections in POTENTIAL IMPACTED SECTIONS. If a major new event is introduced (e.g., character makes a significant decision, new plot development, location change), it requires updates in:
- Expanded Plot (to include the new event)
- Chapters Overview (to reflect the new development)
- Following chapters (to maintain continuity with the new event)

Examples:

Example 1: Expanded Plot states character Gary survives, and Chapters Overview indicates this happens in Chapter 4 (out of 7 chapters). Modification: Gary dies in Chapter 4.
- Expanded Plot: IMPACTED (Gary dies, contradicting the survival mentioned in the Plot Summary section. Update the Developments phase to reflect Gary's death instead of survival. Adapt the Climax and Resolution sections to account for Gary's absence. Check and update the Key Characters section if it mentions Gary's role in later events.)
- Chapters Overview: IMPACTED (continuity broken, Chapters 5-7 need adaptation. Update Chapter 4 description to reflect Gary's death. Adapt Chapters 5, 6, and 7 descriptions to show characters reacting to his death and continuing the story without him.)
- Chapters 5, 6, 7: IMPACTED (continuity broken - Gary's death means these chapters cannot reference Gary being alive. Adapt Chapter 5 opening to show characters reacting to Gary's death. Remove scenes or references that depended on Gary's presence in Chapters 6 and 7, while maintaining each chapter's core purpose.)

Example 2: Character name changed in Expanded Plot from "Robert" to "Michael". That character appears in Chapter 3 description (out of 5 chapters).
- Chapters Overview: IMPACTED (needs name update in Chapter 3 description. Replace "Robert" with "Michael" in the Chapter 3 description to match the Expanded Plot.)
- Chapter 3: IMPACTED (name appears, needs update. Replace all instances of "Robert" with "Michael" throughout the chapter text, preserving all other content unchanged.)
- Chapter 4: IMPACTED (name appears but not mentioned in Chapters Overview, still needs update. Replace all instances of "Robert" with "Michael" in the chapter text for consistency.)

Example 3: Minor change in Chapter 3 (out of 5): Susan's eyes are green instead of brown. Eye color is also mentioned in Chapter 5.
- Chapter 5: IMPACTED (eye color detail needs update for consistency. Replace "brown" with "green" wherever Susan's eye color is mentioned in Chapter 5, preserving all other content unchanged.)

Example 4: Chapter 4 (out of 5) is modified. Previously, Chapter 4 ended with John at home. New modification: John decides to embark on an adventure to Mount Everest the next day. This is a major new plot development not mentioned in Expanded Plot or Chapters Overview.
- Expanded Plot: IMPACTED (major new event - John's Everest adventure - needs to be included. Integrate John's Everest adventure into the Plot Summary section, specifically in the Developments phase where John's journey is described. Update the section that currently describes John's story ending at home to include his decision to go to Everest and the subsequent adventure, integrating it naturally into the existing narrative flow. Do not mention which chapter this occurs in.)
- Chapters Overview: IMPACTED (needs to reflect John's departure and adventure in Chapter 4 description, Chapter 5 needs adaptation. Update Chapter 4 description to mention John's decision to embark on the Everest adventure. Adapt Chapter 5 description to show John is on Everest rather than continuing from the home scene.)
- Chapter 5: IMPACTED (must account for John being on Everest adventure, continuity broken with previous ending. Adapt the chapter to reflect that John is on his Everest adventure, not continuing from being at home. Update the opening and subsequent scenes to show John preparing for or beginning his journey to Everest, maintaining continuity with the modified Chapter 4.)

{infill_example}

Task:
1. Review the edited section content, change summary, and potentially impacted sections.
2. **IMPORTANT**: SECTION EDITED ({section_name}) is the one that was modified. POTENTIAL IMPACTED SECTIONS are other sections that may need updates due to changes made in {section_name}.
3. **CRITICAL**: Check continuity between EDITED SECTION CONTENT and following sections in POTENTIAL IMPACTED SECTIONS. If a major new event or plot development is introduced, it requires updates even if there are no direct contradictions.
4. Apply the impact expectations above to determine which sections require adaptation.
5. Only reference section names from the POTENTIALLY IMPACTED SECTION NAMES list.
6. For every impacted section, provide detailed instructions (2-4 sentences) directly addressed to the AI editor that will adapt that section. Write as if giving instructions directly to that AI (e.g., for Expanded Plot: "Update...", "Adapt...", "Integrate..."). The instructions should include:
   - **Why** the changes made in {section_name} require this adaptation
   - **What specific content** needs to be changed or added
   - **Where in the section** the changes should be made (e.g., "in the Plot Summary section, during the Developments phase", "in Chapter X description", "in the Key Characters section")
   - **Context** about how the new change relates to existing content (e.g., "this event affects the story arc described in the Plot Summary")
7. Write instructions directly and concisely, as if addressing the AI editor that will perform the adaptation (e.g., "Update the Developments phase...", "Adapt Chapter 4 description...", "Replace all instances of...").
8. If none of the sections require an update, state that explicitly.

Output format (strict JSON):
- Respond with a single JSON object and nothing else.
- Use one of the following structures:

If no updates are needed:
{{
  "result": "NO_IMPACT",
  "message": "brief reason",
  "impacted_sections": []
}}

If updates are required:
{{
  "result": "IMPACT_DETECTED",
  "impacted_sections": [
    {{
      "name": "Section Name",
      "reason": "Detailed instructions (2-4 sentences) directly addressed to the AI editor that will adapt this section. Include: why the changes require adaptation, what specific content needs to change, where in the section the changes should be made, and context about how the new change relates to existing content. Write directly and concisely (e.g., 'Update the Developments phase...', 'Adapt Chapter 4 description...', 'Replace all instances of...')"
    }}
  ]
}}

- The JSON must include only the keys shown above.
- The impacted_sections array must list only sections from POTENTIALLY IMPACTED SECTION NAMES.
- Do not add any extra text before or after the JSON.
""").strip()


def _format_candidate_sections(sections: List[Tuple[str, str]]) -> str:
    formatted = []
    for name, content in sections:
        snippet = (content or "").strip()
        block = f"- {name}: \"{snippet}\""
        formatted.append(block)
    if not formatted:
        return "(no additional context provided)"
    return "\n".join(formatted)


def call_llm_impact_analysis(
    *,
    section_name: str,
    edited_section_content: str,
    diff_summary: str,
    candidate_sections: List[Tuple[str, str]],
    is_infill: bool = False,
    total_chapters: int = 0,
    api_url: str = None,
    model_name: str = None,
    timeout: int = 300,
) -> Tuple[str, Dict[str, Any], List[str]]:
    """
    Analizează ce secțiuni trebuie adaptate după un diff.

    Returnează:
      ("NO_IMPACT", data, impacted_sections)
      ("IMPACT_DETECTED", data, impacted_sections)
      ("UNKNOWN", {"raw": content}, [])
      ("ERROR", {"error": message}, [])
    """


    formatted_candidates = _format_candidate_sections(candidate_sections)
    candidate_names = ", ".join(name for name, _ in candidate_sections) or "(none)"

    if is_infill:
        new_total_chapters = total_chapters + 1
        infill_rule = f"""
**CRITICAL INFILL RULE**:
Since IS INFILL is "yes" (indicating a new chapter insertion), Chapters Overview is ALWAYS impacted, even if there are no contradictions. A new chapter requires:
- adding a new chapter summary
- shifting numbering of subsequent chapters ONLY if they exist (there will be {new_total_chapters} total chapters after insertion)
- adapting summaries that follow the insertion point ONLY if they exist

**IMPORTANT**: To determine if renumbering is needed, check the SECTION EDITED name. If the chapter number in SECTION EDITED is greater than {total_chapters} (the current total number of chapters), then the new chapter is being inserted at the END and NO renumbering is needed (no subsequent chapters exist). If the chapter number is less than or equal to {total_chapters}, then subsequent chapters exist and must be renumbered."""
        
        infill_chapter_rule = f"""
**CRITICAL INFILL RULE**: 
- POTENTIAL IMPACTED SECTIONS contain chapters that exist BEFORE the insertion. The insertion happens AFTER validation, so you must consider how existing chapters will be affected
- You must reference chapters by their CURRENT names (before insertion) when analyzing impact"""
        
        infill_example = """Example 5: New Chapter Insertion.
Edited Section: "Chapter 2 (Candidate)" (A new chapter inserted between Chapter 1 and Chapter 2. Content: John packs up and secretly leaves the country at night, fleeing from the authorities.)
Changes: New Chapter Created
- Chapters Overview: IMPACTED (New chapter inserted. Add summary for the new chapter (which becomes Chapter 2) explicitly stating that John makes a secret departure and leaves the country. Renumber all subsequent chapters (the new chapter becomes Chapter 2, and all following chapters shift forward by 1, so the old Chapter 2 becomes Chapter 3, etc.). Update chapter descriptions that reference the insertion point to maintain continuity.)
- Chapter 2: IMPACTED (Continuity broken - Previously John was in the country at the start of this chapter, now he is already abroad (having left in the new Chapter 2). Adapt Chapter 2 to reflect that John is already abroad, removing references to him being in the original location and updating the opening to show he's already established in the new location.)

Example 6: New Chapter Insertion at the End.
Edited Section: "Chapter 6 (Candidate)" (A new chapter inserted at the end, after Chapter 5. Current total chapters: 5. Content: John packs up and secretly leaves the country at night, fleeing from the authorities.)
Changes: New Chapter Created
- Chapters Overview: IMPACTED (New chapter inserted at the end. Add summary for the new chapter (which becomes Chapter 6) explicitly stating that John makes a secret departure and leaves the country. NO renumbering is needed since this is the last chapter - the chapter number (6) is greater than the current total (5), meaning no subsequent chapters exist to renumber.)"""
    else:
        infill_rule = ""
        infill_chapter_rule = ""
        infill_example = ""

    prompt = _IMPACT_PROMPT.format(
        section_name=section_name,
        is_infill="yes" if is_infill else "no",
        edited_section_content=edited_section_content or "(empty)",
        diff_summary=diff_summary or "(empty)",
        candidate_count=len(candidate_sections),
        candidate_sections=formatted_candidates,
        candidate_names=candidate_names,
        infill_rule=infill_rule,
        infill_chapter_rule=infill_chapter_rule,
        infill_example=infill_example,
    )

    messages = [
        {"role": "system", "content": "You are a precise story continuity analyst."},
        {"role": "user", "content": prompt},
    ]

    try:
        content = provider_manager.get_llm_response(
            task_name="impact_analyzer",
            messages=messages,
            timeout=timeout,
            temperature=0.1,
            top_p=0.3
        )
    except Exception as e:
        return ("ERROR", {"error": str(e)}, [])

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return ("UNKNOWN", {"raw": content}, [])

    result = parsed.get("result")
    if result in {"NO_IMPACT", "IMPACT_DETECTED"}:
        impacted_sections = []
        if result == "NO_IMPACT":
            parsed.setdefault("message", "No other sections require updates.")
            parsed.setdefault("impacted_sections", [])
        else:
            sections_data = parsed.get("impacted_sections") or []
            cleaned_sections = []
            for entry in sections_data:
                if isinstance(entry, dict):
                    name = entry.get("name")
                    reason = entry.get("reason")
                    if name:
                        impacted_sections.append(name)
                        cleaned_sections.append({"name": name, "reason": reason or ""})
            parsed["impacted_sections"] = cleaned_sections
        if result == "NO_IMPACT" and not impacted_sections:
            impacted_sections = []
        return (result, parsed, impacted_sections)

    return ("UNKNOWN", {"raw": content}, [])

