# -*- coding: utf-8 -*-
# pipeline/steps/overview_editor/pipeline.py
from state.pipeline_context import PipelineContext
from state.drafts_manager import DraftsManager, DraftType
from state.infill_manager import InfillManager
from .llm import call_llm_edit_overview
from llm.overview_generator_from_fill.llm import call_llm_generate_overview_from_fill

def run_overview_editor(
    context: PipelineContext,
    original_overview: str,
    impact_reason: str,
    diff_summary: str,
    edited_section: str = None,
    fill_name: str = None,
) -> PipelineContext:
    """
    Pipeline step: editează chapters_overview bazat pe impact și diff.
    
    Args:
        edited_section: Numele secțiunii editate (ex: "Chapter 4" sau "Expanded Plot" sau "Chapter 2 (Candidate)")
        fill_name: Numele fill-ului original dacă este infill (ex: "Fill 2 (#1)")
    """
    new_chapter_content = None
    chapter_index = None
    is_infill = fill_name is not None
    
    drafts_mgr = DraftsManager()
    
    if is_infill:
        im = InfillManager()
        if fill_name:
            chapter_index = im.parse_fill_target(fill_name)
            new_chapter_content = drafts_mgr.get_content(fill_name)
    elif edited_section and edited_section.startswith("Chapter "):
        try:
            chapter_index = int(edited_section.split()[1])
            new_chapter_content = drafts_mgr.get_content(edited_section)
            if new_chapter_content is None:
                if 1 <= chapter_index <= len(context.chapters_full or []):
                    new_chapter_content = context.chapters_full[chapter_index - 1]
        except (ValueError, IndexError):
            pass

    total_chapters = len(context.chapters_full or [])

    if is_infill:
        num_chapters = total_chapters + 1
    else:
        num_chapters = context.num_chapters
    
    
    # Check Special Case: First Chapter (Fill) on Empty Project (or Project with 0 chapters)
    if is_infill and total_chapters == 0 and new_chapter_content:
        context.chapters_overview = call_llm_generate_overview_from_fill(
            chapter_content=new_chapter_content,
            original_overview=original_overview or "",
            genre=context.genre or "",
        )
    else:
        context.chapters_overview = call_llm_edit_overview(
            original_overview=original_overview,
            impact_reason=impact_reason,
            diff_summary=diff_summary,
            expanded_plot=context.expanded_plot or "",
            genre=context.genre or "",
            edited_section=edited_section,
            new_chapter_content=new_chapter_content,
            chapter_index=chapter_index,
            num_chapters=num_chapters,
            is_infill=is_infill,
        )
    return context

