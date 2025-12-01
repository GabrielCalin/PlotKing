# pipeline/steps/title_fetcher/llm.py
import os
import requests
import textwrap

LOCAL_API_URL = os.getenv("LMSTUDIO_API_URL", "http://127.0.0.1:1234/v1/chat/completions")
MODEL_NAME = os.getenv("LMSTUDIO_MODEL", "phi-3-mini-4k-instruct")

def fetch_title_llm(expanded_plot: str,
                    api_url: str = None,
                    model_name: str = None,
                    timeout: int = 300) -> str:
    """
    Analyzes the expanded plot to determine or invent a suitable title.
    Returns the title as a plain string.
    """
    url = api_url or LOCAL_API_URL
    model = model_name or MODEL_NAME

    if not expanded_plot or not expanded_plot.strip():
        return "Untitled Story"

    prompt = textwrap.dedent(f"""
    You are a creative editor. Your task is to determine the title of a book based on its plot summary.
    
    Instructions:
    1. Analyze the provided Expanded Plot.
    2. If a title is explicitly mentioned (e.g., "Title: ..."), extract it.
    3. If no title is mentioned, invent a creative and fitting title based on the plot's content, themes, and genre.
    4. Return ONLY the title as plain text. Do not include quotes, "Title:", or any other text.
    
    Expanded Plot:
    \"\"\"{expanded_plot}\"\"\"
    
    Title:
    """).strip()

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that extracts or generates book titles."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 50,
    }

    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        # Cleanup if the model returns quotes or "Title: " prefix despite instructions
        content = content.replace('"', '').replace("Title:", "").strip()
        return content
    except Exception as e:
        return f"Error fetching title: {e}"
