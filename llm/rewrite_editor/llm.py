# -*- coding: utf-8 -*-
# pipeline/steps/rewrite_editor/llm.py


import textwrap
import json
from typing import Dict, Any, Optional
from utils.json_utils import extract_json_from_response
from provider import provider_manager
from state.settings_manager import settings_manager


_REWRITE_PROMPT = textwrap.dedent("""\
You are an expert fiction editor and co-author. Your task is to rewrite a specific selected text within a larger section based on user instructions.

Context:
The user has selected a portion of text from a story section.
- **Section Content (for context):**
\"\"\"{section_content}\"\"\"
- **Selected Text (to be replaced):**
\"\"\"{selected_text}\"\"\"
- **Context Before Selection (last 25 chars):** "{context_before}"
- **Context After Selection (first 25 chars):** "{context_after}"

User Instructions:
\"\"\"{instructions}\"\"\"

Task:
1. Analyze the User Instructions.
   - If the instructions are NOT valid editing requests (e.g., random gibberish, questions unrelated to editing, nonsense), return "success": false.
   - If the instructions are valid, proceed to rewrite the Selected Text.
2. Rewrite the Selected Text to satisfy the instructions.
   - The rewrite must fit naturally into the surrounding context (Section Content).
   - Maintain the style, tone, and continuity of the story.
   - If the selection is in the middle of a sentence, ensure the rewritten text connects grammatically and logically with the parts before and after.
   - If the instruction implies adding text after the selection, include the original selection (or a modified version of it) followed by the new addition.

Examples:

Example 1:
Selected Text: "The door creaked open."
Instructions: "Make it more ominous."
Response:
{{
  "success": true,
  "edited_text": "The heavy oak door groaned in protest as it slowly swung inward, revealing the darkness beyond."
}}

Example 2:
Selected Text: "He walked to the store."
Instructions: "run instead of walk"
Response:
{{
  "success": true,
  "edited_text": "He sprinted to the store."
}}

Example 3 (Mid-sentence):
Selected Text: "blue"
Context: "The sky was [blue] and clear."
Instructions: "change to stormy gray"
Response:
{{
  "success": true,
  "edited_text": "stormy gray"
}}

Example 4 (Append):
Selected Text: "She smiled."
Instructions: "add that she also waved"
Response:
{{
  "success": true,
  "edited_text": "She smiled and gave a cheerful wave."
}}

Example 5 (Failure):
Selected Text: "The sun set."
Instructions: "What is the capital of France?"
Response:
{{
  "success": false,
  "edited_text": "",
  "message": "The instructions do not appear to be a valid editing request."
}}

Output Format:
Return ONLY a JSON object with the following structure:
{{
  "success": true/false,
  "edited_text": "The rewritten text (if success is true)",
  "message": "Optional error message (if success is false)"
}}
""").strip()

def call_llm_rewrite_editor(
    section_content: str,
    selected_text: str,
    instructions: str,
    context_before: str = "",
    context_after: str = "",
    *,
    api_url: Optional[str] = None,
    model_name: Optional[str] = None,
    timeout: int = 60,
) -> Dict[str, Any]:
    """
    Calls the LLM to rewrite the selected text based on instructions.
    """


    prompt = _REWRITE_PROMPT.format(
        section_content=section_content or "",
        selected_text=selected_text or "",
        instructions=instructions or "",
        context_before=context_before or "",
        context_after=context_after or "",
    )


    messages = [
        {"role": "system", "content": "You are a helpful AI editor. Output only valid JSON."},
        {"role": "user", "content": prompt},
    ]

    task_params = settings_manager.get_task_params("rewrite_editor")
    retries = task_params.get("retries", 3)
    if retries is None:
        retries = 3
    retries = max(0, int(retries))

    last_error = None
    last_content = None

    for attempt in range(retries + 1):
        try:
            content = provider_manager.get_llm_response(
                task_name="rewrite_editor",
                messages=messages
            )
            last_content = content
        except Exception as e:
            last_error = str(e)
            if attempt < retries:
                continue
            return {
                "success": False,
                "edited_text": "",
                "message": f"Error calling LLM: {last_error}"
            }

        try:
            result = extract_json_from_response(content)
            return result
        except (json.JSONDecodeError, ValueError):
            if attempt < retries:
                continue
            return {
                "success": False,
                "edited_text": "",
                "message": "Failed to parse AI response."
            }

    return {
        "success": False,
        "edited_text": "",
        "message": f"Error calling LLM: {last_error or 'Unknown error'}"
    }

