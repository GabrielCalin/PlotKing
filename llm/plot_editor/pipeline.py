# -*- coding: utf-8 -*-
# pipeline/steps/plot_editor/pipeline.py
from state.pipeline_context import PipelineContext
from .llm import call_llm_edit_plot

def run_plot_editor(
    context: PipelineContext,
    original_plot: str,
    impact_reason: str,
    diff_summary: str,
    edited_section: str = "",
) -> PipelineContext:
    """
    Pipeline step: editează expanded_plot bazat pe impact și diff.
    """
    context.expanded_plot = call_llm_edit_plot(
        original_plot=original_plot,
        impact_reason=impact_reason,
        diff_summary=diff_summary,
        edited_section=edited_section,
        genre=context.genre or "",
    )
    return context

