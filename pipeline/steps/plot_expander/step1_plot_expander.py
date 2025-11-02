# step1_plot_expander.py
import requests
import textwrap
import os

def expand_plot(user_plot: str, genre: str, model="mistral", api_url="http://localhost:1234/v1/chat/completions"):
    PROMPT_TEMPLATE = textwrap.dedent(f"""
    You are an expert **story planner and narrative designer** specialized in turning short ideas into rich, novel-length blueprints.

    Task:
    Expand and elaborate the following short plot idea from the USER into a **structured Markdown story blueprint** of about 5 pages (approximately 1500–2000 words).
    The result must describe **what happens in the story — scene by scene —** in a clear, factual, and objective tone, as if outlining the events and motivations for later novelization.
    Avoid artistic phrasing, dialogue, or metaphorical writing. Use a neutral, descriptive voice focused on cause and effect.

    Creativity expectations:
    - Preserve the **core premise and main characters** of the user's plot, but expand it substantially.  
    - Add **new events, subplots, and connecting sequences** that make the story coherent and long enough for a novel.  
    - It is encouraged to **create logical “in-between” scenes** that connect the user’s original ideas smoothly, deepening motivations, relationships, and world context.  
    - All creative additions must fit naturally within the genre and the logic of the story.

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

      1. **Setup / Initial Situation** — establish the main characters, their world, and their normal life before the story begins.  
      2. **Inciting Incident / Conflict** — describe the key event that disrupts the normal world and sets the story in motion.  
      3. **Developments / Escalation** — this section should be the most detailed and extensive part of the story.  
         - Expand it with multiple interrelated developments, rising tensions, discoveries, setbacks, and interactions between characters.  
         - Introduce side plots or secondary conflicts that enrich the middle of the novel and deepen character arcs.  
         - Maintain a clear sense of progression toward the climax.  
      4. **Climax / Turning Point** — describe the decisive confrontation or moment of irreversible change.  
      5. **Resolution / Outcome** — explain how the conflict concludes, what consequences follow, and what lasting changes result.

    - Each paragraph should explain **what happens, where, and why it matters**.
    - Keep the tone factual, neutral, and structured — this is a blueprint, not prose.
    - Do **not** divide the story into chapters or use dialogue.
    - Maintain strict cause–effect logic throughout.

    Additional Guidelines:
    - Maintain the user's main concept, tone, and characters as much as possible.
    - Adapt structure, pacing, and tone to the specified **GENRE**.
    - The total text should be **1500–2000 words**, or proportional to the input length if the user's text already exceeds this range.
    - Always ensure the output is at least as detailed as the input.
    - Emphasize rich, creative expansion inside the **Developments** phase while keeping coherence with the **original plot** and **global logic**.

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
