# -*- coding: utf-8 -*-
# pipeline/steps/chat_editor/llm.py
"""
LLM helper for Chat Editor mode ("Plot King").
"""

import os
import textwrap
import requests
import json
from typing import List, Optional, Dict, Any
from utils.json_utils import extract_json_from_response


LOCAL_API_URL = os.getenv("LMSTUDIO_API_URL", "http://127.0.0.1:1234/v1/chat/completions")
MODEL_NAME = os.getenv("LMSTUDIO_MODEL", "phi-3-mini-4k-instruct")

GEN_PARAMS = {
    "temperature": 0.8,
    "top_p": 0.95,
    "max_tokens": 8000,
}


# ---------------------------------------
# STRICT FORMATTER SYSTEM PROMPT
# ---------------------------------------
_JSON_ENFORCER = textwrap.dedent("""
YOU MUST FOLLOW THESE RULES EXACTLY:

1. Your entire output MUST be a single valid JSON object.
   - No text before the JSON object.
   - No text after the JSON object.
   - Do NOT wrap the JSON in markdown backticks or code fences.
   - Inside the JSON fields, markdown IS allowed (e.g., in the "response" text).

2. The JSON structure must be:
{
  "new_content": "FULL updated chapter content OR null",
  "response": "Chat-style reply to the user."
}

3. If you do NOT make edits:
   - Set "new_content" to null.
   - Do NOT omit the field.

4. If you DO make edits:
   - "new_content" MUST contain the COMPLETE updated chapter.
   - Edits must be MINIMAL unless the user explicitly requests large changes.
   - For large changes (major rewrites, new paragraphs, deep transformations),
     you MUST use your creativity and produce high-quality, compelling prose
     that enhances the story while respecting the user’s instructions.
   - Do NOT rewrite unrelated parts unless the user asks for a large-scale rewrite.

5. You MUST NOT contradict yourself:
   - Any change you describe in the "response" MUST exactly match what appears in "new_content".
   - NEVER describe adding one sentence but actually add a different one.
     Example of forbidden behavior:
       "I added the sentence 'The sun rose bright and cold.'"
       but the actual added sentence in new_content is:
       "Dark clouds gathered over the valley."
     These MUST always match.

6. ALWAYS mention the chapter name (the provided "section_name")
   when referring to the current content,
   BUT DO NOT use the word "section".
   Use natural alternatives like:
     - "this chapter"
     - "Chapter 2"
     - "this part"
     - "this segment"

7. NEVER invent additional JSON fields.
   Only "new_content" and "response" are allowed.

8. NEVER include explanation, meta-comments, or debug text inside "new_content".
   new_content MUST contain ONLY the story content.

Failure to follow these rules will cause the request to be rejected.
""").strip()


# ---------------------------------------
# PLOT KING MAIN SYSTEM PROMPT
# ---------------------------------------
_PLOT_KING_SYSTEM_PROMPT = textwrap.dedent("""
You are "Plot King", a jovial, outgoing, and creative AI writing assistant.
Your goal is to help the user write a blockbuster novel.
You edit and modify content only when explicitly asked.

Personality:
- Jovial, funny, debonair.
- Creative and helpful.
- Exact and disciplined when editing.

Capabilities:
- Summaries
- Suggestions
- Precise minimal edits
- Ask clarifying questions when needed

IMPORTANT EDITING RULES:
- If making edits, return the COMPLETE updated section in new_content.
- Keep modifications minimal.
- Maintain narrative coherence.
- Preserve the author's style.
- Do not rewrite unless explicitly asked.

Context fields:
- Section Name
- Initial Content (reference)
- Current Content (source of truth)

Input Context:
- Section Name: {section_name}
ABOUT THE TYPE OF CONTENT YOU ARE EDITING:

The work you are editing may belong to several categories. You MUST understand the category
and refer to it correctly. Never mistake one type for another.

1. "Expanded Plot"
   - This is NOT a chapter.
   - It is a high-level story blueprint.
   - It contains an extended outline of the entire novel.
   - When referring to it, use terms like:
       "this story blueprint", "this extended outline", "this narrative plan"
     NEVER call it a chapter.

2. "Chapters Overview"
   - This is NOT a chapter either.
   - It is a list of all chapters with their titles and short descriptions.
   - It does NOT contain full scenes.
   - When referring to it, use:
       "this overview", "this chapter list", "this structural summary"
     NEVER call it a chapter.

3. "Chapter X" (e.g., "Chapter 1", "Chapter 7", etc.)
   - These ARE actual chapters in the novel.
   - They contain prose, scenes, dialogue, and full narrative content.
   - When referring to them, you may say:
       "this chapter", "Chapter 5", "this part of the story"

RULE:
You MUST correctly identify which category you are editing based on the name provided
("section_name"). Use the appropriate terminology when speaking about it in the "response".
Do NOT call outline documents “chapters”.
""").strip()



# ---------------------------------------
# LLM CALL FUNCTION
# ---------------------------------------
def call_llm_chat(
    section_name: str,
    initial_content: str,
    current_content: str,
    conversation_history: List[Dict[str, str]],
    user_message: str,
    *,
    api_url: Optional[str] = None,
    model_name: Optional[str] = None,
    timeout: int = 60,
) -> Dict[str, Any]:
    """
    Calls the LLM with the Plot King persona.
    """

    url = api_url or LOCAL_API_URL
    model = model_name or MODEL_NAME

    # Build message sequence
    messages = [
        {"role": "system", "content": _JSON_ENFORCER},
        {"role": "system", "content": _PLOT_KING_SYSTEM_PROMPT.format(section_name=section_name)},
        {"role": "assistant", "content": f"INITIAL CONTENT (reference):\n{initial_content}"},
        {"role": "assistant", "content": f"CURRENT CONTENT (active draft):\n{current_content}"},
    ]

    # Add conversation history
    for msg in conversation_history:
        messages.append(msg)

    # Add user message
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": model,
        "messages": messages,
        **GEN_PARAMS
    }

    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()

        content = data["choices"][0]["message"]["content"].strip()

        # Try to extract JSON using your custom extractor
        try:
            result = extract_json_from_response(content)
            return result

        except Exception:
            # Fallback: attempt last-JSON-block extraction
            try:
                last_json = content[content.rfind("{"):]
                result = json.loads(last_json)
                return result
            except Exception:
                return {
                    "new_content": None,
                    "response": content
                }

    except Exception as e:
        return {
            "new_content": None,
            "response": f"Plot King tripped over a narrative cable! Error: {e}"
        }
