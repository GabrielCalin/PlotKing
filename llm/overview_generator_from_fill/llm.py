import textwrap
import json
from utils.json_utils import extract_json_from_response
from provider import provider_manager

_GENERATE_OVERVIEW_FROM_FILL_PROMPT = textwrap.dedent("""\
You are a story architect organizing the chapters of a new book based on its FIRST chapter. You must output only valid JSON.

CONTEXT:
The user has just written/generated the FIRST CHAPTER (Infill) for a new project.
Your task is to create the initial "Chapters Overview" containing ONLY this first chapter.

NEW CHAPTER CONTENT:
\"\"\"{chapter_content}\"\"\"

GENRE: {genre}

Task:
Create the Chapters Overview.
1. Include ONLY "Chapter 1".
2. Create a "Title" for Chapter 1 based on its content.
3. Write a "Description" for Chapter 1 that strictly summarizes the events in the content provided (10-15 sentences).
4. Do NOT include placeholders for Chapter 2, 3, etc.
5. Do NOT suggest future plot points.
6. Do NOT mention "drafts" or "fills".

Output Requirements:
- Markdown format:
  #### Chapter 1: [Chapter Title]
  **Description:** [Summary of events]
- Output JSON:
{{
  "is_breaking_change": true,
  "adapted_overview": "the complete Chapters Overview markdown"
}}
""").strip()

def call_llm_generate_overview_from_fill(
    chapter_content: str,
    genre: str = "",
    timeout: int = 300,
) -> str:
    """
    Generate the initial Chapters Overview from the first chapter fill.
    """
    prompt = _GENERATE_OVERVIEW_FROM_FILL_PROMPT.format(
        chapter_content=chapter_content or "",
        genre=genre or "unspecified",
    )

    messages = [
        {"role": "system", "content": "You are a story architect. You must output only valid JSON."},
        {"role": "user", "content": prompt},
    ]

    try:
        content = provider_manager.get_llm_response(
            task_name="overview_generator_from_fill",
            messages=messages,
            timeout=timeout,
            temperature=0.6,
            top_p=0.95,
            max_tokens=4000
        )
        
        result = extract_json_from_response(content)
        return result.get("adapted_overview", content)
    except Exception as e:
        return f"Error during overview generation from fill: {e}"
