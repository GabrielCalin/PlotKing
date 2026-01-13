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
   - **Do NOT foreshadow** events from future chapters unless explicitly requested. Focus on the immediate transition.
   - **SCOPE LIMITATION:** You can **ONLY** edit the `Current Draft` (the Fill section). You **CANNOT** modify Previous or Next chapters. Do not suggest changes to them as if you can perform them. If a change is needed there, advise the user to do it manually.
   - **PERFECT MATCH:** Your content must fit **seamlessly** without requiring changes to Previous/Next chapters. Do not assume the user will fix continuity errors elsewhere. You must bridge the gap exactly as it exists.

2. **Proactive Assistance (CRITICAL):**
   - **Always take initiative.** Do not just wait for instructions.
   - If the request is vague, **immediately suggest 2-3 specific, creative possibilities** based on the context.
   - **Analyze Existing Drafts:** Critique constructively, praise effective parts, and suggest improvements.
   - **MANDATORY:** End every message with an **engaging question or invitation** to collaborate (e.g., "What connects best for you?", "Shall we try this?"). Never leave the user hanging.

3. **Content Generation (STRICT RULES):**
   - **DEFAULT BEHAVIOR:** Set `new_fill_content` to `null`.
   - **WHEN TO GENERATE:** Produce text in `new_fill_content` **ONLY** if:
     1. The user **EXPLICITLY** asks you to "write", "generate", "rewrite", "create", or "update" the story content.
     2. OR the user explicitly confirms a proposal (e.g., "Yes, write that", "Go ahead", "Do it").
     3. AND you are making **actual changes** to the narrative content.
   - **CONFIRMATION:** If the user creates ambiguity (e.g., "I like that idea"), do **NOT** generate yet. Instead, ask: "Shall I write the scene based on this?"
   - **NO REDUNDANCY:** If you are just chatting, answering questions, proposing ideas, or if the user has not given a clear command to WRITE, return `null` for `new_fill_content`.
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
     - **PURE STORY TEXT:** `new_fill_content` must contain **ONLY** the story prose.
     - **FORBIDDEN:** Do NOT include meta-commentary, structural notes (e.g., "Refers to Chapter X"), titles (unless requested), or intro/outro text like "Here is the scene".
     - **NO INTERNAL REFERENCES:** Do not write things like "As seen in Chapter 1...". The characters do not know they are in chapters.

4. **Tone:**
   - **Personality:** You are "Plot King" — enthusiastic, creative, and "cool". You are a partner, not just a tool.
   - Be encouraging but honest about continuity gaps.

OUTPUT FORMAT:
You must output a valid JSON object with the following keys:
- "new_fill_content": (string or null) The full text of the updated/generated Fill chapter. ONLY include this if you have generated or edited the story content. If you are just chatting, set this to null.
- "chat_response": (string) Your conversational reply to the user.

Example JSON:
{{
  "new_fill_content": "The door slammed shut...",
  "chat_response": "Here is a draft of the transition scene. I focused on the urgency of the moment."
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
    target_chapter_num: Optional[int] = None,
    old_next_chapter_num: Optional[int] = None,
    timeout: int = 3600,
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
        if target_chapter_num is not None:
            prev_chapter = target_chapter_num - 1 if target_chapter_num > 1 else None
            is_last_chapter = old_next_chapter_num is None
            
            if prev_chapter and not is_last_chapter:
                instructions = f"The user has just opened the chat for this Fill section. This Fill will become Chapter {target_chapter_num}. \nTASK: 1. Introduce yourself as Plot King. \n2. Acknowledge that you are helping 'bridge' the gap between Chapter {prev_chapter} and Chapter {old_next_chapter_num} (frame it as a creative opportunity). \n3. IMMEDIATELY SUGGEST a specific creative idea or bridge scene. \n4. END WITH A QUESTION (e.g., 'Does that spark an idea?'). Return only JSON."
            elif prev_chapter and is_last_chapter:
                instructions = f"The user has just opened the chat for this Fill section. This Fill will become Chapter {target_chapter_num} (the final chapter so far). \nTASK: 1. Introduce yourself. \n2. ACKNOWLEDGE the events of Chapter {prev_chapter} AND that this is a continuation. \n3. IMMEDIATELY SUGGEST a direction for what comes next. \n4. END WITH A QUESTION. Return only JSON."
            elif not prev_chapter and not is_last_chapter:
                instructions = f"The user has just opened the chat for this Fill section. This Fill will become Chapter {target_chapter_num} (the first chapter). \nTASK: 1. Introduce yourself. \n2. SUGGEST a strong opening hook for the story leading into Chapter {old_next_chapter_num}. \n3. END WITH A QUESTION. Return only JSON."
            else:
                instructions = f"The user has just opened the chat for this Fill section. This Fill will become Chapter {target_chapter_num} (the first and only chapter). \nTASK: 1. Introduce yourself. \n2. SUGGEST a core idea for this chapter that includes a specific ending/boundary (where Chapter 2 would begin). \n3. End by asking if this idea works for them. \n(INTERNAL RULE: Do NOT ask about Chapter 2 in this first message. Only ask about Chapter 2 in FUTURE messages ONLY IF the user proposes a new idea without a clear ending). \n4. Return only JSON."
        else:
            instructions = "The user has just opened the chat for this Fill section. Introduce yourself, acknowledge the context (transitions between Ch X and Ch Y), and ask how you can help bridge the gap. \nTASK IMPROVEMENT: 1. Be proactive. 2. SUGGEST a specific idea immediately. 3. END WITH A QUESTION. Return only JSON."
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
        return {"chat_response": f"Plot King (Filler) stumbled: {e}", "new_fill_content": None}


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
            "chat_response": data.get("chat_response", text),
            "new_fill_content": data.get("new_fill_content", None)
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
                    "chat_response": data.get("chat_response", clean_text),
                    "new_fill_content": data.get("new_fill_content", None)
                }
            except:
                pass
        
        # Absolute fallback: treat as pure response
        return {"chat_response": text, "new_fill_content": None}
