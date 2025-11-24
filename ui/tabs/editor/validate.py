import gradio as gr
import ui.editor_handlers as H
from utils.logger import merge_logs
from ui.tabs.editor.utils import append_status, remove_highlight

_stop_flag = False

def request_stop():
    global _stop_flag
    _stop_flag = True
    return gr.update(interactive=False)

def clear_stop():
    global _stop_flag
    _stop_flag = False

def should_stop():
    global _stop_flag
    return _stop_flag

def apply_updates(section, draft, plan, current_log, create_epoch, current_mode, current_md):
    """
    Aplică modificările și rulează pipeline-ul de editare dacă există secțiuni impactate.
    Este generator dacă există plan, altfel returnează direct.
    """
    # Reset stop signal at start
    clear_stop()

    # In Rewrite mode, use current_md (without highlights) instead of draft from editor_tb
    if current_mode == "Rewrite" and current_md:
        draft_clean = remove_highlight(current_md)
        draft_to_save = draft_clean
    elif current_mode == "Chat" and current_md:
        draft_to_save = current_md
    else:
        draft_to_save = draft
    
    if plan and isinstance(plan, dict) and plan.get("impacted_sections"):
        base_log = current_log
        current_epoch = create_epoch or 0
        
        # Yield imediat cu draft-ul salvat pentru a actualiza markdown-ul
        new_log, status_update = append_status(current_log, f"✅ ({section}) Changes saved. Adapting impacted sections...")
        yield (
            gr.update(value=draft_to_save, visible=True),  # afișează draft-ul salvat imediat
            status_update,  # update Process Log
            gr.update(visible=False),   # hide Editor
            gr.update(visible=False),   # hide Validation Title
            gr.update(visible=False),   # hide Validation Box
            gr.update(visible=False),   # hide Apply Updates
            gr.update(visible=True, interactive=True),    # SHOW Stop Button (interactive)
            gr.update(visible=False),   # hide Regenerate
            gr.update(visible=False),   # hide Continue Editing
            gr.update(visible=False),   # hide Discard2
            gr.update(visible=False),   # hide Start Editing (pipeline running)
            gr.update(visible=False),   # hide Rewrite Section
            gr.update(value="View", interactive=False),  # set Mode to View and lock
            gr.update(interactive=True),  # allow Section change
            draft_to_save,  # update current_md state with draft (without highlights)
            new_log,  # update status_log state
            current_epoch,  # bump create_sections_epoch
        )
        
        for result in H.editor_apply(section, draft_to_save, plan):
            # Check for stop signal
            if should_stop():
                break

            if isinstance(result, tuple) and len(result) == 8:
                expanded_plot, chapters_overview, chapters_full, current_text, dropdown, counter, status_log_text, validation_text = result
                
                new_log = merge_logs(base_log, status_log_text)
                current_epoch += 1  # Bump create_sections_epoch at each iteration
                
                yield (
                    gr.update(visible=True),  # keep viewer visible, don't change content
                    gr.update(value=new_log, visible=True),  # update Process Log
                    gr.update(visible=False),   # hide Editor
                    gr.update(visible=False),   # hide Validation Title
                    gr.update(visible=False),   # hide Validation Box
                    gr.update(visible=False),   # hide Apply Updates
                    gr.update(visible=True),    # keep Stop Button visible
                    gr.update(visible=False),   # hide Regenerate
                    gr.update(visible=False),   # hide Continue Editing
                    gr.update(visible=False),   # hide Discard2
                    gr.update(visible=False),   # hide Start Editing (pipeline running)
                    gr.update(visible=False),   # hide Rewrite Section
                    gr.update(value="View", interactive=False),  # set Mode to View and lock
                    gr.update(interactive=True),  # allow Section change
                    gr.update(),  # keep current_md state unchanged
                    new_log,  # update status_log state
                    current_epoch,  # bump create_sections_epoch to notify Create tab at each iteration
                )
        
        if new_log and not new_log.endswith("\n"):
            new_log += "\n"
        
        if should_stop():
             new_log, status_update = append_status(new_log, f"🛑 ({section}) Adaptive editing pipeline stopped!")
        else:
             new_log, status_update = append_status(new_log, f"✅ ({section}) Synced and sections adapted.")

        current_epoch += 1  # Bump create_sections_epoch at final yield too
        yield (
            gr.update(visible=True),  # keep viewer visible, don't change content
            gr.update(value=new_log, visible=True),  # update Process Log with final message
            gr.update(visible=False),   # hide Editor
            gr.update(visible=False),   # hide Validation Title
            gr.update(visible=False),   # hide Validation Box
            gr.update(visible=False),   # hide Apply Updates
            gr.update(visible=False),   # HIDE Stop Button
            gr.update(visible=False),   # hide Regenerate
            gr.update(visible=False),   # hide Continue Editing
            gr.update(visible=False),   # hide Discard2
            gr.update(visible=False),  # hide Start Editing (Mode is set to View after Apply)
            gr.update(visible=False),   # hide Rewrite Section
            gr.update(value="View", interactive=True),  # unlock Mode (pipeline finished)
            gr.update(interactive=True),  # unlock Section (pipeline finished)
            gr.update(),  # keep current_md state unchanged
            new_log,  # update status_log state
            current_epoch,  # bump create_sections_epoch to notify Create tab at final yield
        )
    else:
        # Nu există plan sau secțiuni impactate, doar salvează modificarea
        result = H.editor_apply(section, draft_to_save, plan)
        # editor_apply poate fi generator sau returnează tuple
        if hasattr(result, '__iter__') and not isinstance(result, (str, tuple)):
            # Este generator, dar nu ar trebui să fie în acest caz
            for item in result:
                pass  # Consumă generator-ul
        
        new_log, status_update = append_status(current_log, f"✅ ({section}) Synced.")
        new_create_epoch = (create_epoch or 0) + 1  # Bump create_sections_epoch AFTER save completes

        yield (
            gr.update(value=draft_to_save, visible=True),  # update and show Viewer with draft (without highlights)
            gr.update(value=new_log, visible=True),  # update Process Log
            gr.update(visible=False),   # hide Editor
            gr.update(visible=False),   # hide Validation Title
            gr.update(visible=False),   # hide Validation Box
            gr.update(visible=False),   # hide Apply Updates
            gr.update(visible=False),   # hide Stop Button
            gr.update(visible=False),   # hide Regenerate
            gr.update(visible=False),   # hide Continue Editing
            gr.update(visible=False),   # hide Discard2
            gr.update(visible=False),  # hide Start Editing (Mode is set to View after Apply)
            gr.update(visible=False),   # hide Rewrite Section
            gr.update(value="View", interactive=True), # reset Mode to View and unlock
            gr.update(interactive=True), # unlock Section
            draft_to_save,  # update current_md state with draft (without highlights)
            new_log,  # update status_log state
            new_create_epoch,  # bump create_sections_epoch to notify Create tab
        )

def discard_from_validate(section, current_log):
    """Revert changes from validation — return to View mode with no buttons visible. Always use checkpoint as source of truth."""
    clean_text = H.editor_get_section_content(section) or "_Empty_"
    new_log, status_update = append_status(current_log, f"🗑️ ({section}) Changes discarded.")
    return (
        gr.update(value=clean_text, visible=True),  # update and show Viewer with clean text from checkpoint
        gr.update(value="", visible=False),   # clear and hide Editor
        gr.update(value="", visible=False),  # clear and hide Validation Box
        None,  # clear pending_plan
        gr.update(visible=False),   # hide Validation Title
        gr.update(visible=False),   # hide Apply Updates
        gr.update(visible=False),   # hide Regenerate
        gr.update(visible=False),   # hide Continue Editing
        gr.update(visible=False),   # hide Discard2
        gr.update(visible=False),   # hide Start Editing (View mode - no buttons)
        gr.update(visible=False),   # hide Validate
        gr.update(visible=False),   # hide Discard
        gr.update(visible=False),   # hide Force Edit
        gr.update(visible=False),   # hide Rewrite Section
        gr.update(value="View", interactive=True),  # set Mode to View and unlock
        gr.update(interactive=True),# unlock Section
        status_update,
        new_log,
        clean_text,  # current_md - resetat la textul curat din checkpoint
    )
