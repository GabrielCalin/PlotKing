# -*- coding: utf-8 -*-
# pipeline/steps/overview_generator/pipeline.py
from typing import Optional
from state.pipeline_context import PipelineContext
from .llm import call_llm_generate_overview

def run_overview_generator(
    context: PipelineContext,
    *,
    feedback: Optional[str] = None
) -> PipelineContext:
    """
    Pipeline step: setează context.chapters_overview folosind LLM-ul.
    - Dacă există feedback, îl trecem ca revizie, folosind outputul precedent.
    - Respectă context.num_chapters, context.genre etc.
    """
    previous_output = context.chapters_overview if feedback else None

    overview = call_llm_generate_overview(
        initial_requirements=context.plot,
        expanded_plot=context.expanded_plot or "",
        num_chapters=context.num_chapters,
        genre=context.genre,
        feedback=feedback,
        previous_output=previous_output,
    )

    context.chapters_overview = overview
    return context
