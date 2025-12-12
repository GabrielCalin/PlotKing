# -*- coding: utf-8 -*-
# pipeline/steps/overview_generator/llm.py
import textwrap
from typing import Optional
from provider import provider_manager


def call_llm_generate_overview(
    initial_requirements: str,
    expanded_plot: str,
    num_chapters: int,
    genre: str,
    *,
    feedback: Optional[str] = None,
    previous_output: Optional[str] = None,
    model: str = "mistral",
    api_url: str = "http://localhost:1234/v1/chat/completions",
    temperature: float = 0.6,
    max_tokens: int = 4096,
) -> str:
    """
    LLM-only: generează sau revizuiește overview-ul pe capitole.
    Nu are dependențe de contextul pipeline-ului.
    """

    # --- Prompt: revision vs. original ---
    if feedback and previous_output:
        prompt = textwrap.dedent(f"""
        You are a professional **book structure designer** and narrative planner.

        The user originally provided the following brief concept or requirements for the story:
        \"\"\"{initial_requirements}\"\"\"

        This concept has been expanded into a detailed and authoritative **story summary** below.
        Use the expanded summary as the **main reference**, preserving tone, logic, and themes.

        ---

        ### Your task
        You previously generated the following **chapter overview draft**, which now needs to be **revised**, not rewritten from scratch:
        \"\"\"{previous_output}\"\"\"\n
        The reviewer provided the following feedback:
        \"\"\"{feedback}\"\"\"\n
        **Revise and improve** the existing chapter overview by applying the feedback with minimal necessary changes.
        - The **exact number of chapters ({num_chapters}) must remain unchanged** — do not change it.
        - Preserve the **overall structure**, **progression**, and **tone**.
        - Adjust only what is needed to fix logic, flow, clarity, or consistency.
        - Keep chapter titles unless the feedback calls for renaming.
        - Output must follow the exact format described below.

        ---

        ### Narrative & structural guidelines
        - **Use Markdown formatting**.
        - Format each chapter as:

        #### Chapter 1: *<Title>*
        **Description:** <neutral summary of 10–15 sentences>

        - Realistic novel arc:
          1) 10–20% Setup/Inciting
          2) 60–70% Developments/Escalation
          3) Climax + Resolution at the end
        - All key elements from the **Expanded Story Summary** must appear.
        - You may **creatively add bridges** if needed, aligned with tone/genre.
        - Keep tone **neutral, factual, descriptive**.

        ---

        ### Reference materials
        **Expanded Story Summary:**
        \"\"\"{expanded_plot}\"\"\"\n
        **Genre:**
        \"\"\"{genre}\"\"\"\n

        ---

        ### Output format
        Return only the **Markdown-formatted list of chapters**, in the exact format above.
        No commentary outside the chapter list.
        """)
    else:
        prompt = textwrap.dedent(f"""
        You are a professional **book structure designer** and narrative planner.

        The user originally provided the following brief concept or requirements for the story:
        \"\"\"{initial_requirements}\"\"\"\n
        This concept has been expanded into a detailed and authoritative **story summary** below.
        Use the expanded summary as the **main reference**, preserving tone, logic, and themes.

        ---

        ### Your task
        Create exactly **{num_chapters} chapters**, each with:
        - A **final, catchy chapter title**.
        - A **medium-length factual description** (10–15 sentences) of key events, actions, and transitions.

        ---

        ### Narrative & structural guidelines
        - **Use Markdown formatting**.
        - Format each chapter as:

        #### Chapter 1: *<Title>*
        **Description:** <neutral summary of 10–15 sentences>

        - Realistic novel arc:
          1) 10–20% Setup/Inciting
          2) 60–70% Developments/Escalation
          3) Climax + Resolution at the end
        - Include all significant elements from the **Expanded Story Summary**.
        - If {num_chapters} requires more material, **add bridging content** aligned with tone/genre.
        - Tone **neutral, factual, descriptive**.

        ---

        ### Reference materials
        **Expanded Story Summary:**
        \"\"\"{expanded_plot}\"\"\"\n
        **Genre:**
        \"\"\"{genre}\"\"\"\n

        ---

        ### Output format
        Return only the **Markdown-formatted list of chapters**, exactly as above.
        No extra commentary.
        """)


    messages = [{"role": "user", "content": prompt}]
    
    try:
        content = provider_manager.get_llm_response(
            task_name="overview_generator",
            messages=messages,
            timeout=300,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return content
    except Exception as e:
        return f"Error during chapter generation: {e}"

