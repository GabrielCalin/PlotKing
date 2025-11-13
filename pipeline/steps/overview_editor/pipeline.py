# -*- coding: utf-8 -*-
# pipeline/steps/overview_editor/pipeline.py
from pipeline.context import PipelineContext
from .llm import call_llm_edit_overview

def run_overview_editor(
    context: PipelineContext,
    original_overview: str,
    impact_reason: str,
    diff_summary: str,
) -> PipelineContext:
    """
    Pipeline step: editează chapters_overview bazat pe impact și diff.
    """
    context.chapters_overview = call_llm_edit_overview(
        original_overview=original_overview,
        impact_reason=impact_reason,
        diff_summary=diff_summary,
        expanded_plot=context.expanded_plot or "",
        genre=context.genre or "",
    )
    return context

