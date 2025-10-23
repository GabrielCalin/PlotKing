# -*- coding: utf-8 -*-
# step2_chapter_generator.py
import requests
import textwrap

def generate_chapters(initial_requirements: str, expanded_plot: str, num_chapters: int, model="mistral", api_url="http://localhost:1234/v1/chat/completions"):
    PROMPT_TEMPLATE = textwrap.dedent(f"""
    You are a professional book structure designer.

    The user originally provided the following brief concept or requirements for the story:
    \"\"\"{initial_requirements}\"\"\"

    This idea has been expanded into a detailed and authoritative story summary below.
    Use the expanded summary as the **main reference** for your work, but also keep in mind
    the intent and themes suggested in the initial requirements.

    Your task:
    - Create exactly {num_chapters} chapter titles and medium-length descriptions.
    - Each description should summarize what happens in that chapter, focusing on key events or turning points.
    - Keep the tone neutral and factual (not artistic or emotional).
    - Output as a numbered list in the following format:

    Chapter 1: <Title>
    Description: <10-15 sentences>

    EXPANDED STORY SUMMARY:
    \"\"\"{expanded_plot}\"\"\"
    """)

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": PROMPT_TEMPLATE}],
        "temperature": 0.6,
    }

    response = requests.post(api_url, json=payload, timeout=300)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
