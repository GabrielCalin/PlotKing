import textwrap
from provider import provider_manager

_GENERATE_PLOT_FROM_FILL_PROMPT = textwrap.dedent("""\
You are an expert story architect triggered by the first chapter of a new book. Output valid Markdown only.

CONTEXT:
The user has started a project and written/generated the FIRST CHAPTER.
Your task is to create (or update) the "Expanded Plot" blueprint matching this first chapter.

FIRST CHAPTER CONTENT:
\"\"\"{chapter_content}\"\"\"

EXISTING PLOT (Optional - may be empty):
\"\"\"{original_plot}\"\"\"

GENRE: {genre}

Task:
Create a full Markdown Expanded Plot structure including:
1. Title (Invent a creative title for the book based on the chapter content, OR keep existing if suitable)
2. Key Characters (Extract from chapter. Merge with meaningful details from EXISTING PLOT if they don't contradict the chapter)
3. World / Setting Overview (Extract from chapter. Merge with meaningful details from EXISTING PLOT if they don't contradict the chapter)
4. Plot Summary
   - Describe the events of this chapter naturally.
   - Do NOT use chapter numbers or references (e.g., avoid "In Chapter 1", just describe the events).
   - Do NOT propose future events or continuations. Stop strictly after the events of this chapter.
   - Do NOT mention "drafts", "fills", or "user edits".
   - The summary should be a standalone narrative of the story so far.
   - If EXISTING PLOT contains valid context that precedes or explains the chapter events without contradicting them, you may incorporate it.
   - PRIORITY: The FIRST CHAPTER CONTENT is the absolute source of truth.

Output Requirements:
- Output ONLY the Markdown content. Do not wrap in JSON.
- Use standard Markdown headers.
""").strip()

def call_llm_generate_plot_from_fill(
    chapter_content: str,
    original_plot: str = "",
    genre: str = "",
    timeout: int = 300,
) -> str:
    """
    Generate the initial Expanded Plot from the first chapter fill.
    If original_plot exists, try to preserve compatible details.
    """
    prompt = _GENERATE_PLOT_FROM_FILL_PROMPT.format(
        chapter_content=chapter_content or "",
        original_plot=original_plot or "",
        genre=genre or "unspecified",
    )

    messages = [
        {"role": "system", "content": "You are an expert story architect. Output valid Markdown only."},
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
        
        return content
    except Exception as e:
        return f"Error during plot generation from fill: {e}"
