# -*- coding: utf-8 -*-
# pipeline/steps/overview_editor/llm.py
"""
LLM helper pentru editarea Chapters Overview bazat pe impact și diff.
"""

import os
import textwrap
import requests
import json
from utils.json_utils import extract_json_from_response

LOCAL_API_URL = os.getenv("LMSTUDIO_API_URL", "http://127.0.0.1:1234/v1/chat/completions")
MODEL_NAME = os.getenv("LMSTUDIO_MODEL", "phi-3-mini-4k-instruct")

GEN_PARAMS = {
    "temperature": 0.6,
    "top_p": 0.95,
    "max_tokens": 4096,
}

_EDIT_OVERVIEW_PROMPT = textwrap.dedent("""\
You are an expert book structure editor specializing in adapting chapter overviews to maintain continuity after changes.

Context:
A user made an edit to a section of the story. This edit has been analyzed, and the Chapters Overview needs to be updated to reflect the impact of that change.

EDITED SECTION:
\"\"\"{edited_section}\"\"\"

ORIGINAL CHAPTERS OVERVIEW:
\"\"\"{original_overview}\"\"\"

EXPANDED PLOT (reference):
\"\"\"{expanded_plot}\"\"\"

CHANGES DETECTED IN USER'S EDIT:
\"\"\"{diff_summary}\"\"\"

IMPACT REASON (why this section needs adaptation):
\"\"\"{impact_reason}\"\"\"

GENRE:
\"\"\"{genre}\"\"\"

{chapter_section}

Task:
1. First, analyze the impact and changes to determine if this is a BREAKING CHANGE:
   - A breaking change requires significant restructuring, contradicts established facts, or fundamentally alters the story's direction
   - A non-breaking change can be accommodated with minimal modifications while preserving most of the original content

2. Then, adapt the Chapters Overview accordingly:

{adaptation_instructions}

Output Requirements:
- Maintain the same Markdown format as the original (#### Chapter N: *Title* followed by **Description:**)
- Preserve the same number of chapters
- Keep chapter titles unchanged unless the impact requires title updates
- Preserve all chapter descriptions that are not affected by the changes
- Update only the parts that need to change based on the impact
- Ensure the adapted overview remains coherent with the Expanded Plot

You must output a JSON object with the following structure:
{{
  "is_breaking_change": true/false,
  "adapted_overview": "the complete adapted Chapters Overview in Markdown format"
}}

Output ONLY the JSON object, no other text or explanations.
""").strip()


def call_llm_edit_overview(
    original_overview: str,
    impact_reason: str,
    diff_summary: str,
    expanded_plot: str,
    genre: str = "",
    edited_section: str = None,
    new_chapter_content: str = None,
    chapter_index: int = None,
    *,
    api_url: str = None,
    model_name: str = None,
    timeout: int = 300,
) -> str:
    """
    Editează Chapters Overview bazat pe impact și diff.
    AI-ul determină dacă e breaking change și adaptează în consecință.
    
    Args:
        edited_section: Numele secțiunii editate (ex: "Chapter 4" sau "Expanded Plot")
        new_chapter_content: Conținutul complet al capitolului nou (dacă a fost editat un capitol)
        chapter_index: Index-ul capitolului editat (1-based, dacă e cazul)
    """
    url = api_url or LOCAL_API_URL
    model = model_name or MODEL_NAME

    edited_section = edited_section or "Unknown section"
    
    if edited_section.startswith("Chapter ") and new_chapter_content and chapter_index:
        chapter_section = f"""NEW CHAPTER {chapter_index} CONTENT (the complete edited chapter):
\"\"\"{new_chapter_content}\"\"\"

IMPORTANT: The user edited Chapter {chapter_index}. You need to:
1. Analyze the new chapter content and create a summary of what actually happens in it
2. Update the description of Chapter {chapter_index} in the Chapters Overview to incorporate the user's changes
3. The new description should be based on a summary of this new chapter content, while preserving everything from the old description that is still valid
4. Do NOT add anything extra beyond what is in the new chapter content
5. If this is a BREAKING CHANGE and the impact reason provides instructions, adapt the following chapters to naturally continue from this modified chapter, using creativity while maintaining coherence
"""
        adaptation_instructions = f"""- Generate the description for Chapter {chapter_index} based on a summary of the NEW CHAPTER CONTENT provided above
   - Preserve everything from the old Chapter {chapter_index} description that is still valid
   - Do NOT add anything beyond what is in the new chapter content
   - If BREAKING CHANGE: Adapt subsequent chapters (if mentioned in impact reason) to naturally continue from this modified chapter, using creativity while maintaining coherence
   - If NON-BREAKING CHANGE: Make MINIMAL modifications to other chapters — only what is strictly necessary
- If BREAKING CHANGE: Significant modifications are allowed, but preserve as much of the original overview as possible. Only change what is necessary to address the breaking change.
- If NON-BREAKING CHANGE: Make MINIMAL modifications — only what is strictly necessary. Preserve the vast majority of the original text unchanged."""
    else:
        chapter_section = ""
        adaptation_instructions = """- The most important priority is COHERENCE with the Expanded Plot
   - Modify impacted chapters according to the impact reason and diff so that chapters are coherent with the Expanded Plot
   - Preserve everything that is still valid, but coherence with Expanded Plot takes precedence
- If BREAKING CHANGE: Significant modifications are allowed, but preserve as much of the original overview as possible. Only change what is necessary to address the breaking change.
- If NON-BREAKING CHANGE: Make MINIMAL modifications — only what is strictly necessary. Preserve the vast majority of the original text unchanged."""

    prompt = _EDIT_OVERVIEW_PROMPT.format(
        edited_section=edited_section,
        original_overview=original_overview or "",
        expanded_plot=expanded_plot or "",
        diff_summary=diff_summary or "",
        impact_reason=impact_reason or "",
        genre=genre or "unspecified",
        chapter_section=chapter_section,
        adaptation_instructions=adaptation_instructions,
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a precise story structure editor that adapts chapter overviews while preserving as much original content as possible. You must output only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        **GEN_PARAMS,
    }

    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        
        # Parse JSON response (suportă atât JSON pur cât și wrappat în tag-uri)
        try:
            result = extract_json_from_response(content)
            return result.get("adapted_overview", content)
        except (json.JSONDecodeError, ValueError):
            # Fallback dacă nu e JSON valid
            return content
    except Exception as e:
        return f"Error during overview editing: {e}"

