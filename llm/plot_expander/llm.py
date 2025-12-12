# -*- coding: utf-8 -*-
# pipeline/steps/plot_expander/llm.py
import textwrap
from provider import provider_manager


def call_llm_expand_plot(
    user_plot: str,
    genre: str,
    *,
    model: str = "mistral",
    api_url: str = "http://localhost:1234/v1/chat/completions",
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> str:
    """
    LLM-only: transformă plotul scurt într-un blueprint Markdown (1500–2000 cuvinte).
    Nu are dependențe de contextul pipeline-ului.
    """
    PROMPT_TEMPLATE = textwrap.dedent(f"""
    You are an expert **story planner and narrative designer** specialized in turning short ideas into rich, novel-length blueprints.

    Task:
    Expand and elaborate the following short plot idea from the USER into a **structured Markdown story blueprint** of about 5 pages (approximately 1500–2000 words).
    The result must describe **what happens in the story — scene by scene —** in a clear, factual, and objective tone, as if outlining the events and motivations for later novelization.
    Avoid artistic phrasing, dialogue, or metaphorical writing. Use a neutral, descriptive voice focused on cause and effect.

    Creativity expectations:
    - Preserve the **core premise and main characters** of the user's plot, but expand it substantially.
    - Add **new events, subplots, and connecting sequences** that make the story coherent and long enough for a novel.
    - Create logical “in-between” scenes that connect the user’s original ideas smoothly, deepening motivations, relationships, and world context.
    - All creative additions must fit naturally within the genre and the logic of the story.

    Your output must include the following **four Markdown sections**, in this exact order:

    ### 1. Title
    - Write a concise, evocative **book title** (invent one if not provided).

    ### 2. Key Characters
    - List **1–5 important characters**, each with a **short 1–2 sentence description** explaining their role, traits, or motivation.

    ### 3. World / Setting Overview
    - Briefly describe the **universe, world, or setting** where the story takes place.

    ### 4. Plot Summary
    - Present the full plot here, written in **factual paragraphs** (not bullet points).
    - Follow a clear, logical **five-part structure**:
      1. **Setup / Initial Situation**
      2. **Inciting Incident / Conflict**
      3. **Developments / Escalation** (the most detailed section; include subplots, reversals, discoveries)
      4. **Climax / Turning Point**
      5. **Resolution / Outcome**
    - Each paragraph should explain **what happens, where, and why it matters**.
    - Keep the tone factual, neutral, and structured — this is a blueprint, not prose.
    - Do **not** divide the story into chapters or use dialogue.
    - Maintain strict cause–effect logic throughout.

    Additional Guidelines:
    - Maintain the user's main concept, tone, and characters as much as possible.
    - Adapt structure, pacing, and tone to the specified **GENRE**.
    - The total text should be **1500–2000 words** (or proportional if input already exceeds this).
    - Emphasize rich, creative expansion in the **Developments** phase while keeping coherence with the **original plot** and **global logic**.

    USER PLOT:
    \"\"\"{user_plot}\"\"\"

    GENRE:
    \"\"\"{genre}\"\"\"

    Output only the Markdown document with the four sections above — no extra commentary.
    """)


    messages = [{"role": "user", "content": PROMPT_TEMPLATE}]
    
    try:
        content = provider_manager.get_llm_response(
            task_name="plot_expander",
            messages=messages,
            timeout=300,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return content
    except Exception as e:
        return f"Error during plot expansion: {e}"

