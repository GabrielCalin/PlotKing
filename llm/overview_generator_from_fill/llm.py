import textwrap
from provider import provider_manager

_GENERATE_OVERVIEW_FROM_FILL_PROMPT = textwrap.dedent("""\
You are a story architect organizing the chapters of a new book based on its FIRST chapter. Output valid Markdown only.

CONTEXT:
The user has just written/generated the FIRST CHAPTER (Infill) for a new project.
Your task is to create the initial "Chapters Overview" containing ONLY this first chapter.

NEW CHAPTER CONTENT:
\"\"\"{chapter_content}\"\"\"

EXISTING OVERVIEW (Optional - may be empty):
\"\"\"{original_overview}\"\"\"

GENRE: {genre}

Task:
Create the Chapters Overview.
1. Include ONLY "Chapter 1".
2. Create a "Title" for Chapter 1 based on its content.
3. Write a "Description" for Chapter 1 that strictly summarizes the events in the content provided (10-15 sentences).
4. Do NOT include placeholders for Chapter 2, 3, etc.
5. Do NOT suggest future plot points.
6. Do NOT mention "drafts" or "fills".
7. If EXISTING OVERVIEW contains valid notes or context for Chapter 1 that doesn't contradict the new content, you may incorporate it.
8. PRIORITY: The NEW CHAPTER CONTENT is the source of truth for Chapter 1.

Output Requirements:
- Output ONLY the Markdown content. Do not wrap in JSON.
- Markdown format:
  #### Chapter 1: [Chapter Title]
  **Description:** [Summary of events]
""").strip()

def call_llm_generate_overview_from_fill(
    chapter_content: str,
    original_overview: str = "",
    genre: str = "",
    timeout: int = 300,
) -> str:
    """
    Generate the initial Chapters Overview from the first chapter fill.
    """
    prompt = _GENERATE_OVERVIEW_FROM_FILL_PROMPT.format(
        chapter_content=chapter_content or "",
        original_overview=original_overview or "",
        genre=genre or "unspecified",
    )

    messages = [
        {"role": "system", "content": "You are a story architect. Output valid Markdown only."},
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
        
        return content
    except Exception as e:
        return f"Error during overview generation from fill: {e}"
