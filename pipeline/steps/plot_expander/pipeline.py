# -*- coding: utf-8 -*-
# pipeline/steps/plot_expander/pipeline.py
from pipeline.context import PipelineContext
from .llm import call_llm_expand_plot

def run_plot_expander(context: PipelineContext) -> PipelineContext:
    """
    Pipeline step: setează context.expanded_plot folosind LLM-ul.
    (Nu face logging cu timestamp; runner-ul tău deja loghează pasul.)
    """
    if context.expanded_plot is None:
        context.expanded_plot = call_llm_expand_plot(context.plot, context.genre)
    return context
