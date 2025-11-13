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
        (expanded_plot, chapters_overview, chapters_full, current_text, dropdown, counter, status_log, validation_text)
    """
    clear_stop()
    
    checkpoint = get_checkpoint()
    if not checkpoint:
        yield "", "", [], "", gr.update(choices=[]), "_Error_", "⚠️ No checkpoint found.", ""
        return
    
    state = PipelineContext.from_checkpoint(checkpoint)
    
    diff_summary = ""
    if diff_data.get("changes"):
        diff_summary = "\n".join(f"- {item}" for item in diff_data.get("changes", []) if item)
    else:
        diff_summary = diff_data.get("message", "")
    
    log_ui(state.status_log, f"🔄 Starting adaptive editing pipeline for: {', '.join(impacted_sections) if impacted_sections else 'no sections'}")
    yield (
        state.expanded_plot or "",
        state.chapters_overview or "",
        state.chapters_full or [],
        gr.update(),
        gr.update(choices=[f"Chapter {i+1}" for i in range(len(state.chapters_full))]),
        "_Adapting sections..._",
        "\n".join(state.status_log),
        state.validation_text,
    )
    
    if (yield from _maybe_pause_pipeline("edit pipeline start", state)):
        return
    
    # Debug: log impact_data structure
    if impact_data:
        impact_items = impact_data.get("impacted_sections", [])
        log_ui(state.status_log, f"🔍 Debug: impact_data has {len(impact_items)} impacted_sections entries")
        for item in impact_items:
            if isinstance(item, dict):
                log_ui(state.status_log, f"🔍 Debug: - {item.get('name', 'unknown')}: {item.get('reason', 'no reason')[:50]}...")
    
    # 1. Edit Expanded Plot dacă e impactat
    if "Expanded Plot" in impacted_sections:
        impact_reason = _get_section_impact(impact_data, "Expanded Plot")
        if not impact_reason:
            log_ui(state.status_log, f"⚠️ Expanded Plot in impacted_sections but no impact reason found in impact_data")
        if impact_reason:
            log_ui(state.status_log, "📝 Adapting Expanded Plot...")
            yield (
                state.expanded_plot or "",
                state.chapters_overview or "",
                state.chapters_full or [],
                gr.update(),
                gr.update(choices=[f"Chapter {i+1}" for i in range(len(state.chapters_full))]),
                "_Adapting Expanded Plot..._",
                "\n".join(state.status_log),
                state.validation_text,
            )
            
            original_plot = state.expanded_plot or ""
            state = run_plot_editor(
                context=state,
                original_plot=original_plot,
                impact_reason=impact_reason,
                diff_summary=diff_summary,
            )
            log_ui(state.status_log, "✅ Expanded Plot adapted.")
            save_checkpoint(state.__dict__)
            
            yield (
                state.expanded_plot or "",
                state.chapters_overview or "",
                state.chapters_full or [],
                gr.update(),
                gr.update(choices=[f"Chapter {i+1}" for i in range(len(state.chapters_full))]),
                "_Expanded Plot adapted_",
                "\n".join(state.status_log),
                state.validation_text,
            )
            
            if (yield from _maybe_pause_pipeline("expanded plot adaptation", state)):
                return
    
    # 2. Edit Chapters Overview dacă e impactat
    if "Chapters Overview" in impacted_sections:
        impact_reason = _get_section_impact(impact_data, "Chapters Overview")
        if not impact_reason:
            log_ui(state.status_log, f"⚠️ Chapters Overview in impacted_sections but no impact reason found in impact_data")
        if impact_reason:
            log_ui(state.status_log, "📘 Adapting Chapters Overview...")
            yield (
                state.expanded_plot or "",
                state.chapters_overview or "",
                state.chapters_full or [],
                gr.update(),
                gr.update(choices=[f"Chapter {i+1}" for i in range(len(state.chapters_full))]),
                "_Adapting Chapters Overview..._",
                "\n".join(state.status_log),
                state.validation_text,
            )
            
            original_overview = state.chapters_overview or ""
            state = run_overview_editor(
                context=state,
                original_overview=original_overview,
                impact_reason=impact_reason,
                diff_summary=diff_summary,
            )
            log_ui(state.status_log, "✅ Chapters Overview adapted.")
            save_checkpoint(state.__dict__)
            
            yield (
                state.expanded_plot or "",
                state.chapters_overview or "",
                state.chapters_full or [],
                gr.update(),
                gr.update(choices=[f"Chapter {i+1}" for i in range(len(state.chapters_full))]),
                "_Chapters Overview adapted_",
                "\n".join(state.status_log),
                state.validation_text,
            )
            
            if (yield from _maybe_pause_pipeline("chapters overview adaptation", state)):
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
        
        log_ui(state.status_log, f"✍️ Adapting {chapter_name}...")
        yield (
            state.expanded_plot or "",
            state.chapters_overview or "",
            state.chapters_full or [],
            gr.update(),
            gr.update(choices=[f"Chapter {i+1}" for i in range(len(state.chapters_full))]),
            f"_Adapting {chapter_name}..._",
            "\n".join(state.status_log),
            state.validation_text,
        )
        
        original_chapter = state.chapters_full[chapter_num - 1] or ""
        edited_chapter = run_chapter_editor(
            context=state,
            chapter_index=chapter_num,
            original_chapter=original_chapter,
            impact_reason=impact_reason,
            diff_summary=diff_summary,
        )
        
        state.chapters_full[chapter_num - 1] = edited_chapter
        log_ui(state.status_log, f"✅ {chapter_name} adapted.")
        save_checkpoint(state.__dict__)
        
        yield (
            state.expanded_plot or "",
            state.chapters_overview or "",
            state.chapters_full or [],
            gr.update(),
            gr.update(choices=[f"Chapter {i+1}" for i in range(len(state.chapters_full))]),
            f"_{chapter_name} adapted_",
            "\n".join(state.status_log),
            state.validation_text,
        )
        
        if (yield from _maybe_pause_pipeline(f"{chapter_name} adaptation", state)):
            return
    
    # Finalizare
    log_ui(state.status_log, "🎉 Adaptive editing pipeline completed!")
    final_choices = [f"Chapter {i+1}" for i in range(len(state.chapters_full))]
    dropdown_final = gr.update(choices=final_choices)
    counter_final = f"✅ Adaptation complete for {len(impacted_sections)} section(s)"
    
    save_checkpoint(state.__dict__)
    
    yield (
        state.expanded_plot or "",
        state.chapters_overview or "",
        state.chapters_full or [],
        gr.update(),
        dropdown_final,
        counter_final,
        "\n".join(state.status_log),
        state.validation_text,
    )


def _maybe_pause_pipeline(step_label: str, state: PipelineContext):
    """Helper pentru pauză pipeline (similar cu runner.py)."""
    if not is_stop_requested():
        return False
    save_checkpoint(state.__dict__)
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
    )
    return True

