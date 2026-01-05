# -*- coding: utf-8 -*-
# llm/chat_filler/llm.py

import textwrap
import json
import random
from typing import List, Optional, Dict, Any
from provider import provider_manager


def _compute_word_target(anpc: Optional[int]) -> int:
    if anpc and anpc > 0:
        base_words = anpc * 500
        return int(random.uniform(base_words * 0.75, base_words * 1.25))
    return random.randint(1500, 2500) # Slightly shorter default for fills than chapters


# ---------------------------------------
# CHAT FILLER SYSTEM PROMPT
# ---------------------------------------
_CHAT_FILLER_SYSTEM_PROMPT = textwrap.dedent("""
You are "Plot King", a creative, proactive, and helpful AI writing assistant specialized in **bridging narrative gaps**.

Your Goal:
Help the user write or refine a "Fill" chapter (a transition scene or chapter) that fits perfectly between the existing previous and next chapters.

Context Provided:
- **Previous Chapter(s):** The story leading up to this point.
- **Next Chapter(s):** Where the story goes immediately after this point.
- **Original Fill Content:** The initial draft of this section (if any), which serves as the "safe" baseline.
- **Current Draft:** The content currently being edited.

Your Responsibilities:
1. **Maintain Continuity (Default):**
   - Ensure characters, setting, tone, and timeline flow logically from the Previous Chapter into the Next Chapter.
   - Do NOT introduce contradictions unless explicitly asked.
   - If the user's request would break continuity with the Next Chapter, **warn them** but proceed if they insist.

2. **Proactive Assistance:**
   - Ask clarifying questions about what happens in this gap.
   - Suggest creative ideas that link the two sides of the story effectively.
   - Be helpful and encouraging.

3. **Content Generation:**
   - If the user asks you to "write", "generate", or "rewrite" the scene/chapter, produce the full text in `new_content`.
   - **Target Length:** Approximately {word_target} words.
   - **Writing Style:**
     - Maintain a clear, engaging, and immersive prose style appropriate for long-form fiction.
     - Use natural dialogue, expressive narration, and sensory details.
     - **Do not** subdivide the text into numbered or titled scenes; maintain smooth internal flow.
   - **Continuity:**
     - Ensure logical consistency with previous chapters (characters, setting, timeline).
     - Seamlessly transition into the **Next Chapter**; the end of your text should be the natural "before" state of the next chapter's beginning.
   - **Format:**
     - **Title:** Start with a catchy title formatted as a Markdown H2 heading (`## Title`).
     - Use Markdown (e.g., `*italics*`, `**bold**`, `---` for scene breaks).
     - Do NOT add meta-commentary, titles (unless requested), or "Here is the text" prefixes inside `new_content`. It should be pure story text.

4. **Tone:**
   - Creative, enthusiastic, professional.

OUTPUT FORMAT:
You must output a valid JSON object with the following keys:
- "response": (string) Your conversational reply to the user.
- "new_content": (string or null) The full text of the updated/generated Fill chapter. ONLY include this if you have generated or edited the story content. If you are just chatting, set this to null.

Example JSON:
{{
  "response": "Here is a draft of the transition scene. I focused on the urgency of the moment.",
  "new_content": "The door slammed shut..."
}}
""").strip()


def call_llm_chat_filler(
    previous_chapters_text: str,
    next_chapters_text: str,
    original_fill_content: str,
    current_content: str,
    chat_history: List[Dict[str, str]],
    user_message: str,
    *,
    anpc: Optional[int] = None,
    timeout: int = 60,
) -> Dict[str, Any]:
    """
    Calls the LLM as Plot King (Filler Mode) to chat with the user.
    Returns a dict with 'response' and optional 'new_content'.
    """

    # 0. Compute word target
    word_target = _compute_word_target(anpc)

    # 1. Construct the system context
    system_context = _CHAT_FILLER_SYSTEM_PROMPT.format(word_target=word_target)
    
    # 2. Build the messages list
    context_block = f"""
    
=== CONTEXT START ===
--- PREVIOUS CHAPTERS (Ending of previous) ---
{previous_chapters_text if previous_chapters_text else "(No previous chapters)"}

--- NEXT CHAPTERS (Beginning of next) ---
{next_chapters_text if next_chapters_text else "(No next chapters)"}

--- ORIGINAL FILL CONTENT (Baseline) ---
{original_fill_content if original_fill_content else "(Empty)"}

--- CURRENT DRAFT (What we are editing) ---
{current_content if current_content else "(Empty)"}
=== CONTEXT END ===
    """

    messages = [
        {"role": "system", "content": system_context + context_block}
    ]

    # 3. Append history
    for msg in chat_history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        # Filter out system instructions from history if needed, but usually fine to keep
        messages.append({"role": role, "content": content})

    # 4. Handle User Message
    if user_message == "START_SESSION":
        instructions = "The user has just opened the chat for this Fill section. Introduce yourself, acknowledge the context (transitions between Ch X and Ch Y), and ask how you can help bridge the gap. Return only JSON."
        messages.append({"role": "user", "content": f"[SYSTEM_INSTRUCTION]: {instructions}"})
    elif user_message:
        messages.append({"role": "user", "content": user_message})

    try:
        response_text = provider_manager.get_llm_response(
            task_name="chat_filler",
            messages=messages,
            timeout=timeout,
            temperature=0.7, 
            max_tokens=16000
        )
        
        return _parse_response(response_text)

    except Exception as e:
        return {"response": f"Plot King (Filler) stumbled: {e}", "new_content": None}


def _parse_response(text: str) -> Dict[str, Any]:
    import json
    
    # Clean up markdown code blocks if present
    clean_text = text.strip()
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    if clean_text.startswith("```"):
        clean_text = clean_text[3:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
    clean_text = clean_text.strip()
    
    try:
        data = json.loads(clean_text)
        return {
            "response": data.get("response", text),
            "new_content": data.get("new_content", None)
        }
    except json.JSONDecodeError:
        # Fallback: Try to find JSON block inside text
        start = clean_text.find('{')
        end = clean_text.rfind('}')
        if start != -1 and end != -1:
            try:
                json_str = clean_text[start:end+1]
                data = json.loads(json_str)
                return {
                    "response": data.get("response", clean_text),
                    "new_content": data.get("new_content", None)
                }
            except:
                pass
        
        # Absolute fallback: treat as pure response
        return {"response": text, "new_content": None}
