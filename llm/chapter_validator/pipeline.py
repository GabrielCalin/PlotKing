# -*- coding: utf-8 -*-
# pipeline/steps/chapter_validator/pipeline.py
"""
Wrapper pipeline-friendly pentru validarea unui capitol.
Nu modifică `context`; întoarce (result, details) iar runner-ul decide ce face.
"""

from typing import Tuple, Optional, Dict, Any
from state.pipeline_context import PipelineContext
from state.transitions_manager import get_transition_for_chapter
from .llm import call_llm_validate_chapter

def run_chapter_validator(
    context: PipelineContext,
    chapter_index: int,
) -> Tuple[str, str]:
    """
    Validează capitolul `chapter_index` (1-based) față de overview + expanded plot + capitolele anterioare + transition contract.
    """
    current_text = context.chapters_full[chapter_index - 1] if 0 < chapter_index <= len(context.chapters_full) else ""
    previous = context.chapters_full[:max(0, chapter_index - 1)]
    transition = get_transition_for_chapter(chapter_index)

    return call_llm_validate_chapter(
        expanded_plot=context.expanded_plot or "",
        chapters_overview=context.chapters_overview or "",
        previous_chapters=previous,
        current_chapter=current_text or "",
        current_index=chapter_index,
        genre=context.genre or "",
        transition=transition,
    )
