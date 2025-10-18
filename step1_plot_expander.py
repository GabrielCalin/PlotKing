# step1_plot_expander.py
import requests
import textwrap
import os

def expand_plot(user_plot: str, model="mistral", api_url="http://localhost:1234/v1/chat/completions"):
    PROMPT_TEMPLATE = textwrap.dedent(f"""
    You are an expert story planner and narrative designer.

    Task:
    Expand and detail the following short plot idea provided by the USER into a structured, objective plot summary of about two pages (approximately 700–1000 words). 
    The text must describe what happens in the story — scene by scene — in a clear, factual tone, as if outlining the events and motivations for later novelization. 
    Avoid artistic phrasing, dialogue, metaphors, or emotional embellishment. Write as a neutral narrator describing the progression of events.

    Guidelines:
    - Keep the user's main concept, characters, and relationships intact.
    - Structure the plot in three parts: setup, conflict, resolution.
    - Use impersonal, descriptive tone.
    - Each scene should explain what happens, where, and why it matters.
    - End with the final outcome of the story. No meta commentary.

    USER PLOT:
    \"\"\"{user_plot}\"\"\"
    """)

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": PROMPT_TEMPLATE}],
        "temperature": 0.7,
    }

    response = requests.post(api_url, json=payload)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
