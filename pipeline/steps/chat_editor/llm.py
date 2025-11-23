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
  "response": "Chat-style reply to the user.",
  "new_content": "FULL updated chapter content (ONLY if edits were made)"
}

3. If you do NOT make edits:
   - Omit the "new_content" field entirely OR set it to null.

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
   Only "response" and optionally "new_content" are allowed.

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
        {"role": "assistant", "content": f"SECTION NAME: {section_name}"},
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
                    "response": content,
                    "new_content": None
                }

    except Exception as e:
        return {
            "response": f"Plot King tripped over a narrative cable! Error: {e}",
            "new_content": None
        }
