# -*- coding: utf-8 -*-
# step2_chapter_generator.py

import requests
import textwrap

def generate_chapters(initial_requirements: str,
                      expanded_plot: str,
                      num_chapters: int,
                      genre: str,
                      feedback: str = None,
                      previous_output: str = None,
                      model="mistral",
                      api_url="http://localhost:1234/v1/chat/completions"):
    """
    Generates a structured chapter overview for the story.
    If feedback and previous_output are provided, revises the previous version accordingly.
    """

    # --- CASE 1: REVISION PROMPT (feedback + previous_output provided) ---
    if feedback and previous_output:
        PROMPT_TEMPLATE = textwrap.dedent(f"""
        You are a professional **book structure designer** and narrative planner.

        The user originally provided the following brief concept or requirements for the story:
        \"\"\"{initial_requirements}\"\"\"

        This concept has been expanded into a detailed and authoritative **story summary** below.  
        Use the expanded summary as the **main reference** for your work, while preserving the tone, logic, and themes of the initial requirements.

        ---

        ### Your task
        You previously generated the following **chapter overview draft**, which now needs to be **revised**, not rewritten from scratch:
        \"\"\"{previous_output}\"\"\"

        The reviewer provided the following feedback:
        \"\"\"{feedback}\"\"\"

        **Revise and improve** the existing chapter overview by applying the feedback with minimal necessary changes.
        - The **exact number of chapters ({num_chapters}) must remain unchanged** — do not change the nunber of chapters under any circumstance.
        - Preserve the **overall structure**, **progression**, and **tone** of the story.
        - Adjust only what is needed to fix logic, flow, clarity, or consistency issues.
        - Keep chapter titles unless the feedback calls for renaming.
        - Output the result in the *exact same Markdown format* as the original instructions require.

        ---

        ### Narrative & structural guidelines
        - **Use Markdown formatting** for clarity and readability.
        - Format each chapter as:

        #### Chapter 1: *<Title>*
        **Description:** <neutral summary of 10–15 sentences>

        - The overall flow of chapters should reflect a **realistic novel structure**:
          1. Only the **first few chapters** (roughly 10–20%) should focus on **Setup / Initial Situation** and **Inciting Conflict**.  
          2. The **majority of chapters** (roughly 60–70%) should center on **Developments / Escalation**, where the tension rises, new events unfold, and stakes increase.  
          3. The final chapters should include the **Climax / Turning Point** and **Resolution / Outcome**, providing a satisfying conclusion consistent with the story arc.

        - Every significant event, character, or development mentioned in the **Expanded Story Summary** must appear in your chapter plan.  
        - If the number of chapters requested ({num_chapters}) requires more material than is present in the expanded plot, you may **creatively elaborate or add bridging content**, as long as it aligns with the tone and genre.
        - Keep tone **neutral, factual, and descriptive**, as this outline will be used later for full novelization.

        ---

        ### Reference materials

        **Expanded Story Summary:**
        \"\"\"{expanded_plot}\"\"\"

        **Genre:**
        \"\"\"{genre}\"\"\"

        ---

        ### Output format
        Return only the **Markdown-formatted list of chapters**, in the exact format shown above.  
        No meta explanations, commentary, or text outside the chapter list.
        """)

    # --- CASE 2: ORIGINAL PROMPT (no feedback / no previous_output) ---
    else:
        PROMPT_TEMPLATE = textwrap.dedent(f"""
        You are a professional **book structure designer** and narrative planner.

        The user originally provided the following brief concept or requirements for the story:
        \"\"\"{initial_requirements}\"\"\"

        This concept has been expanded into a detailed and authoritative **story summary** below.  
        Use the expanded summary as the **main reference** for your work, while preserving the tone, logic, and themes of the initial requirements.

        ---

        ### Your task
        Create exactly **{num_chapters} chapters**, each with:
        - A **catchy, final chapter title** that could be used in a published book (brief, memorable, evocative).
        - A **medium-length factual description** (10–15 sentences) summarizing the key events, actions, and transitions of that chapter.

        ---

        ### Narrative & structural guidelines
        - **Use Markdown formatting** for clarity and readability.
        - Format each chapter as:

        #### Chapter 1: *<Title>*
        **Description:** <neutral summary of 10–15 sentences>

        - The overall flow of chapters should reflect a **realistic novel structure**:
          1. Only the **first few chapters** (roughly 10–20%) should focus on **Setup / Initial Situation** and **Inciting Conflict**.  
          2. The **majority of chapters** (roughly 60–70%) should center on **Developments / Escalation**, where the tension rises, new events unfold, and stakes increase.  
          3. The final chapters should include the **Climax / Turning Point** and **Resolution / Outcome**, providing a satisfying conclusion consistent with the story arc.

        - Every significant event, character, or development mentioned in the **Expanded Story Summary** must appear in your chapter plan.  
        - If the number of chapters requested ({num_chapters}) requires more material than is present in the expanded plot, you are encouraged to **creatively elaborate or add bridging content** — as long as it aligns with the story’s tone, logic, and genre.
        - Keep tone **neutral, factual, and descriptive**, as this outline will be used later for full novelization.

        ---

        ### Reference materials

        **Expanded Story Summary:**
        \"\"\"{expanded_plot}\"\"\"

        **Genre:**
        \"\"\"{genre}\"\"\"

        ---

        ### Output format
        Return only the **Markdown-formatted list of chapters**, in the exact format shown above.  
        No meta explanations, commentary, or text outside the chapter list.
        """)

    # --- API call ---
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": PROMPT_TEMPLATE}],
        "temperature": 0.6,
    }

    try:
        response = requests.post(api_url, json=payload, timeout=300)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error during chapter generation: {e}"
