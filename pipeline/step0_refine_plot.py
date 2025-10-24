# -*- coding: utf-8 -*-
"""
step0_refine_plot.py

Refines and enriches the user's initial plot idea using a local LLM.

Purpose:
- Take the user's short initial plot (if any) and genre.
- Produce a refined and more detailed plot, approximately 3-4x longer than the original,
  but not exceeding 500 words.
- If the input plot is empty, generate an original plot aligned with the genre
  (or free-form if genre is also empty).
"""

import os
import textwrap
import requests


def refine_plot(user_plot: str, genre: str,
                model="mistral",
                api_url="http://localhost:1234/v1/chat/completions"):
    """
    Generates a refined and enriched version of the user-provided plot.

    Args:
        user_plot (str): Original short plot description from the user.
        genre (str): Literary genre (optional).
        model (str): Model name for the local LLM API.
        api_url (str): Endpoint of the local LLM API.

    Returns:
        str: Refined, creative, genre-aligned plot text.
    """

    # --- Choose which scenario to use ---
    if not user_plot.strip() and not genre.strip():
        scenario_desc = (
            "The user provided no plot or genre. "
            "Create a completely new and creative plot of about 10 sentences, of any genre or tone."
        )
    elif not user_plot.strip() and genre.strip():
        scenario_desc = (
            "The user provided no plot, but specified a genre. "
            "Create a completely new and imaginative plot aligned with the genre provided below, "
            "about 10 sentences long."
        )
    elif user_plot.strip() and not genre.strip():
        scenario_desc = (
            "The user provided a plot but no genre. "
            "Refine, expand, and creatively enrich this plot while keeping its core ideas consistent and coherent. "
            "Use your own judgment to choose an appropriate tone, atmosphere, and level of imagination."
        )
    else:
        scenario_desc = (
            "The user provided both a plot and a genre. "
            "Refine and expand the plot while enhancing it with creativity, style, and structure appropriate "
            "to the genre described below."
        )

    PROMPT_TEMPLATE = textwrap.dedent(f"""
    You are an imaginative fiction author and story craftsman, refining and expanding initial plot ideas into richer, more compelling story concepts.

    Task:
    {scenario_desc}

    Guidelines:
    - Maintain the original ideas, tone, and characters if provided.
    - Enrich the narrative with imaginative details, motivations, and scenes.
    - Target a result approximately 3-4x longer than the user's input, but not exceeding 500 words.
    - Never produce less text than the user's original input length.
    - Adapt style and elements to the GENRE if one is given.
    - If no input plot is given, invent a fresh plot with roughly 10 sentences.

    Input plot (if any):
    \"\"\"{user_plot}\"\"\"

    GENRE (if any):
    \"\"\"{genre}\"\"\"

    Output only the refined plot text — no titles, explanations, or commentary.
    """)

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": PROMPT_TEMPLATE}],
        "temperature": 0.8,
        "top_p": 0.9,
        "max_tokens": 1200,
    }

    try:
        response = requests.post(api_url, json=payload, timeout=300)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Error during refinement: {e}"
