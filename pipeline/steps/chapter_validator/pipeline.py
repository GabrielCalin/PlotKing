# -*- coding: utf-8 -*-
# pipeline/steps/chapter_validator/pipeline.py
"""
Wrapper pipeline-friendly pentru validarea unui capitol.
Nu modifică `context`; întoarce (result, details) iar runner-ul decide ce face.
"""

from typing import Tuple
from pipeline.pipeline_context import PipelineContext
from .llm import call_llm_validate_chapter

def run_chapter_validator(
    context: PipelineContext,
    chapter_index: int,
) -> Tuple[str, str]:
    """
    Validează capitolul `chapter_index` (1-based) față de overview + expanded plot + capitolele anterioare.
    """
    current_text = context.chapters_full[chapter_index - 1] if 0 < chapter_index <= len(context.chapters_full) else ""
    previous = context.chapters_full[:max(0, chapter_index - 1)]

    return call_llm_validate_chapter(
        expanded_plot=context.expanded_plot or "",
        chapters_overview=context.chapters_overview or "",
        previous_chapters=previous,
        current_chapter=current_text or "",
        current_index=chapter_index,
        genre=context.genre or "",
    )
