# ui/handlers.py
import gradio as gr
import os, re, json
from pipeline.constants import RUN_MODE_CHOICES
from pipeline.state_manager import request_stop, clear_stop
from pipeline.checkpoint_manager import get_checkpoint, clear_checkpoint
from utils.timestamp import ts_prefix
from ui.project_manager import (
    list_projects,
    save_project,
    load_project,
    delete_project,
    new_project,
)

# --- Helpers “pure” folosite în mai multe locuri ---

def choose_plot_for_pipeline(plot, refined):
    return refined if (refined or "").strip() else plot

def pre_run_reset_and_controls():
    clear_stop()
    clear_checkpoint()
    return (
        gr.update(visible=True, interactive=True, value="🛑 Stop"),
        gr.update(visible=False),  # resume
        gr.update(visible=False),  # generate
        gr.update(visible=False),  # regen expanded
        gr.update(visible=False),  # regen overview
        gr.update(visible=False),  # regen chapter
    )

def post_pipeline_controls():
    checkpoint = get_checkpoint()
    if not checkpoint:
        return (
            gr.update(interactive=True, visible=False),  # stop
            gr.update(visible=False),  # resume
            gr.update(visible=True),  # generate
            gr.update(visible=False), # regen expanded
            gr.update(visible=False), # regen overview
            gr.update(visible=False), # regen chapter
        )

    expanded_visible = bool(checkpoint.expanded_plot)
    overview_visible = bool(checkpoint.chapters_overview)
    chapters_count = len(checkpoint.chapters_full or [])

    try:
        total_chapters = int(checkpoint.num_chapters or chapters_count)
    except Exception:
        total_chapters = chapters_count

    has_resume_markers = bool(checkpoint.pending_validation_index) or bool(checkpoint.next_chapter_index)
    is_full_complete = expanded_visible and overview_visible and (chapters_count >= max(1, total_chapters)) and not has_resume_markers
    stopped_at_overview = expanded_visible and overview_visible and (chapters_count == 0) and not has_resume_markers
    chapters_visible = chapters_count > 0

    if is_full_complete:
        return (
            gr.update(interactive=True, visible=False),  # stop
            gr.update(visible=False),  # resume
            gr.update(visible=True),   # generate
            gr.update(visible=expanded_visible),
            gr.update(visible=overview_visible),
            gr.update(visible=chapters_visible),
        )
    elif stopped_at_overview:
        return (
            gr.update(interactive=True, visible=False),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=expanded_visible),
            gr.update(visible=overview_visible),
            gr.update(visible=False),
        )
    else:
        return (
            gr.update(interactive=True, visible=False),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=expanded_visible),
            gr.update(visible=overview_visible),
            gr.update(visible=chapters_visible),
        )

def show_stop_only():
    return (
        gr.update(visible=True, interactive=True, value="🛑 Stop"),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
    )

def stop_pipeline(cur_status):
    request_stop()
    new_status = (cur_status + "\n" + ts_prefix("🛑 Stop requested")).strip() if cur_status else ts_prefix("🛑 Stop requested")
    return new_status, gr.update(interactive=False, value="Stopping…"), gr.update(visible=False)

def show_controls_on_resume_run():
    return (
        gr.update(visible=True, interactive=True, value="🛑 Stop"),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
    )

def resume_pipeline(pipeline_fn):
    checkpoint = get_checkpoint()
    if not checkpoint:
        yield "", "", [], "", gr.update(choices=[]), "_No checkpoint_", "⚠️ No checkpoint found to resume from.", ""
        return

    plot = checkpoint.plot
    num_chapters = checkpoint.num_chapters
    genre = checkpoint.genre
    anpc = checkpoint.anpc
    run_mode = checkpoint.run_mode

    expanded = checkpoint.expanded_plot
    overview = checkpoint.chapters_overview
    chapters = checkpoint.chapters_full or []

    clear_stop()

    if not expanded:
        yield (
            "", "", [], "", gr.update(choices=[]),
            "_No expanded plot_",
            "⚠️ Cannot resume: plot not expanded yet.",
            "",
        )
        return

    if not overview:
        yield from pipeline_fn(plot, num_chapters, genre, anpc, run_mode, checkpoint=checkpoint, refresh_from="overview")
        return

    if len(chapters) < (num_chapters or 0):
        next_index = len(chapters) + 1
        yield from pipeline_fn(plot, num_chapters, genre, anpc, run_mode, checkpoint=checkpoint, refresh_from=next_index)
        return

    yield (
        checkpoint.expanded_plot or "",
        checkpoint.chapters_overview or "",
        checkpoint.chapters_full or [],
        gr.update(),
        gr.update(choices=[f"Chapter {i+1}" for i in range(len(chapters))]),
        f"✅ All {len(chapters)} chapters already complete.",
        "\n".join(checkpoint.status_log or [])
        + "\n" + ts_prefix("ℹ️ Nothing left to resume."),
        checkpoint.validation_text or "",
    )

def refresh_expanded(pipeline_fn):
    checkpoint = get_checkpoint()
    if not checkpoint:
        yield "", "", [], "", gr.update(), "_No checkpoint_", "⚠️ Cannot refresh without checkpoint.", ""
        return
    clear_stop()
    yield from pipeline_fn(
        checkpoint.plot,
        checkpoint.num_chapters,
        checkpoint.genre,
        checkpoint.anpc,
        checkpoint.run_mode,
        checkpoint=checkpoint,
        refresh_from="expanded"
    )

def refresh_overview(pipeline_fn):
    checkpoint = get_checkpoint()
    if not checkpoint:
        yield "", "", [], "", gr.update(), "_No checkpoint_", "⚠️ Cannot refresh without checkpoint.", ""
        return
    clear_stop()
    yield from pipeline_fn(
        checkpoint.plot,
        checkpoint.num_chapters,
        checkpoint.genre,
        checkpoint.anpc,
        checkpoint.run_mode,
        checkpoint=checkpoint,
        refresh_from="overview"
    )

def refresh_chapter(pipeline_fn, selected_name):
    checkpoint = get_checkpoint()
    if not checkpoint:
        yield "", "", [], "", gr.update(), "_No checkpoint_", "⚠️ Cannot refresh without checkpoint.", ""
        return
    if not selected_name:
        yield "", "", [], "", gr.update(), "_No chapter selected_", "⚠️ Please select a chapter.", ""
        return
    try:
        idx = int(selected_name.split(" ")[1])
    except Exception:
        idx = None
    clear_stop()
    if idx == 1:
        current_text_update = ""
        dropdown_update = gr.update(value=None)
    else:
        current_text_update = checkpoint.chapters_full[0] if checkpoint.chapters_full else ""
        dropdown_update = gr.update(value="Chapter 1")

    yield (
        gr.update(value=checkpoint.expanded_plot or ""),
        gr.update(value=checkpoint.chapters_overview or ""),
        checkpoint.chapters_full or [],
        current_text_update,
        dropdown_update,
        f"Refreshing from chapter {idx}...",
        ts_prefix(f"🔁 Refresh from chapter {idx} initiated."),
        checkpoint.validation_text or "",
    )
    yield from pipeline_fn(
        checkpoint.plot,
        checkpoint.num_chapters,
        checkpoint.genre,
        checkpoint.anpc,
        checkpoint.run_mode,
        checkpoint=checkpoint,
        refresh_from=idx
    )

# plot/refine mode toggles
def show_original(plot, refined):
    return gr.update(value=plot, label="Original", interactive=True,
                     placeholder="Ex: A young girl discovers a portal to another world..."), \
           "original", gr.update(value="🪄")

def show_refined(plot, refined):
    return gr.update(value=refined, label="Refined", interactive=False,
                     placeholder="This refined version will be used for generation (if present)."), \
           "refined", gr.update(value="🧹")

def refine_or_clear(plot, refined, mode, genre, refine_fn):
    if mode == "refined":
        return gr.update(value=plot, label="Original", interactive=True), "", "original", gr.update(value="🪄")
    else:
        new_refined = refine_fn(plot, genre)
        return gr.update(value=new_refined, label="Refined", interactive=False,
                         placeholder="This refined version will be used for generation (if present)."), \
               new_refined, "refined", gr.update(value="🧹")

def sync_textbox(text, mode):
    if mode == "refined":
        return gr.update(), text
    else:
        return text, gr.update()

def refresh_create_from_checkpoint(epoch, current_chapters_state, current_chapter_selector):
    """Actualizează conținutul Create tab din checkpoint când Editor modifică ceva."""
    from ui.ui_state import display_selected_chapter
    
    checkpoint = get_checkpoint()
    if not checkpoint:
        # Dacă nu există checkpoint, nu schimbăm nimic
        return (
            gr.update(),  # expanded_output
            gr.update(),  # chapters_output
            gr.update(),  # chapters_state
            gr.update(),  # current_chapter_output
            gr.update(),  # chapter_selector
            gr.update(),  # chapter_counter
        )
    
    # Citește din checkpoint
    expanded = checkpoint.expanded_plot or ""
    overview = checkpoint.chapters_overview or ""
    chapters_list = checkpoint.chapters_full or []
    
    # Actualizează expanded_output și chapters_output
    expanded_update = gr.update(value=expanded)
    overview_update = gr.update(value=overview)
    
    # Actualizează chapters_state
    chapters_state_update = chapters_list
    
    # Actualizează chapter_selector dacă numărul de capitole s-a schimbat
    if len(chapters_list) != len(current_chapters_state or []):
        if chapters_list:
            chapter_choices = [f"Chapter {i+1}" for i in range(len(chapters_list))]
            # Păstrează selecția curentă dacă e validă, altfel selectează primul
            current_value = current_chapter_selector
            if current_value not in chapter_choices:
                current_value = chapter_choices[0] if chapter_choices else None
            chapter_selector_update = gr.update(choices=chapter_choices, value=current_value)
        else:
            chapter_selector_update = gr.update(choices=[], value=None)
    else:
        # Păstrează selector-ul, dar actualizează choices în caz că s-a schimbat ceva
        if chapters_list:
            chapter_choices = [f"Chapter {i+1}" for i in range(len(chapters_list))]
            chapter_selector_update = gr.update(choices=chapter_choices)
        else:
            chapter_selector_update = gr.update()
    
    # Actualizează current_chapter_output dacă există o selecție (întotdeauna, pentru că conținutul poate fi modificat)
    if current_chapter_selector and chapters_list:
        current_chapter_update = display_selected_chapter(current_chapter_selector, chapters_list)
    else:
        current_chapter_update = gr.update(value="")
    
    # Actualizează chapter_counter
    if chapters_list:
        chapter_counter_update = gr.update(value=f"📖 {len(chapters_list)} chapter(s) available")
    else:
        chapter_counter_update = gr.update(value="_No chapters yet_")
    
    return (
        expanded_update,
        overview_update,
        chapters_state_update,
        current_chapter_update,
        chapter_selector_update,
        chapter_counter_update,
    )