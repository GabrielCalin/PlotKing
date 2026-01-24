# -*- coding: utf-8 -*-
# pipeline/steps/chapter_writer/pipeline.py
"""
Wrapper pipeline-friendly pentru scriere/revizie capitol.
Nu face logging și, by design, **NU** modifică `context.chapters_full` — returnează textul,
iar runner-ul decide cum îl inserează/înlocuiește.
"""

from typing import Optional, List, Dict, Any
from state.pipeline_context import PipelineContext
from .llm import call_llm_generate_chapter, call_llm_revise_chapter

def run_chapter_writer(
    context: PipelineContext,
    chapter_index: int,
    *,
    chapter_description: Optional[str] = None,
    transition: Optional[Dict[str, Any]] = None,
    feedback: Optional[str] = None,
    previous_output: Optional[str] = None,
) -> str:
    """
    Returnează textul capitolului (nou sau revizuit), fără efecte secundare asupra contextului.
    - chapter_index este 1-based (conform prompturilor existente).
    - chapter_description: if provided, uses this specific description instead of full overview.
    - transition: if provided, includes transition contract for continuity guidance.
    - dacă `feedback` și `previous_output` sunt date => revizie; altfel generație nouă.
    """
    prev_list: List[str] = context.chapters_full[:-1] if context.chapters_full else []

    if feedback and previous_output:
        return call_llm_revise_chapter(
            expanded_plot=context.expanded_plot or "",
            chapters_overview=context.chapters_overview or "",
            chapter_index=chapter_index,
            previous_chapters=prev_list,
            previous_output=previous_output,
            feedback=feedback,
            chapter_description=chapter_description,
            transition=transition,
            genre=context.genre,
            anpc=context.anpc,
        )

    return call_llm_generate_chapter(
        expanded_plot=context.expanded_plot or "",
        chapters_overview=context.chapters_overview or "",
        chapter_index=chapter_index,
        previous_chapters=prev_list,
        chapter_description=chapter_description,
        transition=transition,
        genre=context.genre,
        anpc=context.anpc,
    )
