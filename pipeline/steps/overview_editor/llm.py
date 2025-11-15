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

EXPANDED PLOT (already modified according to the diff):
\"\"\"{expanded_plot}\"\"\"

CHANGES DETECTED IN USER'S EDIT:
\"\"\"{diff_summary}\"\"\"

IMPACT REASON (why this section needs adaptation):
\"\"\"{impact_reason}\"\"\"

GENRE:
\"\"\"{genre}\"\"\"

{chapter_section}

Examples:

Example 1: Chapter 4 (out of 7) is modified. Original Chapter 4 description: "Gary faces danger but survives." New chapter content: Gary dies at the end of Chapter 4.
- BREAKING CHANGE: Yes (Gary's death requires major adaptations to Chapters 5-7)
- Chapters Overview adaptation: Update Chapter 4 description to reflect Gary's death. Adapt Chapters 5-7 descriptions to account for Gary's absence (characters react to his death, story continues without him, etc.)

Example 2: Chapter 3 (out of 5) is modified. Original Chapter 3 description: "Susan visits the market, her brown eyes scanning the stalls." New chapter content: Susan visits the market, her green eyes scanning the stalls. Eye color change only.
- BREAKING CHANGE: No (minor detail change)
- Chapters Overview adaptation: Update Chapter 3 description to mention green eyes instead of brown. If Chapter 5 also mentions eye color, make minimal update there for consistency. Preserve all other content unchanged.

Example 3: Chapter 4 (out of 5) is modified. Original Chapter 4 description: "John returns home and reflects on his day." New chapter content: John returns home, but then decides to embark on an adventure to Mount Everest the next day. This is a major new plot development.
- BREAKING CHANGE: Yes (major new plot development requires Chapter 5 to adapt significantly)
- Chapters Overview adaptation: Update Chapter 4 description to include John's decision to go to Mount Everest. Adapt Chapter 5 description to reflect John being on Everest adventure instead of continuing from the previous home scene.

Example 4: Expanded Plot is modified. Character name "Robert" changed to "Michael" throughout. Chapters Overview mentions Robert in Chapter 2 and Chapter 4 descriptions.
- BREAKING CHANGE: No (simple name replacement)
- Chapters Overview adaptation: Replace "Robert" with "Michael" in Chapter 2 and Chapter 4 descriptions. Preserve all other content unchanged.

Example 5: Expanded Plot is modified. Original plot: "The story follows a peaceful journey." Modified plot: "The story follows a journey that ends in a violent confrontation with enemies." This affects the climax described in Chapters Overview for Chapters 6-7 (out of 7).
- BREAKING CHANGE: Yes (fundamental change to story direction requires major adaptations)
- Chapters Overview adaptation: Adapt Chapters 6-7 descriptions to reflect the violent confrontation ending, ensuring coherence with the modified Expanded Plot. Preserve earlier chapters as much as possible.

Task:
1. First, analyze the impact and changes to determine if this is a BREAKING CHANGE:
   - The Expanded Plot provided above is already modified according to the diff. Do NOT compare against an "original" Expanded Plot that doesn't exist here.
   - A BREAKING CHANGE means that subsequent chapters need MAJOR adaptations to continue naturally from the changes made (according to diff_summary and impact_reason)
   - A NON-BREAKING CHANGE means the changes can be accommodated with minimal modifications, but you may still need to make minor adjustments to subsequent chapters for coherence
   - Consider: Do the changes require substantial restructuring of following chapters, or can they flow naturally with minor tweaks?

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

The user edited Chapter {chapter_index}. You need to:
1. Analyze the new chapter content and create a summary of what actually happens in it
2. Update the description of Chapter {chapter_index} in the Chapters Overview to incorporate the user's changes
3. The new description should be based on a summary of this new chapter content, while preserving everything from the old description that is still valid
4. The new description must be STRICTLY based ONLY on what happens in the new chapter content. Do NOT add conclusions, realizations, or consequences that are not explicitly stated in the new chapter content
5. If this is a BREAKING CHANGE and the impact reason provides instructions, adapt the following chapters to naturally continue from this modified chapter, using creativity while maintaining coherence
"""
        adaptation_instructions = f"""- Generate the description for Chapter {chapter_index} based on a summary of the NEW CHAPTER CONTENT provided above
   - Preserve everything from the old Chapter {chapter_index} description that is still valid
   - Do NOT add anything beyond what is in the new chapter content
   - If BREAKING CHANGE: Adapt subsequent chapters (as indicated in impact_reason) with significant modifications to naturally continue from this modified chapter, using creativity while maintaining coherence
   - If NON-BREAKING CHANGE: Make MINIMAL modifications to subsequent chapters for coherence — only what is necessary to ensure they flow naturally from the modified Chapter {chapter_index}
- If BREAKING CHANGE: Significant modifications to subsequent chapters are allowed, but preserve as much of the original overview as possible. Only change what is necessary to address the breaking change.
- If NON-BREAKING CHANGE: Make MINIMAL modifications to subsequent chapters for coherence. Preserve the vast majority of the original text unchanged, but ensure smooth flow from the modified chapter."""
    else:
        chapter_section = ""
        adaptation_instructions = """- The most important priority is COHERENCE with the Expanded Plot (which is already modified according to the diff)
   - Modify impacted chapters according to the impact reason and diff so that chapters are coherent with the Expanded Plot
   - Preserve everything that is still valid, but coherence with Expanded Plot takes precedence
- If BREAKING CHANGE: Significant modifications to impacted chapters are allowed, but preserve as much of the original overview as possible. Only change what is necessary to address the breaking change.
- If NON-BREAKING CHANGE: Make MINIMAL modifications to impacted chapters for coherence — only what is necessary to ensure they align with the modified Expanded Plot. Preserve the vast majority of the original text unchanged."""

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

