# step1_plot_expander.py
import requests
import textwrap
import os

def expand_plot(user_plot: str, genre: str, model="mistral", api_url="http://localhost:1234/v1/chat/completions"):
    PROMPT_TEMPLATE = textwrap.dedent(f"""
    You are an expert story planner and narrative designer.

    Task:
    Expand and detail the following short plot idea provided by the USER into a **structured Markdown story blueprint** of about two pages (approximately 1500–2000 words).
    The result must describe **what happens in the story — scene by scene —** in a clear, factual, and objective tone, as if outlining the events and motivations for later novelization.
    Avoid artistic phrasing, dialogue, metaphors, or emotional embellishment. Write as a neutral narrator describing the logical progression of events.

    Your output must include the following **four Markdown sections**, in this exact order:

    ### 1. Title
    - Write a concise, evocative **book title** (invent one if not provided).

    ### 2. Key Characters
    - List **1–5 important characters**, each with a **short 1–2 sentence description** explaining their role, traits, or motivation.
    - Focus on those essential to the story’s main conflict or resolution.

    ### 3. World / Setting Overview
    - Briefly describe the **universe, world, or setting** where the story takes place.
    - Mention relevant details about time period, society, geography, technology, politics, or atmosphere that influence the events.

    ### 4. Plot Summary
    - Present the full plot here, written in **factual paragraphs** (not bullet points or numbered lists).
    - Follow a clear, logical **five-part structure**:

    1. **Setup / Initial Situation** — establish the main characters, their world, and normal life before the story begins.  
    2. **Inciting Incident / Conflict** — describe the key event that disrupts the normal world and sets the main story in motion.  
    3. **Developments / Escalation** — show how the situation grows more complex through actions, discoveries, or confrontations.  
    4. **Climax / Turning Point** — detail the decisive confrontation or critical event where the story reaches maximum tension and irreversible change.  
    5. **Resolution / Outcome** — explain how the conflict concludes, what consequences follow, and what lasting changes result.

    - Each paragraph should explain **what happens, where, and why it matters**.
    - Keep tone impersonal and descriptive.
    - Do **not** divide the story into chapters or use dialogue.
    - Maintain clear cause–effect logic throughout.

    Additional Guidelines:
    - Maintain the user's main concept, tone, and characters as much as possible.
    - Adapt structure, pacing, and tone to the specified **GENRE**.
    - The total text should be **1500–2000 words**, or proportional to the input length if the user’s text already exceeds this range.
    - Always ensure the output is at least as detailed as the input.

    USER PLOT:
    \"\"\"{user_plot}\"\"\"

    GENRE:
    \"\"\"{genre}\"\"\"

    Output only the Markdown document with the four sections above — no extra commentary or explanations.
    """)

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": PROMPT_TEMPLATE}],
        "temperature": 0.7,
    }

    response = requests.post(api_url, json=payload, timeout=300)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
