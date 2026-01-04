# -*- coding: utf-8 -*-
# pipeline/steps/chapter_editor/pipeline.py
"""
Wrapper pipeline-friendly pentru editarea unui capitol bazat pe impact și diff.
"""

from typing import List, Tuple, Optional
from state.pipeline_context import PipelineContext
from .llm import call_llm_edit_chapter


def _get_fill_chapter_num(fill_name: Optional[str]) -> Optional[int]:
    """Calculează numărul capitolului fill din numele fill-ului."""
    if not fill_name:
        return None
    from state.infill_manager import InfillManager
    im = InfillManager()
    return im.parse_fill_target(fill_name)


def _build_previous_chapters_with_fill(
    context: PipelineContext,
    chapter_index: int,
    fill_name: Optional[str],
    fill_chapter_num: Optional[int],
) -> List[str]:
    """
    Construiește lista de capitole anterioare considerând fill-ul dacă există.
    Include capitolele înainte de fill, fill-ul, și capitolele între fill și capitolul editat.
    """
    if not fill_name or not fill_chapter_num or fill_chapter_num > chapter_index:
        return []
    
    from state.drafts_manager import DraftsManager
    drafts_mgr = DraftsManager()
    fill_content = drafts_mgr.get_content(fill_name)
    
    if not fill_content:
        return []
    
    before_fill = context.chapters_full[:fill_chapter_num - 1] if fill_chapter_num > 1 else []
    after_fill = context.chapters_full[fill_chapter_num - 1:chapter_index - 1] if fill_chapter_num < chapter_index else []
    return before_fill + [fill_content] + after_fill


def _calculate_infill_chapter_info(
    chapter_index: int,
    fill_name: Optional[str],
    fill_chapter_num: Optional[int],
    edited_section: str,
) -> Tuple[int, str]:
    """
    Calculează numărul capitolului după renumbering și numele secțiunii editate pentru infill.
    Returnează (new_chapter_number, updated_edited_section).
    """
    new_chapter_number = chapter_index
    updated_edited_section = edited_section
    
    if fill_name and fill_chapter_num:
        if chapter_index >= fill_chapter_num:
            new_chapter_number = chapter_index + 1
        
        if "(Candidate)" in edited_section:
            updated_edited_section = f"Chapter {fill_chapter_num}"
        elif fill_name in edited_section or "Candidate" in edited_section:
            updated_edited_section = f"Chapter {fill_chapter_num}"
    
    return new_chapter_number, updated_edited_section


def run_chapter_editor(
    context: PipelineContext,
    chapter_index: int,
    original_chapter: str,
    impact_reason: str,
    diff_summary: str,
    edited_section: str = "",
    fill_name: str = None,
) -> str:
    """
    Returnează textul capitolului editat, fără efecte secundare asupra contextului.
    - chapter_index este 1-based (vechiul număr de capitol din checkpoint)
    - fill_name este pentru cazul când avem un fill care trebuie inclus în previous_chapters
    - Pentru infill, chapter_number în prompt va fi chapter_index + 1 (după renumbering)
    """
    fill_chapter_num = None
    if fill_name:
        fill_chapter_num = _get_fill_chapter_num(fill_name)
    
    previous_chapters: List[str] = []
    if chapter_index > 1:
        previous_chapters = context.chapters_full[:chapter_index - 1]
    
    if fill_name and fill_chapter_num and fill_chapter_num <= chapter_index:
        fill_previous_chapters = _build_previous_chapters_with_fill(
            context, chapter_index, fill_name, fill_chapter_num
        )
        if fill_previous_chapters:
            previous_chapters = fill_previous_chapters

    if fill_name and fill_chapter_num:
        new_chapter_number, updated_edited_section = _calculate_infill_chapter_info(
            chapter_index, fill_name, fill_chapter_num, edited_section
        )
    else:
        new_chapter_number = chapter_index
        updated_edited_section = edited_section

    return call_llm_edit_chapter(
        expanded_plot=context.expanded_plot or "",
        chapters_overview=context.chapters_overview or "",
        chapter_index=new_chapter_number,  # Use new chapter number after renumbering
        previous_chapters=previous_chapters,
        original_chapter=original_chapter,
        impact_reason=impact_reason,
        diff_summary=diff_summary,
        edited_section=updated_edited_section,  # Use updated edited_section without (Candidate)
        genre=context.genre or "",
        anpc=context.anpc,
        is_infill=fill_name is not None,
    )

