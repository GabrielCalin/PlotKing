# ui/handlers.py
import gradio as gr
import os, re, json
from pipeline.constants import RUN_MODE_CHOICES
from pipeline.state_manager import request_stop, get_checkpoint, clear_stop, clear_checkpoint, save_checkpoint
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

    expanded_visible = bool(checkpoint.get("expanded_plot"))
    overview_visible = bool(checkpoint.get("chapters_overview"))
    chapters_count = len(checkpoint.get("chapters_full", []))

    try:
        total_chapters = int(checkpoint.get("num_chapters") or chapters_count)
    except Exception:
        total_chapters = chapters_count

    has_resume_markers = bool(checkpoint.get("pending_validation_index")) or bool(checkpoint.get("next_chapter_index"))
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

    plot = checkpoint.get("plot", "")
    num_chapters = checkpoint.get("num_chapters", 0)
    genre = checkpoint.get("genre", "")
    anpc = checkpoint.get("anpc", 0)
    run_mode = checkpoint.get("run_mode", RUN_MODE_CHOICES["FULL"])

    expanded = checkpoint.get("expanded_plot")
    overview = checkpoint.get("chapters_overview")
    chapters = checkpoint.get("chapters_full", [])

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
        checkpoint.get("expanded_plot", ""),
        checkpoint.get("chapters_overview", ""),
        checkpoint.get("chapters_full", []),
        gr.update(),
        gr.update(choices=[f"Chapter {i+1}" for i in range(len(chapters))]),
        f"✅ All {len(chapters)} chapters already complete.",
        "\n".join(checkpoint.get("status_log", []))
        + "\n" + ts_prefix("ℹ️ Nothing left to resume."),
        checkpoint.get("validation_text", ""),
    )

def refresh_expanded(pipeline_fn):
    checkpoint = get_checkpoint()
    if not checkpoint:
        yield "", "", [], "", gr.update(), "_No checkpoint_", "⚠️ Cannot refresh without checkpoint.", ""
        return
    clear_stop()
    yield from pipeline_fn(
        checkpoint["plot"],
        checkpoint["num_chapters"],
        checkpoint["genre"],
        checkpoint["anpc"],
        checkpoint["run_mode"],
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
        checkpoint["plot"],
        checkpoint["num_chapters"],
        checkpoint["genre"],
        checkpoint["anpc"],
        checkpoint["run_mode"],
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
        current_text_update = checkpoint.get("chapters_full", [])[0] if checkpoint.get("chapters_full") else ""
        dropdown_update = gr.update(value="Chapter 1")

    yield (
        gr.update(value=checkpoint.get("expanded_plot", "")),
        gr.update(value=checkpoint.get("chapters_overview", "")),
        checkpoint.get("chapters_full", []),
        current_text_update,
        dropdown_update,
        f"Refreshing from chapter {idx}...",
        ts_prefix(f"🔁 Refresh from chapter {idx} initiated."),
        checkpoint.get("validation_text", ""),
    )
    yield from pipeline_fn(
        checkpoint["plot"],
        checkpoint["num_chapters"],
        checkpoint["genre"],
        checkpoint["anpc"],
        checkpoint["run_mode"],
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
