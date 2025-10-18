# -*- coding: utf-8 -*-
import requests
import os
import textwrap

API_URL = os.getenv("LMSTUDIO_API_URL", "http://localhost:1234/v1/chat/completions")
MODEL_NAME = os.getenv("LMSTUDIO_MODEL", "local-model")

def generate_chapter(expanded_plot, chapters_overview, previous_chapters, current_index):
    """Generate a full chapter iteratively, using the LM Studio local model."""
    current_title = chapters_overview.splitlines()[current_index].strip()
    context_previous = "\n\n".join([f"Chapter {i+1}: {ch[:400]}..." for i, ch in enumerate(previous_chapters)]) if previous_chapters else "None"
    
    prompt = textwrap.dedent(f"""
    You are a professional novelist AI. You are now writing the chapter **{current_index+1}** of a novel.

    Full expanded plot:
    {expanded_plot}

    Chapter outline list:
    {chapters_overview}

    Chapters already written:
    {context_previous}

    Your task:
    - Write the complete text of chapter {current_index+1}: "{current_title}".
    - Use a neutral, descriptive narrative style (no fancy metaphors or heavy emotion).
    - Keep it clear, coherent, and around 5–10 pages (roughly 2500–5000 words).
    - Make sure it logically follows from the previous chapters and fits the global plot.
    - Finish the chapter naturally, not mid-scene.

    Start directly with the story text.
    """)

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are an expert long-form fiction generator."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.8,
        "max_tokens": 6000,
    }

    try:
        response = requests.post(API_URL, json=payload, timeout=600)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return content.strip()
    except Exception as e:
        return f"Error during chapter generation: {e}"
