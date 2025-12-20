import gradio as gr
from handlers.editor.validate_commons import editor_validate
from utils.logger import merge_logs
from handlers.editor.utils import append_status, remove_highlight
from handlers.editor.constants import Components, States
from state.checkpoint_manager import save_section, get_checkpoint, get_section_content
from state.drafts_manager import DraftsManager, DraftType

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

def _get_generated_drafts_list(plan, exclude_section):
    """Helper to generate the list of drafts for review.
    Returns ALL impacted sections from plan (except the one being edited).
    """
    if not plan:
        return []
        
    impacted_sections = plan.get("impacted_sections", [])
    
    # Simple list comprehension as requested: just the impacted sections from plan
    final_list = [s for s in impacted_sections if s != exclude_section]
    
    return final_list

def _get_revert_state(section):
    """Calculate basic state variables after a revert/accept."""
    drafts_mgr = DraftsManager()
    # Priority: only USER draft remains after cleanup
    content = drafts_mgr.get_content(section, DraftType.USER.value)
    
    if content is not None:
        return content, "Draft", "**Viewing:** <span style='color:red;'>Draft</span>", True
    else:
        content = get_section_content(section) or ""
        return content, "Checkpoint", "**Viewing:** <span style='color:red;'>Checkpoint</span>", False

def get_draft_warning(exclude_section: str) -> str:
    """Check for existing USER drafts in other sections and return a warning markdown string."""
    drafts_mgr = DraftsManager()
    user_drafts = drafts_mgr.get_user_drafts()
    
    # Exclude current section since we are validating it actively
    other_drafts = [s for s in user_drafts if s != exclude_section]
    
    if other_drafts:
        draft_names = ", ".join([f"`{d}`" for d in other_drafts])
        return f"⚠️ **Validation is based on other drafts.**\nSome related sections are still drafts: {draft_names}.\nEnsure these drafts are consistent before applying changes."
    return ""


def editor_apply(section, draft, plan):
    """
    Aplică modificarea și rulează pipeline-ul de editare dacă există secțiuni impactate.
    Returnează drafts (dict) și rulează pipeline-ul de editare.
    """
    from state.checkpoint_manager import get_checkpoint
    
    checkpoint = get_checkpoint()
    if not checkpoint:
        return {section: draft}
    
    drafts = DraftsManager()
    drafts.add_original(section, draft)
    
    if plan and isinstance(plan, dict):
        edited_section = plan.get("edited_section", section)
        diff_data = plan.get("diff_data", {})
        impact_data = plan.get("impact_data", {})
        impacted = plan.get("impacted_sections", [])
        
        if impacted:
            from pipeline.runner_edit import run_edit_pipeline_stream
            
            for result in run_edit_pipeline_stream(
                edited_section=edited_section,
                diff_data=diff_data,
                impact_data=impact_data,
                impacted_sections=impacted,
            ):
                if isinstance(result, tuple) and len(result) >= 9:
                    pipeline_drafts = result[8]
                    drafts.update(pipeline_drafts)
                    yield result
                else:
                    yield result
            return
    
    return drafts


def apply_updates(section, plan, current_log, create_epoch, current_mode, draft_content):
    """
    Apply updates based on validation plan or save directly if no plan.
    Consolidated logic: 'draft_content' is the single source of truth (from current_md state).
    """
    # Reset stop signal at start
    clear_stop()
    
    # Simple logic: the incoming draft_content IS the candidate text.
    # We just ensure it's clean of any UI-specific markup (like red highlights).
    draft_to_save = remove_highlight(draft_content or "")
    
    base_log = current_log
    current_epoch = create_epoch or 0
    
    drafts_mgr = DraftsManager()

    # If no plan (no major plot changes), save directly to checkpoint
    if not plan:
        # Add draft to DraftsManager first so draft_accept_selected can find it
        drafts_mgr.add_original(section, draft_to_save)
        
        # Reuse draft_accept_selected to save and get common return values
        draft_panel, status_strip_upd, status_log_val, epoch_val, status_row_upd, status_label_upd, btn_cp_upd, btn_dr_upd, btn_df_upd, view_state, viewer_upd, current_md_val, mode_radio_upd, view_actions_row_upd = draft_accept_selected(
            current_section=section,
            original_selected=[section],
            generated_selected=[],
            current_log=current_log,
            create_epoch=create_epoch
        )
        
        # Update log message to be more specific for this case
        new_log, status_update = append_status(current_log, f"✅ ({section}) Changes saved directly to checkpoint (no major plot changes detected).")
        
        # Return all values expected by apply_updates
        yield (
            viewer_upd, # viewer_md - from draft_accept_selected
            status_update, # status_strip - updated message
            gr.update(visible=False), # editor_tb
            gr.update(visible=False), # validation_title
            gr.update(visible=False), # validation_box
            gr.update(visible=False), # apply_updates_btn
            gr.update(visible=False), # stop_updates_btn - HIDDEN (no pipeline)
            gr.update(visible=False), # regenerate_btn
            gr.update(visible=False), # continue_btn
            gr.update(visible=False), # discard2_btn
            gr.update(visible=False), # start_edit_btn
            gr.update(visible=False), # rewrite_section
            mode_radio_upd, # mode_radio - re-enabled
            gr.update(interactive=True), # section_dropdown
            current_md_val, # current_md - from draft_accept_selected
            new_log, # status_log - updated message
            epoch_val, # create_sections_epoch - from draft_accept_selected
            gr.update(visible=False), # draft_review_panel - HIDDEN (no drafts to review)
            gr.update(choices=[], value=[]), # original_draft_checkbox
            gr.update(choices=[], value=[]), # generated_drafts_list
            status_row_upd, # status_row - from draft_accept_selected
            status_label_upd, # status_label - from draft_accept_selected
            btn_cp_upd, # btn_checkpoint - from draft_accept_selected
            btn_dr_upd, # btn_draft - from draft_accept_selected
            btn_df_upd, # btn_diff - from draft_accept_selected
            view_state, # current_view_state - from draft_accept_selected
            gr.update(value=[], choices=[]), # 27. drafts_to_keep_list
            gr.update(visible=False), # 28. keep_draft_btn
            gr.update(visible=False), # 29. rewrite_keep_draft_btn
            gr.update(visible=False), # 30. chat_keep_draft_btn
            gr.update(visible=False)  # 31. view_actions_row
        )
        return

    # Yield initial status
    new_log, status_update = append_status(current_log, f"✅ ({section}) Starting update pipeline...")
    
    # Initial DraftsManager state (ensure the version we are validating is in the ORIGINAL slot for review)
    if not drafts_mgr.has_type(section, DraftType.ORIGINAL.value):
        drafts_mgr.add_original(section, draft_to_save)

    yield (
        gr.update(value=draft_to_save, visible=True), # viewer - show initial draft
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
        gr.update(value="View", interactive=False), # mode_radio - DISABLED
        gr.update(interactive=True), # section_dropdown
        draft_to_save, # current_md - update with draft
        new_log, # status_log
        current_epoch, # create_sections_epoch
        gr.update(visible=False), # draft_review_panel
        gr.update(choices=[], value=[]), # original_draft_checkbox
        gr.update(choices=[], value=[]), # generated_drafts_list
        gr.update(visible=True), # status_row - SHOW
        gr.update(value="**Viewing:** <span style='color:red;'>Draft</span>"), # status_label
        gr.update(visible=True, interactive=True), # btn_checkpoint - VISIBLE
        gr.update(visible=True, interactive=True), # btn_draft
        gr.update(visible=True, interactive=True), # btn_diff
        "Draft", # 27. current_view_state
        gr.update(value=[], choices=[]), # 28. drafts_to_keep_list
        gr.update(visible=False), # 29. keep_draft_btn
        gr.update(visible=False), # 30. rewrite_keep_draft_btn
        gr.update(visible=False), # 31. chat_keep_draft_btn
        gr.update(visible=False)  # 32. view_actions_row
    )

    # Call editor_apply which yields pipeline results
    new_log = base_log  # Initialize with base_log
    
    for result in editor_apply(section, draft_to_save, plan):
        # result is always a tuple from pipeline now (DraftsManager is a Singleton, no need to yield it)
        
        if not isinstance(result, tuple) or len(result) < 7:
            continue  # Skip invalid results (need at least 7 elements for status_log at index 6)
        
        # Refresh draft lists
        # Original drafts from DraftsManager, Generated from plan (includes all impacted, even if not generated yet)
        current_mgr = DraftsManager()
        original_drafts = current_mgr.get_original_drafts()
        generated_drafts = _get_generated_drafts_list(plan, section)
        
        # Extract status_log_text from pipeline result (position 6)
        status_msg = result[6]  # status_log from pipeline
        new_log = merge_logs(base_log, status_msg)
        
        yield (
            gr.update(), # viewer_md - NO CHANGE
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
            gr.update(value="View", interactive=False), # mode_radio - DISABLED
            gr.update(interactive=True),
            draft_to_save, # current_md - keep updating state just in case
            new_log,
            current_epoch,
            gr.update(visible=False), # draft_review_panel
            gr.update(choices=original_drafts, value=original_drafts), # original_draft_checkbox
            gr.update(choices=generated_drafts, value=generated_drafts), # generated_drafts_list
            gr.update(), # status_row - NO CHANGE
            gr.update(), # status_label - NO CHANGE
            gr.update(), # 24. btn_checkpoint - NO CHANGE
            gr.update(), # 25. btn_draft - NO CHANGE
            gr.update(), # 26. btn_diff - NO CHANGE
            gr.update(), # 27. current_view_state - NO CHANGE
            gr.update(), # 28. drafts_to_keep_list - NO CHANGE
            gr.update(visible=False), # 29. keep_draft_btn
            gr.update(visible=False), # 30. rewrite_keep_draft_btn
            gr.update(visible=False), # 31. chat_keep_draft_btn
            gr.update(visible=False)  # 32. view_actions_row
        )
            
        # Check stop after processing and saving results
        if should_stop():
            break
    
    if new_log and not new_log.endswith("\n"):
        new_log += "\n"
    
    if should_stop():
            new_log, status_update = append_status(new_log, f"🛑 ({section}) Pipeline stopped by user.")
    else:
            new_log, status_update = append_status(new_log, f"✅ ({section}) Pipeline finished. Review drafts.")

    current_epoch += 1
    
    # Final yield: Show Draft Review Panel
    final_mgr = DraftsManager()
    original_drafts = final_mgr.get_original_drafts()
    generated_drafts = _get_generated_drafts_list(plan, section)
    
    viewer_content = final_mgr.get_content(section) or draft_to_save
    
    yield (
        gr.update(), # viewer_md - NO CHANGE (user might be viewing a different section)
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
        gr.update(value="View", interactive=False), # mode_radio - DISABLED during review
        gr.update(interactive=True),
        viewer_content, # current_md
        new_log,
        current_epoch,
        gr.update(visible=True), # SHOW Draft Review Panel
        gr.update(choices=original_drafts, value=original_drafts), # original_draft_checkbox
        gr.update(choices=generated_drafts, value=generated_drafts), # generated_drafts_list
        gr.update(), # status_row - NO CHANGE
        gr.update(), # status_label - NO CHANGE
        gr.update(), # 24. btn_checkpoint - NO CHANGE
        gr.update(), # 25. btn_draft - NO CHANGE
        gr.update(), # 26. btn_diff - NO CHANGE
        gr.update(), # 27. current_view_state - NO CHANGE
        gr.update(value=[], choices=[]), # 28. drafts_to_keep_list
        gr.update(visible=False), # 29. keep_draft_btn
        gr.update(visible=False), # 30. rewrite_keep_draft_btn
        gr.update(visible=False), # 31. chat_keep_draft_btn
        gr.update(visible=False)  # 32. view_actions_row
    )

def draft_accept_all(current_section, plan, current_log, create_epoch):
    """Save only the drafts involved in this session to checkpoint."""
    drafts_mgr = DraftsManager()
    
    # Identify involved sections: originally edited + impacted
    impacted = _get_generated_drafts_list(plan, None)
    edited = plan.get("edited_section", current_section) if plan else current_section
    sections_to_save = list(set(impacted + [edited, current_section]))
    
    for section in sections_to_save:
        content = drafts_mgr.get_content(section)
        if content is not None:
            save_section(section, content)
            # Fully remove drafts for accepted sections (they are now in checkpoint)
            drafts_mgr.remove(section)
            
    new_log, status_update = append_status(current_log, "✅ All drafts accepted and saved.")
    new_epoch = (create_epoch or 0) + 1
    
    content, view_state, mode_label, btns_visible = _get_revert_state(current_section)
    
    return (
        gr.update(visible=False), # 1. Hide draft panel
        status_update,            # 2. Status Strip
        new_log,                  # 3. Status Log
        new_epoch,                # 4. new_epoch
        gr.update(visible=True),   # 5. status_row
        gr.update(value=mode_label), # 6. status_label
        gr.update(visible=btns_visible), # 7. btn_checkpoint
        gr.update(visible=btns_visible, interactive=btns_visible), # 8. btn_draft
        gr.update(visible=btns_visible, interactive=btns_visible), # 9. btn_diff
        view_state,               # 10. current_view_state
        gr.update(value=content), # 11. Update viewer
        content,                  # 12. Update current_md
        gr.update(value="View", interactive=True), # 13. mode_radio
        gr.update(visible=False)   # 14. view_actions_row
    )

def draft_revert_all(current_section, plan, current_log):
    """Discard only session-related generated and original drafts, preserve user drafts."""
    drafts_mgr = DraftsManager()
    impacted = _get_generated_drafts_list(plan, None)
    edited = plan.get("edited_section", current_section) if plan else current_section
    sections = list(set(impacted + [edited, current_section]))
    
    drafts_mgr.keep_only_user_drafts(sections)
    
    new_log, status_update = append_status(current_log, "❌ All drafts reverted.")
    content, view_state, mode_label, btns_visible = _get_revert_state(current_section)

    return (
        gr.update(visible=False), # 1. Hide draft panel
        status_update,            # 2. Status Strip
        new_log,                  # 3. Status Log
        gr.update(visible=True),   # 4. status_row
        gr.update(value=mode_label), # 5. status_label
        gr.update(visible=btns_visible), # 6. btn_checkpoint
        gr.update(visible=btns_visible, interactive=btns_visible), # 7. btn_draft
        gr.update(visible=btns_visible, interactive=btns_visible), # 8. btn_diff
        view_state,               # 9. current_view_state
        gr.update(value=content), # 10. Update viewer
        content,                  # 11. Update current_md
        gr.update(value="View", interactive=True), # 12. mode_radio
        gr.update(visible=False)   # 13. view_actions_row
    )



def draft_accept_selected(current_section, original_selected, generated_selected, current_log, create_epoch, drafts_to_keep=None):
    """Save selected drafts to checkpoint, discard unselected, and close panel."""
    drafts_mgr = DraftsManager()
    
    # 1. Identify sections to save to CHECKPOINT (Accept)
    # Mapping: section -> content
    to_save_checkpoint = {}
    
    if generated_selected:
        for section in generated_selected:
            # Explicitly fetch GENERATED content
            if drafts_mgr.has_type(section, DraftType.GENERATED.value):
                content = drafts_mgr.get_content(section, DraftType.GENERATED.value)
                to_save_checkpoint[section] = content
                
    if original_selected:
        for section in original_selected:
            # Explicitly fetch ORIGINAL content (snapshot)
            # Only if not already selected via generated (Generated usually preferred if both selected? User shouldn't be able to select both for same sec ideally)
            if section not in to_save_checkpoint and drafts_mgr.has_type(section, DraftType.ORIGINAL.value):
                content = drafts_mgr.get_content(section, DraftType.ORIGINAL.value)
                to_save_checkpoint[section] = content

    # 2. Identify sections to KEEP AS USER DRAFT
    drafts_kept_count = 0
    if drafts_to_keep:
        for section in drafts_to_keep:
            if section in to_save_checkpoint:
                continue # Already saving to checkpoint, no need to keep draft
            
            # Logic: If GENERATED exists (from generated list), promote it to USER.
            if drafts_mgr.has_type(section, DraftType.GENERATED.value):
                content = drafts_mgr.get_content(section, DraftType.GENERATED.value)
                drafts_mgr.add_user_draft(section, content)
                # Remove generated component since it's now User
                drafts_mgr.remove(section, DraftType.GENERATED.value)
                drafts_kept_count += 1
            elif drafts_mgr.has_type(section, DraftType.ORIGINAL.value):
                # Keeping original as user draft?
                content = drafts_mgr.get_content(section, DraftType.ORIGINAL.value)
                drafts_mgr.add_user_draft(section, content)
                drafts_mgr.remove(section, DraftType.ORIGINAL.value)
                drafts_kept_count += 1

    # 3. Apply Saves to Checkpoint & Cleanup Accepted
    saved_count = 0
    for section, content in to_save_checkpoint.items():
        save_section(section, content)
        saved_count += 1
        # Accepted -> Clear ALL drafts for this section
        drafts_mgr.remove(section) 
    
    # 4. Discard Unselected / Cleanup & Reset UI
    remaining_sections = list(drafts_mgr.get_all_content().keys())
    drafts_mgr.keep_only_user_drafts(remaining_sections)

    new_log, status_update = append_status(current_log, f"✅ Accepted {saved_count} drafts. {drafts_kept_count} drafts kept as User Drafts.")
    new_epoch = (create_epoch or 0) + 1
    
    content, view_state, mode_label, btns_visible = _get_revert_state(current_section)
    
    # Return updates explicitly
    return (
        gr.update(visible=False), # 1. Hide panel
        status_update,            # 2. Status Strip
        new_log,                  # 3. Status Log
        new_epoch,                # 4. new_epoch
        gr.update(visible=True),   # 5. status_row
        gr.update(value=mode_label), # 6. status_label
        gr.update(visible=btns_visible), # 7. btn_checkpoint
        gr.update(visible=btns_visible, interactive=btns_visible), # 8. btn_draft
        gr.update(visible=btns_visible, interactive=btns_visible), # 9. btn_diff
        view_state,               # 10. current_view_state
        gr.update(value=content), # 11. Update viewer
        content,                  # 12. Update current_md
        gr.update(value="View", interactive=True), # 13. mode_radio
        gr.update(visible=False)   # 14. view_actions_row
    )

def draft_regenerate_selected(generated_selected, plan, section, current_log, create_epoch):
    """Regenerate selected sections."""
    # This is complex. We need to re-run the pipeline for these sections.
    # We can reuse apply_updates logic but with a filtered plan.
    
    if not plan or not isinstance(plan, dict):
        # Can't regenerate without a plan
        return
        
    clear_stop()
    
    # Filter impacted sections in the plan
    original_impacted = plan.get("impacted_sections", [])
    filtered_impacted = [s for s in original_impacted if s in generated_selected]
    
    # Also include the edited section if selected (though usually it's the source)
    # Actually, if we regenerate, we are regenerating the *impacted* ones based on the *edited* one.
    # The edited section itself is usually fixed by the user.
    # If the user selected the edited section to regenerate... well, we can't really "regenerate" the user's manual edit 
    # unless we treat it as an AI task, but here we assume we are regenerating the *consequences*.
    
    # So we just run the pipeline again for the selected impacted sections.
    
    # We need to keep the unselected drafts!
    drafts_mgr = DraftsManager()
    
    base_log = current_log
    current_epoch = create_epoch or 0
    
    new_log, status_update = append_status(current_log, f"🔄 Regenerating {len(filtered_impacted)} sections...")
    
    edited_section = plan.get("edited_section", section)
    diff_data = plan.get("diff_data", {})
    impact_data = plan.get("impact_data", {})
    
    # Prepare initial UI updates
    # Use edited_section as the source of truth for the original draft
    original_drafts = drafts_mgr.get_original_drafts()
    generated_drafts = _get_generated_drafts_list(plan, edited_section)
    
    yield (
        gr.update(visible=False), # Hide draft panel during regen
        gr.update(choices=original_drafts, value=original_drafts), # original_draft_checkbox
        gr.update(choices=generated_drafts, value=generated_drafts), # generated_drafts_list
        status_update,
        new_log,
        current_epoch,
        gr.update(visible=True), # status_row
        gr.update(visible=True, interactive=True) # Show and ENABLE stop button
    )
    
    from pipeline.runner_edit import run_edit_pipeline_stream
    
    for result in run_edit_pipeline_stream(
        edited_section=edited_section,
        diff_data=diff_data,
        impact_data=impact_data,
        impacted_sections=filtered_impacted,
    ):
        if isinstance(result, tuple) and len(result) >= 9:
            expanded_plot, chapters_overview, chapters_full, current_text, dropdown, counter, status_log_text, validation_text, pipeline_drafts = result
            
            new_log = merge_logs(base_log, status_log_text)
            current_epoch += 1
            
            # Update generated drafts list from plan (includes all impacted, even if not generated yet)
            current_mgr = DraftsManager()
            original_drafts = current_mgr.get_original_drafts()
            generated_drafts = _get_generated_drafts_list(plan, edited_section)
            
            yield (
                gr.update(visible=False),
                gr.update(choices=original_drafts, value=original_drafts), # original_draft_checkbox
                gr.update(choices=generated_drafts, value=generated_drafts), # generated_drafts_list
                gr.update(value=new_log, visible=True),
                new_log,
                current_epoch,
                gr.update(visible=True), # status_row
                gr.update(visible=True) # Keep stop button visible
            )
            
            # Check stop after processing and saving results
            if should_stop():
                break

    if new_log and not new_log.endswith("\n"):
        new_log += "\n"

    if should_stop():
         new_log, status_update = append_status(new_log, f"🛑 Regeneration stopped.")
    else:
         # No redundant "Regeneration complete" message, as pipeline already logs completion
         pass
    
    # Final update - show panel again
    current_mgr = DraftsManager()
    original_drafts = current_mgr.get_original_drafts()
    generated_drafts = _get_generated_drafts_list(plan, edited_section)

    yield (
        gr.update(visible=True), # Show panel again
        gr.update(choices=original_drafts, value=original_drafts), # original_draft_checkbox
        gr.update(choices=generated_drafts, value=generated_drafts), # generated_drafts_list
        status_update,
        new_log,
        current_epoch,
        gr.update(visible=True), # status_row
        gr.update(visible=False) # Hide stop button
    )

def discard_from_validate(section, current_log):
    """Revert changes from validation — return to View mode. Preserve USER drafts if exists."""
    new_log, status_update = append_status(current_log, f"🗑️ ({section}) Changes discarded.")
    content, view_state, mode_label, btns_visible = _get_revert_state(section)

    return (
        gr.update(value=content, visible=True),     # 1. Viewer
        gr.update(value="", visible=False),         # 2. Editor
        gr.update(value="", visible=False),         # 3. Validation Box
        None,                                       # 4. pending_plan
        gr.update(visible=False),                   # 5. Validation Title
        gr.update(visible=False),                   # 6. Apply Updates
        gr.update(visible=False),                   # 7. Regenerate
        gr.update(visible=False),                   # 8. Continue Editing
        gr.update(visible=False),                   # 9. Discard2
        gr.update(visible=False),                   # 10. Start Editing
        gr.update(visible=False),                   # 11. Validate
        gr.update(visible=False),                   # 12. Discard
        gr.update(visible=False),                   # 13. Force Edit
        gr.update(visible=False),                   # 14. Rewrite Section
        gr.update(value="View", interactive=True),   # 15. Mode Radio
        gr.update(interactive=True),                 # 16. Section Dropdown
        status_update,                               # 17. Status Strip
        new_log,                                     # 18. Status Log State
        content,                                     # 19. current_md
        gr.update(visible=False),                    # 20. draft panel (hidden)
        gr.update(choices=[], value=[]),             # 21. generated list
        gr.update(visible=True),                     # 22. status_row
        gr.update(value=mode_label),                 # 23. status_label
        gr.update(visible=btns_visible),             # 24. btn_checkpoint
        gr.update(visible=btns_visible, interactive=btns_visible), # 25. btn_draft
        gr.update(visible=btns_visible, interactive=btns_visible), # 26. btn_diff
        view_state,                                  # 27. view_state
        gr.update(choices=[], value=[]),             # 28. original_draft_checkbox
        gr.update(value=[], choices=[]),             # 29. drafts_to_keep_list
        gr.update(visible=False),                    # 30. keep_draft_btn
        gr.update(visible=False),                    # 31. rewrite_keep_draft_btn
        gr.update(visible=False),                    # 32. chat_keep_draft_btn
        gr.update(visible=False)                     # 33. view_actions_row
    )

def mark_drafts_to_keep_handler(original_selected, generated_selected):
    """
    Populate Drafts To Keep with selected items from other lists.
    """
    combined = []
    if original_selected:
        combined.extend(original_selected)
    if generated_selected:
        combined.extend(generated_selected)
    
    # Return as choices and formatted values (all selected)
    return gr.update(choices=combined, value=combined, visible=True)

def update_draft_buttons(original_selected, generated_selected):
    """Enable/disable draft action buttons based on selections."""
    # Accept Selected: enabled if ANY checkbox is selected
    any_selected = bool(original_selected or generated_selected)
    
    # Regenerate Selected: enabled only if auto-generated drafts are selected
    can_regenerate = bool(generated_selected)
    
    return (
        gr.update(interactive=any_selected),  # btn_draft_accept_selected
        gr.update(interactive=can_regenerate)  # btn_draft_regenerate
    )

def regenerate_dispatcher(section, editor_text, current_log, mode, current_md):
    """
    Handles 'Regenerate' button click.
    Re-runs validation logic based on the current mode and updates ONLY the Validation UI.
    """
    # 1. Common "Loading" State
    new_log, status_update = append_status(current_log, f"🔄 ({section}) Regenerating validation...")
    
    yield (
        gr.update(value="🔄 Validating..."), # validation_box
        None, # pending_plan
        gr.update(visible=True), # validation_title
        gr.update(visible=False), # apply_updates_btn
        gr.update(visible=False), # regenerate_btn
        gr.update(visible=False), # continue_btn
        gr.update(visible=False), # discard2_btn
        status_update, # status_strip
        new_log # status_log
    )
    
    # 2. Determine text to validate
    text_to_validate = ""
    if mode == "Manual":
        text_to_validate = editor_text
    else:
        # Chat and Rewrite modes use current_md state
        text_to_validate = current_md
        
    # 3. Run Validation Logic
    msg, plan = editor_validate(section, text_to_validate)
    final_log, final_status = append_status(new_log, f"✅ ({section}) Validation completed.")
    
    # 4. Common "Done" State
    yield (
        gr.update(value=msg), # validation_box
        plan, # pending_plan
        gr.update(visible=True), # validation_title
        gr.update(visible=True), # apply_updates_btn
        gr.update(visible=True), # regenerate_btn
        gr.update(visible=True), # continue_btn
        gr.update(visible=True), # discard2_btn
        final_status, # status_strip
        final_log # status_log
    )

