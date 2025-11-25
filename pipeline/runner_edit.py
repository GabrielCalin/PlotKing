# -*- coding: utf-8 -*-
# pipeline/runner_edit.py
"""
Pipeline pentru editarea selectivă a secțiunilor bazat pe impact analysis.
Rulează doar pașii necesari pentru secțiunile identificate ca impactate.
"""

import gradio as gr

from pipeline.context import PipelineContext
from pipeline.state_manager import get_checkpoint, save_checkpoint, is_stop_requested, clear_stop

# Pașii de editare
from pipeline.steps.plot_editor import run_plot_editor
from pipeline.steps.overview_editor import run_overview_editor
from pipeline.steps.chapter_editor import run_chapter_editor

# Utils: logging cu timestamp
from utils.logger import log_ui


def _get_section_impact(impact_data: dict, section_name: str) -> str:
    """
    Extrage impact-ul pentru o secțiune specifică din impact_data.
    Returnează impact_reason sau None dacă nu e găsit.
    """
    if not impact_data or not isinstance(impact_data, dict):
        return None
    
    impact_list = impact_data.get("impacted_sections", []) or []
    for entry in impact_list:
        if isinstance(entry, dict):
            name = entry.get("name", "")
            reason = entry.get("reason", "")
            if name == section_name and reason:
                return reason
    
    return None


def run_edit_pipeline_stream(
    edited_section: str,
    diff_data: dict,
    impact_data: dict,
    impacted_sections: list,
):
    """
    Rulează pipeline-ul de editare pentru secțiunile impactate.
    
    Args:
        edited_section: Numele secțiunii editate de user (ex: "Chapter 4")
        diff_data: Datele diff-ului din version_diff
        impact_data: Datele impact-ului din impact_analyzer
        impacted_sections: Lista de nume de secțiuni impactate
    
    Yields:
        (expanded_plot, chapters_overview, chapters_full, current_text, dropdown, counter, status_log, validation_text, drafts_dict)
    """
    clear_stop()
    
    checkpoint = get_checkpoint()
    if not checkpoint:
        yield "", "", [], "", gr.update(choices=[]), "_Error_", "⚠️ No checkpoint found.", "", {}
        return
    
    # Initialize state from checkpoint (temporary state)
    state = PipelineContext.from_checkpoint(checkpoint)
    
    # Dictionary to store drafts: {section_name: new_content}
    drafts = {}
    
    # Creează un log nou doar pentru edit pipeline (nu modificăm state.status_log existent)
    edit_log = []
    
    diff_summary = ""
    if diff_data.get("changes"):
        diff_summary = "\n".join(f"- {item}" for item in diff_data.get("changes", []) if item)
    else:
        diff_summary = diff_data.get("message", "")
    
    # Yield cu log-urile existente (edit_log este gol la început)
    yield (
        state.expanded_plot or "",
        state.chapters_overview or "",
        state.chapters_full or [],
        gr.update(),
        gr.update(choices=[f"Chapter {i+1}" for i in range(len(state.chapters_full))]),
        "_Adapting sections..._",
        "\n".join(edit_log),
        state.validation_text,
        drafts
    )
    
    if (yield from _maybe_pause_pipeline("edit pipeline start", state, drafts)):
        return
    
    # 1. Edit Expanded Plot dacă e impactat
    if "Expanded Plot" in impacted_sections:
        impact_reason = _get_section_impact(impact_data, "Expanded Plot")
        if impact_reason:
            log_ui(edit_log, "📝 Adapting Expanded Plot...")
            yield (
                state.expanded_plot or "",
                state.chapters_overview or "",
                state.chapters_full or [],
                gr.update(),
                gr.update(choices=[f"Chapter {i+1}" for i in range(len(state.chapters_full))]),
                "_Adapting Expanded Plot..._",
                "\n".join(edit_log),
                state.validation_text,
                drafts
            )
            
            original_plot = state.expanded_plot or ""
            state = run_plot_editor(
                context=state,
                original_plot=original_plot,
                impact_reason=impact_reason,
                diff_summary=diff_summary,
                edited_section=edited_section,
            )
            drafts["Expanded Plot"] = state.expanded_plot
            log_ui(edit_log, "✅ Expanded Plot adapted.")
            # DO NOT SAVE CHECKPOINT
            
            yield (
                state.expanded_plot or "",
                state.chapters_overview or "",
                state.chapters_full or [],
                gr.update(),
                gr.update(choices=[f"Chapter {i+1}" for i in range(len(state.chapters_full))]),
                "_Expanded Plot adapted_",
                "\n".join(edit_log),
                state.validation_text,
                drafts
            )
            
            if (yield from _maybe_pause_pipeline("expanded plot adaptation", state, drafts)):
                return
    
    # 2. Edit Chapters Overview dacă e impactat
    if "Chapters Overview" in impacted_sections:
        impact_reason = _get_section_impact(impact_data, "Chapters Overview")
        if impact_reason:
            log_ui(edit_log, "📘 Adapting Chapters Overview...")
            yield (
                state.expanded_plot or "",
                state.chapters_overview or "",
                state.chapters_full or [],
                gr.update(),
                gr.update(choices=[f"Chapter {i+1}" for i in range(len(state.chapters_full))]),
                "_Adapting Chapters Overview..._",
                "\n".join(edit_log),
                state.validation_text,
                drafts
            )
            
            original_overview = state.chapters_overview or ""
            state = run_overview_editor(
                context=state,
                original_overview=original_overview,
                impact_reason=impact_reason,
                diff_summary=diff_summary,
                edited_section=edited_section,
            )
            drafts["Chapters Overview"] = state.chapters_overview
            log_ui(edit_log, "✅ Chapters Overview adapted.")
            # DO NOT SAVE CHECKPOINT
            
            yield (
                state.expanded_plot or "",
                state.chapters_overview or "",
                state.chapters_full or [],
                gr.update(),
                gr.update(choices=[f"Chapter {i+1}" for i in range(len(state.chapters_full))]),
                "_Chapters Overview adapted_",
                "\n".join(edit_log),
                state.validation_text,
                drafts
            )
            
            if (yield from _maybe_pause_pipeline("chapters overview adaptation", state, drafts)):
                return
    
    # 3. Edit capitolele impactate
    chapters_to_edit = [s for s in impacted_sections if s.startswith("Chapter ")]
    for chapter_name in sorted(chapters_to_edit, key=lambda x: int(x.split()[1]) if x.split()[1].isdigit() else 0):
        try:
            chapter_num = int(chapter_name.split()[1])
        except (ValueError, IndexError):
            continue
        
        if chapter_num < 1 or chapter_num > len(state.chapters_full):
            continue
        
        impact_reason = _get_section_impact(impact_data, chapter_name)
        if not impact_reason:
            continue
        
        log_ui(edit_log, f"✍️ Adapting {chapter_name}...")
        yield (
            state.expanded_plot or "",
            state.chapters_overview or "",
            state.chapters_full or [],
            gr.update(),
            gr.update(choices=[f"Chapter {i+1}" for i in range(len(state.chapters_full))]),
            f"_Adapting {chapter_name}..._",
            "\n".join(edit_log),
            state.validation_text,
            drafts
        )
        
        original_chapter = state.chapters_full[chapter_num - 1] or ""
        edited_chapter = run_chapter_editor(
            context=state,
            chapter_index=chapter_num,
            original_chapter=original_chapter,
            impact_reason=impact_reason,
            diff_summary=diff_summary,
            edited_section=edited_section,
        )
        
        state.chapters_full[chapter_num - 1] = edited_chapter
        drafts[chapter_name] = edited_chapter
        log_ui(edit_log, f"✅ {chapter_name} adapted.")
        # DO NOT SAVE CHECKPOINT
        
        yield (
            state.expanded_plot or "",
            state.chapters_overview or "",
            state.chapters_full or [],
            gr.update(),
            gr.update(choices=[f"Chapter {i+1}" for i in range(len(state.chapters_full))]),
            f"_{chapter_name} adapted_",
            "\n".join(edit_log),
            state.validation_text,
            drafts
        )
        
        if (yield from _maybe_pause_pipeline(f"{chapter_name} adaptation", state, drafts)):
            return
    
    # Finalizare
    log_ui(edit_log, f"🎉 Adaptive editing pipeline completed!")
    final_choices = [f"Chapter {i+1}" for i in range(len(state.chapters_full))]
    dropdown_final = gr.update(choices=final_choices)
    counter_final = f"✅ Adaptation complete for {len(impacted_sections)} section(s)"
    
    # DO NOT SAVE CHECKPOINT
    
    yield (
        state.expanded_plot or "",
        state.chapters_overview or "",
        state.chapters_full or [],
        gr.update(),
        dropdown_final,
        counter_final,
        "\n".join(edit_log),
        state.validation_text,
        drafts
    )


def _maybe_pause_pipeline(step_label: str, state: PipelineContext, drafts: dict):
    """Helper pentru pauză pipeline (similar cu runner.py)."""
    if not is_stop_requested():
        return False
    # DO NOT SAVE CHECKPOINT
    log_ui(state.status_log, f"🛑 Stop requested — pipeline paused after {step_label}.")
    yield (
        state.expanded_plot or "",
        state.chapters_overview or "",
        state.chapters_full or [],
        gr.update(),
        gr.update(choices=[f"Chapter {i+1}" for i in range(len(state.chapters_full))]) if state.chapters_full else gr.update(choices=[]),
        "_Paused_",
        "\n".join(state.status_log),
        state.validation_text,
        drafts
    )
    return True

