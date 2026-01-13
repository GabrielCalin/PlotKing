import textwrap
import json
from utils.json_utils import extract_json_from_response
from provider import provider_manager

_GENERATE_PLOT_FROM_FILL_PROMPT = textwrap.dedent("""\
You are an expert story architect triggered by the first chapter of a new book. You must output only valid JSON.

CONTEXT:
The user has started an empty project and written/generated the FIRST CHAPTER.
Your task is to create the initial "Expanded Plot" blueprint matching this first chapter.

FIRST CHAPTER CONTENT:
\"\"\"{chapter_content}\"\"\"

GENRE: {genre}

Task:
Create a full Markdown Expanded Plot structure including:
1. Title (Invent a creative title for the book based on the chapter content)
2. Key Characters (Extract and describe from chapter)
3. World / Setting Overview (Extract and describe from chapter)
4. Plot Summary
   - Describe the events of this chapter naturally.
   - Do NOT use chapter numbers or references (e.g., avoid "In Chapter 1", just describe the events).
   - Do NOT propose future events or continuations. Stop strictly after the events of this chapter.
   - Do NOT mention "drafts", "fills", or "user edits".
   - The summary should be a standalone narrative of the story so far.

Output Requirements:
- Use standard Markdown headers.
- Output JSON format:
{{
  "is_breaking_change": true,
  "adapted_plot": "the complete Expanded Plot markdown"
}}
""").strip()

def call_llm_generate_plot_from_fill(
    chapter_content: str,
    genre: str = "",
    timeout: int = 300,
) -> str:
    """
    Generate the initial Expanded Plot from the first chapter fill.
    """
    prompt = _GENERATE_PLOT_FROM_FILL_PROMPT.format(
        chapter_content=chapter_content or "",
        genre=genre or "unspecified",
    )

    messages = [
        {"role": "system", "content": "You are an expert story architect. You must output only valid JSON."},
        {"role": "user", "content": prompt},
    ]

    try:
        content = provider_manager.get_llm_response(
            task_name="plot_generator_from_fill",
            messages=messages,
            timeout=timeout,
            temperature=0.7,
            top_p=0.95,
            max_tokens=4096
        )
        
        result = extract_json_from_response(content)
        return result.get("adapted_plot", content)
    except Exception as e:
        return f"Error during plot generation from fill: {e}"
