# -*- coding: utf-8 -*-
# pipeline/steps/chapter_editor/pipeline.py
"""
Wrapper pipeline-friendly pentru editarea unui capitol bazat pe impact și diff.
"""

from typing import List
from state.pipeline_context import PipelineContext
from .llm import call_llm_edit_chapter

def run_chapter_editor(
    context: PipelineContext,
    chapter_index: int,
    original_chapter: str,
    impact_reason: str,
    diff_summary: str,
    edited_section: str = "",
) -> str:
    """
    Returnează textul capitolului editat, fără efecte secundare asupra contextului.
    - chapter_index este 1-based
    """
    previous_chapters: List[str] = []
    if chapter_index > 1:
        previous_chapters = context.chapters_full[:chapter_index - 1]

    return call_llm_edit_chapter(
        expanded_plot=context.expanded_plot or "",
        chapters_overview=context.chapters_overview or "",
        chapter_index=chapter_index,
        previous_chapters=previous_chapters,
        original_chapter=original_chapter,
        impact_reason=impact_reason,
        diff_summary=diff_summary,
        edited_section=edited_section,
        genre=context.genre or "",
        anpc=context.anpc,
    )

