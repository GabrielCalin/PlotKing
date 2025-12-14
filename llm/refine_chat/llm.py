# -*- coding: utf-8 -*-
# llm/refine_chat/llm.py

import textwrap
from typing import List, Dict
from provider import provider_manager


def refine_chat(
    original_plot: str,
    genre: str,
    chat_history: List[Dict[str, str]],
    *,
    timeout: int = 120,
) -> str:
    """
    Generates a refined plot based on the original plot, genre, and the chat conversation with Plot King.
    """

    system_prompt = textwrap.dedent("""
    You are an expert narrative architect.
    Your task is to synthesize a "Refined Plot" by combining:
    1. The User's Original Plot (if available).
    2. The User's chosen Genre.
    3. The details, ideas, and decisions discussed in a chat conversation between the User and "Plot King" (an AI assistant).

    Guidelines:
    - The output must be a cohesive, well-structured plot summary (Setup, Inciting Incident, Rising Action, Climax, Resolution).
    - INCORPORATE ALL DETAILS agreed upon in the chat, regardless of how long the response becomes. Completeness is more important than brevity.
    - DO NOT include ideas that the user explicitly rejected or disliked in the chat.
    - If not all details have been established in the plot or chat, expand and fill the gaps creatively to create a complete, coherent narrative.    
    - If the chat introduced new characters, settings, or plot twists, ensure they are integrated naturally.
    - The tone should match the specified genre.
    - Write in a clear, third-person summary style.
    - Do NOT write it as a chat transcript or a dialogue. Write it as a story summary.
                                    
    Output solely the Refined Plot to be used as the blueprint for writing the novel.
    """).strip()

    # Format chat history for context
    formatted_history = ""
    for msg in chat_history:
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "")
        formatted_history += f"{role}: {content}\n"

    user_prompt = textwrap.dedent(f"""
    ORIGINAL PLOT:
    {original_plot if original_plot else "Not provided"}

    GENRE:
    {genre if genre else "Not provided"}

    CHAT HISTORY:
    {formatted_history}

    Please generate the Refined Plot now.
    """).strip()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        content = provider_manager.get_llm_response(
            task_name="refine_chat",
            messages=messages,
            timeout=timeout,
            temperature=0.7,
            max_tokens=8000
        )
        return content

    except Exception as e:
        return f"Error gathering the court scribes for refinement: {e}"
