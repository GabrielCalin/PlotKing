# -*- coding: utf-8 -*-
# pipeline/steps/overview_validator/pipeline.py
from typing import Tuple, Optional
from state.pipeline_context import PipelineContext
from .llm import call_llm_validate_overview

def run_overview_validator(context: PipelineContext) -> Tuple[str, Optional[str]]:
    """
    Pipeline-friendly wrapper around the LLM validator.
    Does not mutate context yet (păstrăm runner-ul ca sursă de adevăr pentru logging/flags).
    Returns the (result, feedback) tuple so runner-ul poate decide ce face.
    """
    return call_llm_validate_overview(
        initial_plot=context.plot,
        expanded_plot=context.expanded_plot or "",
        chapters=context.chapters_overview or "",
        genre=context.genre or "",
    )
