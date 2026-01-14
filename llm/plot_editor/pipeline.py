# -*- coding: utf-8 -*-
# pipeline/steps/plot_editor/pipeline.py
from state.pipeline_context import PipelineContext
from .llm import call_llm_edit_plot
from llm.plot_generator_from_fill.llm import call_llm_generate_plot_from_fill
from state.drafts_manager import DraftsManager

def run_plot_editor(
    context: PipelineContext,
    original_plot: str,
    impact_reason: str,
    diff_summary: str,
    edited_section: str = "",
    fill_name: str = None,
) -> PipelineContext:
    """
    Pipeline step: editează expanded_plot bazat pe impact și diff.
    """
    existing_count = len(context.chapters_full or [])
    
    # Check if we are in the "First Chapter" scenario
    # Logic: We have 0 chapters (in context/checkpoint) AND we are adding a fill context.
    # Note: If fill_name is present, it means we are processing an infill.
    
    if fill_name and existing_count == 0:
        # Get content of the fill
        dm = DraftsManager()
        chapter_content = dm.get_content(fill_name)
        
        # We pass original_plot so the LLM can try to preserve it if it exists
        context.expanded_plot = call_llm_generate_plot_from_fill(
            chapter_content=chapter_content,
            original_plot=original_plot or "",
            genre=context.genre or "",
        )
    else:
        context.expanded_plot = call_llm_edit_plot(
            original_plot=original_plot,
            impact_reason=impact_reason,
            diff_summary=diff_summary,
            edited_section=edited_section,
            genre=context.genre or "",
        )
        
    return context

