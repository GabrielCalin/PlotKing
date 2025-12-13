# ui/tabs/create/create_handlers.py
import gradio as gr
import os, re, json
from pipeline.constants import RUN_MODE_CHOICES
from state.pipeline_state import request_stop, clear_stop
from state.checkpoint_manager import get_checkpoint, clear_checkpoint
from state.checkpoint_manager import get_checkpoint, clear_checkpoint
from utils.timestamp import ts_prefix
from llm.chat_refiner.llm import call_llm_chat
from llm.refine_chat.llm import refine_chat
from handlers.create.project_manager import (
    list_projects,
    save_project,
    load_project,
    delete_project,
    new_project,
)

# --- Helpers "pure" folosite în mai multe locuri ---

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
        yield from pipeline_fn(checkpoint=checkpoint, refresh_from="overview")
        return

    if len(chapters) < (checkpoint.num_chapters or 0):
        next_index = len(chapters) + 1
        yield from pipeline_fn(checkpoint=checkpoint, refresh_from=next_index)
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
    yield from pipeline_fn(checkpoint=checkpoint, refresh_from="expanded")

def refresh_overview(pipeline_fn):
    checkpoint = get_checkpoint()
    if not checkpoint:
        yield "", "", [], "", gr.update(), "_No checkpoint_", "⚠️ Cannot refresh without checkpoint.", ""
        return
    clear_stop()
    yield from pipeline_fn(checkpoint=checkpoint, refresh_from="overview")

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
    yield from pipeline_fn(checkpoint=checkpoint, refresh_from=idx)

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
    from handlers.create.utils import display_selected_chapter
    
    checkpoint = get_checkpoint()
    if not checkpoint:
        return (
            gr.update(),  # expanded_output
            gr.update(),  # chapters_output
            gr.update(),  # chapters_state
            gr.update(),  # current_chapter_output
            gr.update(),  # chapter_selector
            gr.update(),  # chapter_counter
        )
    
    expanded = checkpoint.expanded_plot or ""
    overview = checkpoint.chapters_overview or ""
    chapters_list = checkpoint.chapters_full or []
    
    expanded_update = gr.update(value=expanded)
    overview_update = gr.update(value=overview)
    
    chapters_state_update = chapters_list
    
    if len(chapters_list) != len(current_chapters_state or []):
        if chapters_list:
            chapter_choices = [f"Chapter {i+1}" for i in range(len(chapters_list))]
            current_value = current_chapter_selector
            if current_value not in chapter_choices:
                current_value = chapter_choices[0] if chapter_choices else None
            chapter_selector_update = gr.update(choices=chapter_choices, value=current_value)
        else:
            chapter_selector_update = gr.update(choices=[], value=None)
    else:
        if chapters_list:
            chapter_choices = [f"Chapter {i+1}" for i in range(len(chapters_list))]
            chapter_selector_update = gr.update(choices=chapter_choices)
        else:
            chapter_selector_update = gr.update()
    
    if current_chapter_selector and chapters_list:
        current_chapter_update = display_selected_chapter(current_chapter_selector, chapters_list)
    else:
        current_chapter_update = gr.update(value="")
    
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


# ---- Chat Handlers ----

def show_original_wrapper(plot, refined):
    u_val, mode, u_btn = show_original(plot, refined)
    return u_val, mode, u_btn, gr.update(visible=True), gr.update(visible=False)

def show_refined_wrapper(plot, refined):
    u_val, mode, u_btn = show_refined(plot, refined)
    return u_val, mode, u_btn, gr.update(visible=True), gr.update(visible=False)

def show_chat(history, plot, genre):
    new_history = history if history else []
    greeting_log = ""
    if not new_history:
            try:
                greeting = call_llm_chat(plot, genre, [], "START_SESSION", timeout=10)
                new_history.append({"role": "assistant", "content": greeting})
                greeting_log = "\nPlotKing initialized chat."
            except Exception:
                pass

    return (
        gr.update(visible=False), 
        "chat", 
        gr.update(visible=True),  # Keep refine_btn visible
        gr.update(visible=True), 
        new_history, 
        new_history,
        greeting_log
    )

def user_submit_chat_message(msg, history):
    if not msg.strip():
        # If empty, do nothing but keep controls enabled (or handle as no-op)
        return gr.update(), history, history, gr.update(), gr.update(), gr.update(), gr.update()
    
    # Optimistic update: Show user message immediately
    history.append({"role": "user", "content": msg})
    
    return (
        "",                 # Clear input
        history,            # Update chatbot
        history,            # Update state
        gr.update(interactive=False), # Disable Send
        gr.update(interactive=False), # Disable Input
        gr.update(interactive=False), # Disable Clear
        gr.update(interactive=False)  # Disable Refine
    )

def bot_reply_chat_message(history, plot, genre, current_log):
    # Retrieve last message (user's) to send to LLM context properly if needed,
    # or just pass the whole history. call_llm_chat handles history.
    # The last message in history is the user's message we just added.
    
    if not history or history[-1]["role"] != "user":
        # Should not happen in normal flow
        return history, history, current_log, gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True)

    user_msg = history[-1]["content"]
    # We pass history EXCLUDING the last message to the LLM helper if the helper appends user_msg itself?
    # Checking call_llm_chat... it accepts `user_message` string AND `chat_history`.
    # It appends user_message to the history list it sends to provider.
    # So we should pass history[:-1] as "past history" and history[-1]["content"] as current msg.
    
    past_history = history[:-1]
    
    try:
        reply = call_llm_chat(plot, genre, past_history, user_msg)
    except Exception as e:
        reply = f"Error: {str(e)}"

    history.append({"role": "assistant", "content": reply})
    
    log_msg = current_log + "\nPlotKing replied." if current_log else "PlotKing replied."
    
    return (
        history,          # Chatbot
        history,          # State
        log_msg,          # Log
        gr.update(interactive=True), # Enable Send
        gr.update(interactive=True, placeholder="Discuss with PlotKing..."),   # Enable Input
        gr.update(interactive=True), # Enable Clear
        gr.update(interactive=True)  # Enable Refine
    )

def reset_chat_handler(plot, genre, current_log):
    greeting = call_llm_chat(plot, genre, [], "START_SESSION")
    new_hist = [{"role": "assistant", "content": greeting}]
    log_msg = current_log + "\nChat reset." if current_log else "Chat reset."
    return new_hist, new_hist, log_msg

def start_refine_chat(current_log):
    # Visual feedback: disable button, show loading logic. Also disable chat controls.
    log_msg = current_log + "\nRefining plot from chat context..." if current_log else "Refining plot from chat context..."
    return (
        gr.update(interactive=False, value="⏳ Refining..."), # refine_btn
        log_msg,
        gr.update(interactive=False), # chat_msg
        gr.update(interactive=False), # send_btn
        gr.update(interactive=False)  # clear_btn
    )

def finish_refine_chat(plot, genre, history, current_log):
    if not history:
        # Revert button state if checking fails (though UI likely prevents this via separate logic, safe to check)
        return (
            gr.update(), # plot_input
            "chat",      # mode
            gr.update(), # refine_btn
            gr.update(), # chat_wrapper
            gr.update(), # refined_plot_state
            current_log + "\nChat is empty.", # log
            gr.update(interactive=True, value="Refine Chat"), # button reset
            gr.update(interactive=True), # chat_msg
            gr.update(interactive=True), # send_btn
            gr.update(interactive=True)  # clear_btn
        )

    try:
        refined_text = refine_chat(plot, genre, history)
        log_msg = current_log + "\nRefined plot generated."
        
        # Success transition
        return (
            gr.update(value=refined_text, label="Refined", interactive=False, visible=True), # plot_input shows refined
            "refined",               # mode
            gr.update(value="🧹", visible=True), # refine_btn visible
            gr.update(visible=False),# chat_wrapper hidden
            refined_text,            # state
            log_msg,                 # log
            gr.update(interactive=True, value="Refine Chat"), # refine_btn reset
            gr.update(interactive=True), # chat_msg reset
            gr.update(interactive=True), # send_btn reset
            gr.update(interactive=True)  # clear_btn reset
        )
    except Exception as e:
        return (
            gr.update(), "chat", gr.update(), gr.update(), gr.update(),
            current_log + f"\nError in refinement: {e}",
            gr.update(interactive=True, value="Refine Chat"),
            gr.update(interactive=True), # chat_msg reset
            gr.update(interactive=True), # send_btn reset
            gr.update(interactive=True)  # clear_btn reset
        )
