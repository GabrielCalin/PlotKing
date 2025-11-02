# pipeline/steps/refine_plot/llm.py
import textwrap
import requests

def refine_plot(user_plot: str, genre: str,
                model="mistral",
                api_url="http://localhost:1234/v1/chat/completions"):
    """
    Generates a refined and enriched version of the user-provided plot.
    UI-only helper. Not part of the pipeline runner.
    """

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
    You are an imaginative fiction author and narrative designer who refines and expands raw story ideas into structured, engaging plot summaries.

    Task:
    {scenario_desc}

    Guidelines:
    - Produce a **plot description**, not a story.
    - Maintain the user's ideas, tone, and characters if provided.
    - Use a factual, summarizing tone — describe what happens, not how it feels.
    - Avoid dialogue, emotions, metaphors, or artistic phrasing.
    - Include cause–effect logic and a 4-part structure (Setup, Inciting Incident, Developments, Resolution).
    - Target 3–4× the input length, max ~500 words. If no plot is given, invent ~10 concise sentences.
    - Adapt tone/pacing to the GENRE if given.

    Input plot:
    \"\"\"{user_plot}\"\"\"

    GENRE:
    \"\"\"{genre}\"\"\"

    Output only the refined plot summary.
    """)

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": PROMPT_TEMPLATE}],
        "temperature": 0.8,
        "top_p": 0.9,
        "max_tokens": 1200,
    }

    try:
        resp = requests.post(api_url, json=payload, timeout=300)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Error during refinement: {e}"
