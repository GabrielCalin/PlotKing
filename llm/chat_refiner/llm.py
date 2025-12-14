# -*- coding: utf-8 -*-
# llm/chat_refiner/llm.py

import textwrap
from typing import List, Optional, Dict, Any
from provider import provider_manager


# ---------------------------------------
# PLOT KING SYSTEM PROMPT
# ---------------------------------------
_PLOT_KING_SYSTEM_PROMPT = textwrap.dedent("""
You are "Plot King", a creative, proactive, and helpful AI writing assistant.
Your goal is to help the user refine and expand their story idea (plot) and genre into a detailed and structured narrative plan.

Personality:
- Creative, enthusiastic, and encouraging.
- Proactive: always end your messages with a question or a suggestion to move the conversation forward.

Role:
- Review the User's Original Plot and Genre (if provided).
- Discuss details to check for gaps (setting, characters, conflict, tone, etc.).
- Suggest ideas if the user is stuck or has a brief plot.
- If the user asks you to "Refine Plot" or "Create Refined Plot", tell them to press the "Refine" button in the UI.

IMPORTANT:
- Keep your responses conversational and engaging.
- Do NOT output JSON. Output only the plain text of your reply.
- Verify details about the world (time, place, geography, culture), characters (roles, interactions), and plot progression.
""").strip()


def call_llm_chat(
    original_plot: str,
    genre: str,
    chat_history: List[Dict[str, str]],
    user_message: str,
    *,
    timeout: int = 60,
) -> str:
    """
    Calls the LLM as Plot King to chat with the user.
    """

    # 1. Construct the system context
    system_context = _PLOT_KING_SYSTEM_PROMPT
    
    # 2. Build the messages list
    messages = [
        {"role": "system", "content": system_context},
        {"role": "assistant", "content": f"CONTEXT - Original Plot: {original_plot}\nGenre: {genre}"}
    ]

    # 3. Append history
    # Converting internal chat format if needed, but assuming standard dict structure
    for msg in chat_history:
        # ensuring we only pass valid roles
        role = msg.get("role", "user")
        content = msg.get("content", "")
        messages.append({"role": role, "content": content})

    # 4. Append current user message (if not empty/trigger)
    # If user_message is a special trigger (like empty for initial greeting), handle logic below or let LLM infer
    # But usually the UI calls this with specific user input.
    # Logic for initial greeting is handled better by a separate check or a specific prompter if 'user_message' is empty?
    # User requirement: "incet de la intrarea pe modul chat sau la apasarea clear, mesajul initial va fi produs tot de LLM"
    # So if chat_history is empty and user_message is special (e.g. "START_SESSION"), we prompt for greeting.
    
    if user_message == "START_SESSION" and not chat_history:
        # Prompt for the initial greeting
        prompt_for_greeting = ""
        if original_plot and genre:
            prompt_for_greeting = "The user has provided a plot and a genre. Introduce yourself as Plot King and offer to help detail it."
        elif original_plot:
            prompt_for_greeting = "The user has provided a plot but no genre. Introduce yourself as Plot King and offer to help detail it."
        elif genre:
            prompt_for_greeting = "The user has provided a genre but no plot. Introduce yourself as Plot King and offer to help create a plot together in the provided genre."
        else:
            prompt_for_greeting = " The user has provided neither plot nor genre. Introduce yourself as Plot King and suggest we define a plot together."
        
        messages.append({"role": "user", "content": f"[SYSTEM INSTRUCTION]: {prompt_for_greeting}"})
    else:
        messages.append({"role": "user", "content": user_message})

    try:
        content = provider_manager.get_llm_response(
            task_name="chat_refiner",
            messages=messages,
            timeout=timeout,
            temperature=0.8,
            max_tokens=2000
        )
        return content

    except Exception as e:
        return f"Plot King is having a coffee break. Error: {e}"
