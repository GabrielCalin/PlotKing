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
    "temperature": 0.3,
    "top_p": 0.9
}

_IMPACT_PROMPT = textwrap.dedent("""\
You are a continuity analyst helping a human editor understand which story sections need updates after a change.

Inputs you receive:
- SECTION EDITED: {section_name}
- SUMMARY OF CHANGES:
\"\"\"{diff_summary}\"\"\"
- POTENTIAL IMPACTED SECTIONS ({candidate_count}):
{candidate_sections}
- SECTION NAMES (for strict references only): {candidate_names}

Task:
1. Review the change summary and the list of potentially impacted sections.
2. Decide which sections actually require adaptation to preserve continuity, character usage, settings, or plot logic.
3. Only reference section names that appear in the provided SECTION NAMES list.
4. For every section that needs adaptation, provide a short explanation (2 sentences max) describing why the change matters.
5. If none of the sections require an update, state that explicitly.

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
  Reason: <short explanation>
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
