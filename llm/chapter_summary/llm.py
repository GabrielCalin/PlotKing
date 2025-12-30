# -*- coding: utf-8 -*-
# llm/chapter_summary/llm.py
"""
LLM helper pentru generarea unui rezumat al unui capitol (fill draft).
"""

import textwrap
from typing import Optional
from provider import provider_manager


def call_llm_chapter_summary(
    chapter_content: str,
    *,
    api_url: str = None,
    model_name: str = None,
    timeout: int = 300,
) -> str:
    """
    Generează un rezumat al unui capitol (fill draft) similar cu descrierea dintr-un chapter overview.
    
    Args:
        chapter_content: Conținutul capitolului de rezumat
        api_url: URL-ul API (opțional, folosește default din settings)
        model_name: Numele modelului (opțional, folosește default din settings)
        timeout: Timeout în secunde
    
    Returns:
        Rezumatul capitolului (10-15 propoziții) sau mesaj de eroare
    """
    
    prompt = textwrap.dedent(f"""\
You are a professional book structure designer and narrative planner.

### Your task
Create a factual, neutral summary of the following chapter content. The summary should be similar in style and length to a chapter overview description (10-15 sentences).

**Chapter Content:**
\"\"\"{chapter_content}\"\"\"

### Guidelines
- Write a **neutral, factual, descriptive** summary of 10-15 sentences
- Focus on key events, actions, character developments, and narrative transitions
- **DO NOT invent or add information** that is not present in the content
- If the content is shorter and you cannot reach 10-15 sentences, write a shorter summary but **never invent content**
- Use clear, professional language appropriate for a chapter overview

### Output format
Return only the summary text, without any additional formatting, titles, or commentary.
""").strip()

    messages = [
        {"role": "system", "content": "You are a precise narrative summarizer that creates factual chapter overviews based strictly on provided content."},
        {"role": "user", "content": prompt},
    ]

    try:
        content = provider_manager.get_llm_response(
            task_name="chapter_summary",
            messages=messages,
            timeout=timeout,
            temperature=0.3,
            top_p=0.9,
            max_tokens=2000
        )
        return content.strip()
    except Exception as e:
        return f"Error during chapter summary generation: {e}"

