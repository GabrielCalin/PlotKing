# -*- coding: utf-8 -*-
# pipeline/steps/overview_editor/pipeline.py
from state.pipeline_context import PipelineContext
from .llm import call_llm_edit_overview

def run_overview_editor(
    context: PipelineContext,
    original_overview: str,
    impact_reason: str,
    diff_summary: str,
    edited_section: str = None,
) -> PipelineContext:
    """
    Pipeline step: editează chapters_overview bazat pe impact și diff.
    
    Args:
        edited_section: Numele secțiunii editate (ex: "Chapter 4" sau "Expanded Plot")
    """
    new_chapter_content = None
    chapter_index = None
    
    if edited_section and edited_section.startswith("Chapter "):
        try:
            chapter_index = int(edited_section.split()[1])
            if 1 <= chapter_index <= len(context.chapters_full or []):
                new_chapter_content = context.chapters_full[chapter_index - 1]
        except (ValueError, IndexError):
            pass
    
    context.chapters_overview = call_llm_edit_overview(
        original_overview=original_overview,
        impact_reason=impact_reason,
        diff_summary=diff_summary,
        expanded_plot=context.expanded_plot or "",
        genre=context.genre or "",
        edited_section=edited_section,
        new_chapter_content=new_chapter_content,
        chapter_index=chapter_index,
        num_chapters=context.num_chapters,
    )
    return context

