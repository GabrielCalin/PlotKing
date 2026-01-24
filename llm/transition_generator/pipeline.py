# -*- coding: utf-8 -*-
# llm/transition_generator/pipeline.py

from typing import List, Dict, Any, Tuple
from state.pipeline_context import PipelineContext
from .llm import call_llm_generate_transitions


def run_transition_generator(
    context: PipelineContext,
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Generate transition contracts for all chapters based on the chapters overview.
    
    This function does NOT modify the context - transitions are meant to be used
    as local variables in the runner, not cached in state.
    
    Args:
        context: The pipeline context containing expanded_plot, chapters_overview, and num_chapters
    
    Returns:
        Tuple of (transitions_list, success) where:
        - transitions_list: List of transition dicts, one per chapter (empty if failed)
        - success: True if generation succeeded, False otherwise
    """
    if not context.chapters_overview or not context.expanded_plot:
        return [], False
    
    if not context.num_chapters or context.num_chapters <= 0:
        return [], False
    
    transitions = call_llm_generate_transitions(
        expanded_plot=context.expanded_plot,
        chapters_overview=context.chapters_overview,
        num_chapters=context.num_chapters,
    )
    
    if len(transitions) == context.num_chapters:
        return transitions, True
    
    return [], False


def get_transition_for_chapter(
    transitions: List[Dict[str, Any]],
    chapter_index: int,
) -> Dict[str, Any]:
    """
    Get the transition contract for a specific chapter.
    
    Args:
        transitions: List of all transition dicts
        chapter_index: 1-based chapter index
    
    Returns:
        The transition dict for the chapter, or empty dict if not found
    """
    if not transitions:
        return {}
    
    idx = chapter_index - 1
    if idx < 0 or idx >= len(transitions):
        return {}
    
    return transitions[idx]

