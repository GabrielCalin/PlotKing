import gradio as gr
import ui.editor_handlers as H
from utils.logger import merge_logs
from ui.tabs.editor.utils import append_status, remove_highlight
from pipeline.state_manager import save_checkpoint, get_checkpoint

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
    
    base_log = current_log
    current_epoch = create_epoch or 0
    drafts = {}

    # Yield initial status
    new_log, status_update = append_status(current_log, f"✅ ({section}) Starting update pipeline...")
    yield (
        gr.update(visible=True), # viewer
        status_update, # status_strip
        gr.update(visible=False), # editor
        gr.update(visible=False), # validation_title
        gr.update(visible=False), # validation_box
        gr.update(visible=False), # apply_updates_btn
        gr.update(visible=True, interactive=True), # stop_updates_btn
        gr.update(visible=False), # regenerate_btn
        gr.update(visible=False), # continue_btn
        gr.update(visible=False), # discard2_btn
        gr.update(visible=False), # start_edit_btn
        gr.update(visible=False), # rewrite_section
        gr.update(value="View", interactive=False), # mode_radio
        gr.update(interactive=True), # section_dropdown
        gr.update(), # current_md
        new_log, # status_log
        current_epoch, # create_sections_epoch
        gr.update(visible=False), # draft_review_panel
        gr.update(choices=[], value=[]), # draft_section_list
        {} # current_drafts
    )

    # Call editor_apply which now yields drafts
    for result in H.editor_apply(section, draft_to_save, plan):
        if should_stop():
            break

        if isinstance(result, dict):
            # Initial drafts yield (just the user edit)
            drafts.update(result)
            continue

        if isinstance(result, tuple) and len(result) >= 9:
            expanded_plot, chapters_overview, chapters_full, current_text, dropdown, counter, status_log_text, validation_text, pipeline_drafts = result
            
            new_log = merge_logs(base_log, status_log_text)
            current_epoch += 1
            drafts.update(pipeline_drafts)
            
            yield (
                gr.update(visible=True), 
                gr.update(value=new_log, visible=True),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=True), # stop_btn
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(value="View", interactive=False),
                gr.update(interactive=True),
                gr.update(),
                new_log,
                current_epoch,
                gr.update(visible=False),
                gr.update(choices=list(drafts.keys()), value=list(drafts.keys())),
                drafts
            )
    
    if new_log and not new_log.endswith("\n"):
        new_log += "\n"
    
    if should_stop():
            new_log, status_update = append_status(new_log, f"🛑 ({section}) Pipeline stopped by user.")
    else:
            new_log, status_update = append_status(new_log, f"✅ ({section}) Pipeline finished. Review drafts.")

    current_epoch += 1
    
    # Final yield: Show Draft Review Panel
    yield (
        gr.update(visible=True),
        gr.update(value=new_log, visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False), # stop_btn hidden
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(value="View", interactive=True),
        gr.update(interactive=True),
        gr.update(),
        new_log,
        current_epoch,
        gr.update(visible=True), # SHOW Draft Review Panel
        gr.update(choices=list(drafts.keys()), value=list(drafts.keys())), # Populate list
        drafts # Update state
    )

def draft_accept_all(current_drafts, current_log, create_epoch):
    """Save all drafts to checkpoint."""
    if not current_drafts:
        return gr.update(visible=False), gr.update(visible=False), current_log, create_epoch, {}

    checkpoint = get_checkpoint()
    if not checkpoint:
        return gr.update(visible=False), gr.update(visible=False), current_log, create_epoch, {}

    updated_checkpoint = checkpoint.copy()
    for section, content in current_drafts.items():
        if section == "Expanded Plot":
            updated_checkpoint["expanded_plot"] = content
        elif section == "Chapters Overview":
            updated_checkpoint["chapters_overview"] = content
        elif section.startswith("Chapter "):
            try:
                chapter_num = int(section.split(" ")[1])
                chapters_full = list(updated_checkpoint.get("chapters_full", []))
                if 1 <= chapter_num <= len(chapters_full):
                    chapters_full[chapter_num - 1] = content
                    updated_checkpoint["chapters_full"] = chapters_full
            except (ValueError, IndexError):
                pass
    
    save_checkpoint(updated_checkpoint)
    
    new_log, status_update = append_status(current_log, "✅ All drafts accepted and saved.")
    new_epoch = (create_epoch or 0) + 1
    
    return (
        gr.update(visible=False), # Hide draft panel
        status_update,
        new_log,
        new_epoch,
        {} # Clear drafts
    )

def draft_revert_all(current_log):
    """Discard all drafts."""
    new_log, status_update = append_status(current_log, "❌ All drafts reverted.")
    return (
        gr.update(visible=False), # Hide draft panel
        status_update,
        new_log,
        {} # Clear drafts
    )

def draft_accept_selected(selected_sections, current_drafts, current_log, create_epoch):
    """Save selected drafts to checkpoint."""
    if not current_drafts or not selected_sections:
        return gr.update(), gr.update(), current_log, create_epoch, current_drafts

    checkpoint = get_checkpoint()
    updated_checkpoint = checkpoint.copy()
    
    remaining_drafts = current_drafts.copy()
    
    for section in selected_sections:
        if section in current_drafts:
            content = current_drafts[section]
            if section == "Expanded Plot":
                updated_checkpoint["expanded_plot"] = content
            elif section == "Chapters Overview":
                updated_checkpoint["chapters_overview"] = content
            elif section.startswith("Chapter "):
                try:
                    chapter_num = int(section.split(" ")[1])
                    chapters_full = list(updated_checkpoint.get("chapters_full", []))
                    if 1 <= chapter_num <= len(chapters_full):
                        chapters_full[chapter_num - 1] = content
                        updated_checkpoint["chapters_full"] = chapters_full
                except (ValueError, IndexError):
                    pass
            del remaining_drafts[section]

    save_checkpoint(updated_checkpoint)
    
    new_log, status_update = append_status(current_log, f"✅ Accepted {len(selected_sections)} drafts.")
    new_epoch = (create_epoch or 0) + 1
    
    if not remaining_drafts:
        # All done
        return (
            gr.update(visible=False),
            gr.update(choices=[], value=[]),
            status_update,
            new_log,
            new_epoch,
            {}
        )
    else:
        # Update list
        return (
            gr.update(visible=True),
            gr.update(choices=list(remaining_drafts.keys()), value=list(remaining_drafts.keys())),
            status_update,
            new_log,
            new_epoch,
            remaining_drafts
        )

def draft_regenerate_selected(selected_sections, current_drafts, plan, section, current_log, create_epoch):
    """Regenerate selected sections."""
    # This is complex. We need to re-run the pipeline for these sections.
    # We can reuse apply_updates logic but with a filtered plan.
    
    if not plan or not isinstance(plan, dict):
        # Can't regenerate without a plan
        return
        
    clear_stop()
    
    # Filter impacted sections in the plan
    original_impacted = plan.get("impacted_sections", [])
    filtered_impacted = [s for s in original_impacted if s in selected_sections]
    
    # Also include the edited section if selected (though usually it's the source)
    # Actually, if we regenerate, we are regenerating the *impacted* ones based on the *edited* one.
    # The edited section itself is usually fixed by the user.
    # If the user selected the edited section to regenerate... well, we can't really "regenerate" the user's manual edit 
    # unless we treat it as an AI task, but here we assume we are regenerating the *consequences*.
    
    # So we just run the pipeline again for the selected impacted sections.
    
    # We need to keep the unselected drafts!
    drafts = current_drafts.copy()
    
    base_log = current_log
    current_epoch = create_epoch or 0
    
    new_log, status_update = append_status(current_log, f"🔄 Regenerating {len(filtered_impacted)} sections...")
    
    yield (
        gr.update(visible=False), # Hide draft panel during regen
        status_update,
        new_log,
        current_epoch,
        drafts
    )
    
    edited_section = plan.get("edited_section", section)
    diff_data = plan.get("diff_data", {})
    impact_data = plan.get("impact_data", {})
    
    from pipeline.runner_edit import run_edit_pipeline_stream
    
    for result in run_edit_pipeline_stream(
        edited_section=edited_section,
        diff_data=diff_data,
        impact_data=impact_data,
        impacted_sections=filtered_impacted,
    ):
        if should_stop():
            break
            
        if isinstance(result, tuple) and len(result) >= 9:
            expanded_plot, chapters_overview, chapters_full, current_text, dropdown, counter, status_log_text, validation_text, pipeline_drafts = result
            
            new_log = merge_logs(base_log, status_log_text)
            current_epoch += 1
            # Update drafts with NEW values for regenerated sections
            drafts.update(pipeline_drafts)
            
            yield (
                gr.update(visible=False),
                gr.update(value=new_log, visible=True),
                new_log,
                current_epoch,
                drafts
            )

    if should_stop():
         new_log, status_update = append_status(new_log, f"🛑 Regeneration stopped.")
    else:
         new_log, status_update = append_status(new_log, f"✅ Regeneration complete.")
         
    yield (
        gr.update(visible=True), # Show panel again
        status_update,
        new_log,
        current_epoch,
        drafts
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
        gr.update(visible=False), # hide draft panel
        gr.update(choices=[], value=[]), # clear draft list
        {} # clear drafts
    )
