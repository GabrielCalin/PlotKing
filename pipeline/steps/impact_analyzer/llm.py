# -*- coding: utf-8 -*-
# pipeline/steps/impact_analyzer/llm.py
"""
LLM helper pentru analiza impactului unui diff asupra altor secțiuni.
"""

import os
import textwrap
import requests
import json
from typing import List, Tuple

LOCAL_API_URL = os.getenv("LMSTUDIO_API_URL", "http://127.0.0.1:1234/v1/chat/completions")
MODEL_NAME = os.getenv("LMSTUDIO_MODEL", "phi-3-mini-4k-instruct")

GEN_PARAMS = {
    "temperature": 0.1,
    "top_p": 0.3
}

_IMPACT_PROMPT = textwrap.dedent("""\
You are a continuity analyst helping a human editor understand which story sections need updates after a change.

Inputs you receive:
- SECTION EDITED: {section_name}
- EDITED SECTION CONTENT (after modification):
\"\"\"{edited_section_content}\"\"\"
- SUMMARY OF CHANGES:
\"\"\"{diff_summary}\"\"\"
- POTENTIAL IMPACTED SECTIONS ({candidate_count}):
{candidate_sections}
- POTENTIALLY IMPACTED SECTION NAMES (use only these exact names in references): {candidate_names}

Impact Expectations:

**Expanded Plot changes**: Impact occurs if the change contradicts existing content or breaks continuity with other sections. All sections may be affected.

**Chapters Overview changes**: Impact occurs if the change contradicts existing content or breaks continuity. If continuity is broken, all following chapters need adaptation and should be marked as impacted. When marking Chapters Overview as impacted, you must clearly specify which chapters from Chapters Overview need adaptation in the reason.

**Chapter changes**: Impact occurs if the change:
1. Contradicts something (even minor details not mentioned in Expanded Plot or Chapters Overview)
2. Breaks continuity with following sections
3. Introduces a major new event or plot development that affects the story's direction

For major new events: You must check continuity between the EDITED SECTION CONTENT and the following sections in POTENTIAL IMPACTED SECTIONS. If a major new event is introduced (e.g., character makes a significant decision, new plot development, location change), it requires updates in:
- Expanded Plot (to include the new event)
- Chapters Overview (to reflect the new development)
- Following chapters (to maintain continuity with the new event)

Examples:

Example 1: Expanded Plot states character Gary survives, and Chapters Overview indicates this happens in Chapter 4 (out of 7 chapters). Modification: Gary dies in Chapter 4.
- Expanded Plot: IMPACTED (Gary dies, contradicts survival)
- Chapters Overview: IMPACTED (continuity broken, Chapters 5-7 need adaptation)
- Chapters 5, 6, 7: IMPACTED (continuity broken)

Example 2: Character name changed in Expanded Plot. That character appears in Chapter 3 description (out of 5 chapters).
- Chapters Overview: IMPACTED (needs name update in Chapter 3 description)
- Chapter 3: IMPACTED (name appears, needs update)
- Chapter 4: IMPACTED (name appears but not mentioned in Chapters Overview, still needs update)

Example 3: Minor change in Chapter 3 (out of 5): Susan's eyes are green instead of brown. Eye color is also mentioned in Chapter 5.
- Chapter 5: IMPACTED (eye color detail needs update for consistency)

Example 4: Chapter 4 (out of 5) is modified. Previously, Chapter 4 ended with John at home. New modification: John decides to embark on an adventure to Mount Everest the next day. This is a major new plot development not mentioned in Expanded Plot or Chapters Overview.
- Expanded Plot: IMPACTED (major new event - John's Everest adventure - needs to be included)
- Chapters Overview: IMPACTED (needs to reflect John's departure and adventure in Chapter 4 description, Chapter 5 needs adaptation)
- Chapter 5: IMPACTED (must account for John being on Everest adventure, continuity broken with previous ending)

Task:
1. Review the edited section content, change summary, and potentially impacted sections.
2. **IMPORTANT**: SECTION EDITED ({section_name}) is the one that was modified. POTENTIAL IMPACTED SECTIONS are other sections that may need updates due to changes made in {section_name}.
3. **CRITICAL**: Check continuity between EDITED SECTION CONTENT and following sections in POTENTIAL IMPACTED SECTIONS. If a major new event or plot development is introduced, it requires updates even if there are no direct contradictions.
4. Apply the impact expectations above to determine which sections require adaptation.
5. Only reference section names from the POTENTIALLY IMPACTED SECTION NAMES list.
6. For every impacted section, provide a short explanation (2 sentences max) describing why the changes made in {section_name} require this adaptation.
7. If none of the sections require an update, state that explicitly.

Output format (strict):
If no updates needed:
RESULT: NO_IMPACT
IMPACTED_SECTIONS: []
MESSAGE: brief reason

If updates are required:
RESULT: IMPACT_DETECTED
IMPACTED_SECTIONS: ["Section Name", "Another Section"]
IMPACT:
- Section: <section name>
  Reason: <short explanation mentioning that changes in {section_name} require this adaptation>
- Section: <...>
  Reason: <...>

Keep the tone concise and focused on actionable reasoning.
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


def _extract_impacted_sections(content: str) -> List[str]:
    impacted = []
    for line in content.splitlines():
        if line.strip().startswith("IMPACTED_SECTIONS:"):
            try:
                _, rest = line.split(":", 1)
                rest = rest.strip()
                if rest.startswith("[") and rest.endswith("]"):
                    inner = rest[1:-1].strip()
                    if inner:
                        items = [item.strip().strip('"') for item in inner.split(",")]
                        impacted = [item for item in items if item]
                    else:
                        impacted = []
                else:
                    impacted = []
            except ValueError:
                impacted = []
            break
    return impacted


def call_llm_impact_analysis(
    *,
    section_name: str,
    edited_section_content: str,
    diff_summary: str,
    candidate_sections: List[Tuple[str, str]],
    api_url: str = None,
    model_name: str = None,
    timeout: int = 300,
) -> Tuple[str, str, List[str]]:
    """
    Analizează ce secțiuni trebuie adaptate după un diff.

    Returnează:
      ("NO_IMPACT", message, impacted_sections)
      ("IMPACT_DETECTED", details, impacted_sections)
      ("UNKNOWN", raw, [])
      ("ERROR", message, [])
    """
    url = api_url or LOCAL_API_URL
    model = model_name or MODEL_NAME

    formatted_candidates = _format_candidate_sections(candidate_sections)
    candidate_names = ", ".join(name for name, _ in candidate_sections) or "(none)"

    prompt = _IMPACT_PROMPT.format(
        section_name=section_name,
        edited_section_content=edited_section_content or "(empty)",
        diff_summary=diff_summary or "(empty)",
        candidate_count=len(candidate_sections),
        candidate_sections=formatted_candidates,
        candidate_names=candidate_names,
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a precise story continuity analyst."},
            {"role": "user", "content": prompt},
        ],
        **GEN_PARAMS,
    }

    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        content = (
            data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
        )
    except Exception as e:
        return ("ERROR", str(e), [])

    impacted_sections = _extract_impacted_sections(content)
    up = content.upper()
    if "RESULT: NO_IMPACT" in up:
        return ("NO_IMPACT", content, impacted_sections)
    if "RESULT: IMPACT_DETECTED" in up:
        return ("IMPACT_DETECTED", content, impacted_sections)
    return ("UNKNOWN", content, [])
