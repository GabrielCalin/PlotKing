# -*- coding: utf-8 -*-
# llm/overview_tokenizer/pipeline.py

import re
from typing import List, Tuple
from .llm import call_llm_tokenize_overview


def _try_programmatic_split(chapters_overview: str, num_chapters: int) -> Tuple[bool, List[str]]:
    """
    Attempt to split chapters_overview using regex on the chapter heading pattern.
    
    Returns:
        (success, chapters_list) - success is True if exactly num_chapters were found
    """
    pattern = r'(#{1,4}\s*Chapter\s+\d+\s*:\s*\*[^*]+\*)'
    
    splits = re.split(pattern, chapters_overview, flags=re.IGNORECASE)
    
    chapters = []
    i = 1
    while i < len(splits):
        heading = splits[i].strip()
        content = splits[i + 1].strip() if i + 1 < len(splits) else ""
        chapter_text = f"{heading}\n{content}".strip()
        chapters.append(chapter_text)
        i += 2
    
    if len(chapters) == num_chapters:
        return True, chapters
    
    return False, []


def _split_by_line_indices(chapters_overview: str, line_indices: List[int]) -> List[str]:
    """
    Split the overview into chapters based on line indices.
    
    Args:
        chapters_overview: The full overview text
        line_indices: List of 1-based line indices where each chapter starts
    
    Returns:
        List of chapter texts
    """
    lines = chapters_overview.split('\n')
    chapters = []
    
    for i, start_line in enumerate(line_indices):
        start_idx = start_line - 1
        
        if i + 1 < len(line_indices):
            end_idx = line_indices[i + 1] - 1
        else:
            end_idx = len(lines)
        
        chapter_lines = lines[start_idx:end_idx]
        chapter_text = '\n'.join(chapter_lines).strip()
        chapters.append(chapter_text)
    
    return chapters


def run_overview_tokenizer(
    chapters_overview: str,
    num_chapters: int
) -> Tuple[List[str], str]:
    """
    Split chapters_overview into individual chapter descriptions.
    
    First attempts programmatic regex-based splitting.
    Falls back to LLM-based tokenization if programmatic split fails.
    
    Args:
        chapters_overview: The full chapters overview text
        num_chapters: Expected number of chapters
    
    Returns:
        Tuple of (chapters_list, method) where:
        - chapters_list: List of individual chapter descriptions, or empty list if failed
        - method: "programmatic", "llm", or "failed"
    """
    if not chapters_overview or num_chapters <= 0:
        return [], "failed"
    
    success, chapters = _try_programmatic_split(chapters_overview, num_chapters)
    if success:
        return chapters, "programmatic"
    
    llm_result = call_llm_tokenize_overview(chapters_overview, num_chapters)
    
    if len(llm_result) == num_chapters:
        line_indices = [item["line_index"] for item in llm_result]
        chapters = _split_by_line_indices(chapters_overview, line_indices)
        if len(chapters) == num_chapters:
            return chapters, "llm"
    
    return [], "failed"


