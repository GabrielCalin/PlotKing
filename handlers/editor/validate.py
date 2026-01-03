import gradio as gr
from handlers.editor.validate_commons import editor_validate
from utils.logger import merge_logs
from handlers.editor.utils import append_status, remove_highlight, sort_drafts
from handlers.editor.constants import Components, States
from state.checkpoint_manager import save_section, get_checkpoint, get_section_content
from state.drafts_manager import DraftsManager, DraftType
from state.undo_manager import UndoManager

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
    
    return sort_drafts(final_list)

def _get_revert_state(section):
    """Calculate basic state variables after a revert/accept."""
    drafts_mgr = DraftsManager()
    # Priority: USER draft > FILL draft > Checkpoint
    user_content = drafts_mgr.get_content(section, DraftType.USER.value)
    
    if user_content is not None:
        draft_type = DraftType.USER.value
        draft_display_name = DraftsManager.get_display_name(draft_type)
        return user_content, "Draft", f"**Viewing:** <span style='color:red;'>{draft_display_name}</span>", True
    else:
        fill_content = drafts_mgr.get_content(section, DraftType.FILL.value)
        if fill_content is not None:
            draft_type = DraftType.FILL.value
            draft_display_name = DraftsManager.get_display_name(draft_type)
            return fill_content, "Draft", f"**Viewing:** <span style='color:red;'>{draft_display_name}</span>", True
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

def get_fill_draft_warning(exclude_section: str) -> str:
    """Check for existing FILL drafts in other sections and return a warning markdown string."""
    drafts_mgr = DraftsManager()
    fill_drafts = drafts_mgr.get_fill_drafts()
    
    # Exclude current section since we are validating it actively
    other_fills = [s for s in fill_drafts if s != exclude_section]
    
    if other_fills:
        fill_names = ", ".join([f"`{d}`" for d in other_fills])
        return f"⚠️ **Multiple fill drafts present.**\nOther fill drafts exist: {fill_names}.\nThe current fill will not be validated against other fill drafts."
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
        fill_name = plan.get("fill_name")
        
        if impacted:
            from pipeline.runner_edit import run_edit_pipeline_stream
            
            for result in run_edit_pipeline_stream(
                edited_section=edited_section,
                diff_data=diff_data,
                impact_data=impact_data,
                impacted_sections=impacted,
                fill_name=fill_name,
            ):
                if isinstance(result, tuple) and len(result) >= 9:
                    pipeline_drafts = result[8]
                    drafts.update(pipeline_drafts)
                    yield result
                else:
                    yield result
            return
    
    return drafts


def apply_updates(section, plan, current_log, create_epoch, draft_content):
    """
    Apply updates based on validation plan or save directly if no plan.
    draft_content should be passed directly from the calling mode (Manual/Rewrite/Chat).
    """
    # Reset stop signal at start
    clear_stop()
    
    # Ensure content is clean of UI-specific markup (like red highlights)
    draft_to_save = remove_highlight(draft_content or "")
    
    base_log = current_log
    current_epoch = create_epoch or 0
    
    drafts_mgr = DraftsManager()

    # If no plan (no major plot changes), save directly to checkpoint
    if not plan:
        # Add draft to DraftsManager first so draft_accept_selected can find it
        drafts_mgr.add_original(section, draft_to_save)
        
        # Reuse draft_accept_selected to save and get common return values
        draft_panel, status_strip_upd, status_log_val, epoch_val, status_row_upd, status_label_upd, btn_cp_upd, btn_dr_upd, btn_df_upd, view_state, viewer_upd, mode_radio_upd, view_actions_row_upd, pending_plan_val, generated_drafts_choices_state_val, keep_drafts_choices_state_val, btn_undo_upd, btn_redo_upd, dropdown_upd = draft_accept_selected(
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
            gr.update(visible=False), # validation_section
            gr.update(visible=False), # apply_updates_btn
            gr.update(visible=False), # stop_updates_btn - HIDDEN (no pipeline)
            gr.update(visible=False), # regenerate_btn
            gr.update(visible=False), # continue_btn
            gr.update(visible=False), # discard2_btn
            gr.update(visible=False), # start_edit_btn
            gr.update(visible=False), # rewrite_section
            mode_radio_upd, # mode_radio - re-enabled
            dropdown_upd, # section_dropdown - from draft_accept_selected
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
            view_actions_row_upd, # 31. view_actions_row - from draft_accept_selected
            generated_drafts_choices_state_val, # 32. generated_drafts_choices_state - from draft_accept_selected
            keep_drafts_choices_state_val, # 33. keep_drafts_choices_state - from draft_accept_selected
            btn_undo_upd, # 34. btn_undo - from draft_accept_selected
            btn_redo_upd # 35. btn_redo - from draft_accept_selected
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
        gr.update(visible=True), # validation_section - SHOW to display stop button
        gr.update(visible=False), # apply_updates_btn
        gr.update(visible=True, interactive=True), # stop_updates_btn
        gr.update(visible=False), # regenerate_btn
        gr.update(visible=False), # continue_btn
        gr.update(visible=False), # discard2_btn
        gr.update(visible=False), # start_edit_btn
        gr.update(visible=False), # rewrite_section
        gr.update(value="View", interactive=False), # mode_radio - DISABLED
        gr.update(interactive=True), # section_dropdown
        new_log, # status_log
        current_epoch, # create_sections_epoch
        gr.update(visible=False), # draft_review_panel
        gr.update(choices=[], value=[]), # original_draft_checkbox
        gr.update(choices=[], value=[]), # generated_drafts_list
        gr.update(visible=True), # status_row - SHOW
        gr.update(value=f"**Viewing:** <span style='color:red;'>{DraftsManager.get_display_name(drafts_mgr.get_type(section))}</span>"), # status_label
        gr.update(visible=True, interactive=True), # btn_checkpoint - VISIBLE
        gr.update(visible=True, interactive=True), # btn_draft
        gr.update(visible=True, interactive=True), # btn_diff
        "Draft", # 27. current_view_state
        gr.update(value=[], choices=[]), # 28. drafts_to_keep_list
        gr.update(visible=False), # 29. keep_draft_btn
        gr.update(visible=False), # 30. rewrite_keep_draft_btn
        gr.update(visible=False), # 31. chat_keep_draft_btn
        gr.update(visible=False), # 32. view_actions_row
        [],                        # 33. generated_drafts_choices_state
        [],                        # 34. keep_drafts_choices_state
        gr.update(visible=False), # 35. btn_undo - hide during pipeline
        gr.update(visible=False)  # 36. btn_redo - hide during pipeline
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
            gr.update(visible=False), # editor_tb
            gr.update(visible=False), # validation_title
            gr.update(visible=False), # validation_box
            gr.update(visible=True), # validation_section - SHOW to display stop button
            gr.update(visible=False), # apply_updates_btn
            gr.update(visible=True), # stop_btn
            gr.update(visible=False), # regenerate_btn
            gr.update(visible=False), # continue_btn
            gr.update(visible=False), # discard2_btn
            gr.update(visible=False), # start_edit_btn
            gr.update(visible=False), # rewrite_section
            gr.update(value="View", interactive=False), # mode_radio - DISABLED
            gr.update(interactive=True), # section_dropdown
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
            gr.update(visible=False), # 32. view_actions_row
            generated_drafts,          # 33. generated_drafts_choices_state
            [],                        # 34. keep_drafts_choices_state
            gr.update(),               # 35. btn_undo - NO CHANGE
            gr.update()                # 36. btn_redo - NO CHANGE
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
        gr.update(value=new_log, visible=True), # status_strip
        gr.update(visible=False), # editor_tb
        gr.update(visible=False), # validation_title
        gr.update(visible=False), # validation_box
        gr.update(visible=True), # validation_section - SHOW to display draft_review_panel
        gr.update(visible=False), # apply_updates_btn
        gr.update(visible=False), # stop_btn hidden
        gr.update(visible=False), # regenerate_btn
        gr.update(visible=False), # continue_btn
        gr.update(visible=False), # discard2_btn
        gr.update(visible=False), # start_edit_btn
        gr.update(visible=False), # rewrite_section
        gr.update(value="View", interactive=False), # mode_radio - DISABLED during review
        gr.update(interactive=True), # section_dropdown
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
        gr.update(visible=False), # 32. view_actions_row
        generated_drafts,          # 33. generated_drafts_choices_state
        [],                        # 34. keep_drafts_choices_state
        gr.update(),               # 35. btn_undo - NO CHANGE
        gr.update()                # 36. btn_redo - NO CHANGE
    )

def draft_accept_all(current_section, plan, current_log, create_epoch):
    """Save only the drafts involved in this session to checkpoint."""
    drafts_mgr = DraftsManager()
    
    # Identify involved sections: originally edited + impacted
    impacted = _get_generated_drafts_list(plan, None)
    fill_name = plan.get("fill_name") if plan and isinstance(plan, dict) else None
    # For fills, use fill_name (real section name) instead of edited_section (which is "Chapter X (Candidate)")
    edited = fill_name if fill_name else (plan.get("edited_section", "") if plan else "")
    sections_to_save = [s for s in list(set(impacted + [edited])) if s]
    
    from state.infill_manager import InfillManager
    from state.checkpoint_manager import insert_chapter
    from state.overall_state import get_sections_list
    im = InfillManager()
    
    new_chapter_name = None
    for section in sections_to_save:
        content = drafts_mgr.get_content(section)
        if content is not None:
            if im.is_fill(section):
                idx = im.parse_fill_target(section)
                insert_chapter(idx, content)
                im.shift_fills_after_insert(idx, section)
                new_chapter_name = f"Chapter {idx}"
            else:
                save_section(section, content)
            # Fully remove drafts for accepted sections (they are now in checkpoint)
            drafts_mgr.remove(section)
    
    # Update dropdown if fill was accepted
    dropdown_update = gr.update(interactive=True)
    if new_chapter_name:
        new_opts = get_sections_list()
        dropdown_update = gr.update(choices=new_opts, value=new_chapter_name, interactive=True)
            
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
        gr.update(value="View", interactive=True), # 12. mode_radio
        gr.update(visible=btns_visible),   # 13. view_actions_row
        None, # 14. pending_plan
        [],   # 15. generated_drafts_choices_state
        [],    # 16. keep_drafts_choices_state
        gr.update(visible=False, value="↩️"), # 17. btn_undo - no drafts after accept all
        gr.update(visible=False, value="↪️"), # 18. btn_redo - no drafts after accept all
        dropdown_update, # 19. section_dropdown update
    )

def draft_revert_all(current_section, plan, current_log):
    """Discard only session-related generated and original drafts, preserve user drafts."""
    drafts_mgr = DraftsManager()
    impacted = _get_generated_drafts_list(plan, None)
    fill_name = plan.get("fill_name") if plan and isinstance(plan, dict) else None
    # For fills, use fill_name (real section name) instead of edited_section (which is "Chapter X (Candidate)")
    edited = fill_name if fill_name else (plan.get("edited_section", "") if plan else "")
    sections = [s for s in list(set(impacted + [edited])) if s]
    
    drafts_mgr.keep_only_draft_types(sections, [DraftType.USER.value, DraftType.FILL.value])
    
    new_log, status_update = append_status(current_log, "❌ All drafts reverted.")
    content, view_state, mode_label, btns_visible = _get_revert_state(current_section)
    
    # Calculate undo/redo visibility - after revert only USER draft can remain, so use normal icons
    um = UndoManager()
    undo_visible, redo_visible, undo_icon, redo_icon, _ = um.get_undo_redo_state(
        current_section, 
        drafts_mgr.get_type(current_section) if btns_visible and drafts_mgr.has(current_section) else None,
        btns_visible and drafts_mgr.has(current_section)
    )

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
        gr.update(value="View", interactive=True), # 11. mode_radio
        gr.update(visible=btns_visible),   # 13. view_actions_row
        None, # 14. pending_plan
        [],   # 15. generated_drafts_choices_state
        [],    # 16. keep_drafts_choices_state
        gr.update(visible=undo_visible, value=undo_icon), # 17. btn_undo - normal icon (no Generated after revert)
        gr.update(visible=redo_visible, value=redo_icon), # 18. btn_redo - normal icon (no Generated after revert)
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

    # 3. Apply Saves to Checkpoint & Cleanup Accepted
    from state.infill_manager import InfillManager
    from state.checkpoint_manager import insert_chapter
    from state.overall_state import get_sections_list
    im = InfillManager()

    # 2. Identify sections to KEEP AS USER DRAFT
    drafts_kept_count = 0
    if drafts_to_keep:
        for section in drafts_to_keep:
            if section == "None": # Placeholder for no drafts to keep
                continue
            if section in to_save_checkpoint:
                continue # Already saving to checkpoint, no need to keep draft
            
            # Logic: If GENERATED exists (from generated list), promote it to USER.
            if drafts_mgr.has_type(section, DraftType.GENERATED.value):
                content = drafts_mgr.get_content(section, DraftType.GENERATED.value)
                drafts_mgr.add_user_draft(section, content)
                # Remove generated component since it's now User
                drafts_mgr.remove(section, DraftType.GENERATED.value)
                drafts_kept_count += 1

    
    saved_count = 0
    new_chapter_name = None
    for section, content in to_save_checkpoint.items():
        if im.is_fill(section):
            idx = im.parse_fill_target(section)
            if idx is not None:
                insert_chapter(idx, content)
                im.shift_fills_after_insert(idx, section)
                new_chapter_name = f"Chapter {idx}"
        else:
            save_section(section, content)
            
        saved_count += 1
        # Accepted -> Clear ALL drafts for this section
        drafts_mgr.remove(section)
    
    # Update dropdown if fill was accepted
    dropdown_update = gr.update(interactive=True)
    if new_chapter_name:
        new_opts = get_sections_list()
        dropdown_update = gr.update(choices=new_opts, value=new_chapter_name, interactive=True) 
    
    # 4. Discard Unselected / Cleanup & Reset UI
    # Calculate remaining_sections: sections with GENERATED drafts that are NOT accepted and NOT kept
    all_generated_sections = drafts_mgr.get_generated_drafts()
    accepted_sections = set(to_save_checkpoint.keys())
    kept_sections = set(drafts_to_keep) if drafts_to_keep else set()
    
    remaining_sections = [
        section for section in all_generated_sections
        if section not in accepted_sections and section not in kept_sections
    ]
    
    drafts_mgr.keep_only_draft_types(remaining_sections, [DraftType.USER.value])

    new_log, status_update = append_status(current_log, f"✅ Accepted {saved_count} drafts. {drafts_kept_count} drafts kept as User Drafts.")
    new_epoch = (create_epoch or 0) + 1
    
    content, view_state, mode_label, btns_visible = _get_revert_state(current_section)
    
    # Calculate undo/redo visibility
    um = UndoManager()
    undo_visible, redo_visible, undo_icon, redo_icon, _ = um.get_undo_redo_state(
        current_section,
        drafts_mgr.get_type(current_section) if btns_visible and drafts_mgr.has(current_section) else None,
        btns_visible and drafts_mgr.has(current_section)
    )
    
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
        gr.update(value="View", interactive=True), # 12. mode_radio
        gr.update(visible=btns_visible),   # 13. view_actions_row
        None, # 14. pending_plan
        [],   # 15. generated_drafts_choices_state
        [],    # 16. keep_drafts_choices_state
        gr.update(visible=undo_visible, value=undo_icon), # 17. btn_undo
        gr.update(visible=redo_visible, value=redo_icon), # 18. btn_redo
        dropdown_update, # 19. section_dropdown update
    )

def draft_regenerate_selected(generated_selected, plan, section, current_log, create_epoch, keep_drafts_choices_state=None):
    """Regenerate selected sections."""
    # This is complex. We need to re-run the pipeline for these sections.
    # We can reuse apply_updates logic but with a filtered plan.
    
    keep_drafts_choices = keep_drafts_choices_state or []

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
    fill_name = plan.get("fill_name")
    
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
        gr.update(visible=True, interactive=True), # Show and ENABLE stop button
        generated_drafts, # generated_drafts_choices_state
        keep_drafts_choices # keep_drafts_choices_state (Persist!)
    )
    
    from pipeline.runner_edit import run_edit_pipeline_stream
    
    for result in run_edit_pipeline_stream(
        edited_section=edited_section,
        diff_data=diff_data,
        impact_data=impact_data,
        impacted_sections=filtered_impacted,
        fill_name=fill_name,
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
                gr.update(visible=True), # Keep stop button visible
                generated_drafts, # generated_drafts_choices_state
                keep_drafts_choices # keep_drafts_choices_state (Persist!)
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
        gr.update(visible=False), # Hide stop button
        generated_drafts, # generated_drafts_choices_state
        keep_drafts_choices # keep_drafts_choices_state (Persist!)
    )

def discard_from_validate(section, current_log):
    """Revert changes from validation — return to View mode. Preserve USER drafts if exists."""
    new_log, status_update = append_status(current_log, f"🗑️ ({section}) Changes discarded.")
    content, view_state, mode_label, btns_visible = _get_revert_state(section)
    
    # Calculate undo/redo visibility based on remaining draft
    drafts_mgr = DraftsManager()
    draft_type = drafts_mgr.get_type(section) if drafts_mgr.has(section) else None
    um = UndoManager()
    undo_visible, redo_visible, undo_icon, redo_icon, _ = um.get_undo_redo_state(
        section, draft_type, btns_visible
    )

    return (
        gr.update(value=content, visible=True),     # 1. Viewer
        gr.update(value="", visible=False),         # 2. Editor
        gr.update(value="", visible=False),         # 3. Validation Box
        None,                                       # 4. pending_plan
        gr.update(visible=False),                   # 5. Validation Title
        gr.update(visible=False),                   # 5b. Validation Section
        gr.update(visible=False),                   # 6. Apply Updates
        gr.update(visible=False),                   # 7. Regenerate
        gr.update(visible=False),                   # 8. Continue Editing
        gr.update(visible=False),                   # 9. Discard2
        gr.update(visible=False),                   # 10. Start Editing
        gr.update(visible=False),                   # 11. Validate
        gr.update(visible=False),                   # 12. Discard
        gr.update(visible=False),                   # 13. Force Edit
        gr.update(visible=False),                   # 14. Rewrite Section
        gr.update(value="View", interactive=True),   # mode_radio
        gr.update(interactive=True),                 # section_dropdown
        status_update,                               # status_strip
        new_log,                                     # status_log
        gr.update(visible=False),                    # draft_review_panel
        gr.update(choices=[], value=[]),             # generated_drafts_list
        gr.update(visible=True),                     # status_row
        gr.update(value=mode_label),                 # status_label
        gr.update(visible=btns_visible),             # btn_checkpoint
        gr.update(visible=btns_visible, interactive=btns_visible), # btn_draft
        gr.update(visible=btns_visible, interactive=btns_visible), # btn_diff
        view_state,                                  # view_state
        gr.update(choices=[], value=[]),             # original_draft_checkbox
        gr.update(value=[], choices=[]),             # drafts_to_keep_list
        gr.update(visible=False),                    # keep_draft_btn
        gr.update(visible=False),                    # rewrite_keep_draft_btn
        gr.update(visible=False),                    # chat_keep_draft_btn
        gr.update(visible=btns_visible),             # view_actions_row
        [],                                          # generated_drafts_choices_state
        [],                                           # keep_drafts_choices_state
        gr.update(visible=undo_visible, value=undo_icon), # btn_undo
        gr.update(visible=redo_visible, value=redo_icon), # btn_redo
    )

def mark_drafts_to_keep_handler(generated_selected, current_generated_choices, current_keep_choices):
    """
    Move selected items from 'AI Generated Drafts' to 'Drafts To Keep'.
    """

    if not generated_selected:
        return gr.update(), gr.update(), current_generated_choices, current_keep_choices
    
    # Ensure lists
    current_generated_choices = current_generated_choices or []
    current_keep_choices = current_keep_choices or []

    # Calculate new lists
    # Remove from Generated
    new_generated_choices = [c for c in current_generated_choices if c not in generated_selected]
    
    # Add to Keep (avoid duplicates just in case, though logically shouldn't happen if exclusive)
    new_keep_choices = current_keep_choices + [c for c in generated_selected if c not in current_keep_choices]
    
    # Sort the Keep list
    new_keep_choices = sort_drafts(new_keep_choices)
    
    # Return updates:
    # 1. generated_drafts_list (update choices/value)
    # 2. drafts_to_keep_list (update choices/value)
    return (
        gr.update(choices=new_generated_choices, value=new_generated_choices), 
        gr.update(choices=new_keep_choices, value=new_keep_choices, interactive=True, visible=True),
        new_generated_choices,
        new_keep_choices
    )

def move_to_generated_handler(keep_selected, current_keep_choices, current_generated_choices):
    """
    Move selected items from 'Drafts To Keep' to 'AI Generated Drafts'.
    """
    if not keep_selected:
        return gr.update(), gr.update(), current_keep_choices, current_generated_choices
        
    current_keep_choices = current_keep_choices or []
    current_generated_choices = current_generated_choices or []
    
    # Remove from Keep
    new_keep_choices = [c for c in current_keep_choices if c not in keep_selected]
    
    # Add to Generated
    new_generated_choices = current_generated_choices + [c for c in keep_selected if c not in current_generated_choices]
    new_generated_choices = sort_drafts(new_generated_choices)

    return (
        gr.update(choices=new_generated_choices, value=new_generated_choices),
        gr.update(choices=new_keep_choices, value=new_keep_choices),
        new_generated_choices,
        new_keep_choices
    )

def select_all_handler(choices):
    """Select all items in a checkbox group."""
    if not choices:
        return []
    return list(choices)

def unselect_all_handler():
    """Unselect all items in a checkbox group."""
    return []



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

def regenerate_dispatcher(section, text_to_validate, current_log):
    """
    Handles 'Regenerate' button click.
    Re-runs validation logic and updates ONLY the Validation UI.
    text_to_validate should be passed directly from the calling mode (Manual/Rewrite/Chat).
    """
    # 1. Common "Loading" State
    new_log, status_update = append_status(current_log, f"🔄 ({section}) Regenerating validation...")
    
    yield (
        gr.update(value="🔄 Validating..."), # validation_box
        None, # pending_plan
        gr.update(visible=True), # validation_title
        gr.update(visible=True), # validation_section
        gr.update(visible=False), # apply_updates_btn
        gr.update(visible=False), # regenerate_btn
        gr.update(visible=False), # continue_btn
        gr.update(visible=False), # discard2_btn
        status_update, # status_strip
        new_log # status_log
    )
    
    # 2. Run Validation Logic
    msg, plan = editor_validate(section, text_to_validate)
    final_log, final_status = append_status(new_log, f"✅ ({section}) Validation completed.")
    
    # 3. Common "Done" State
    yield (
        gr.update(value=msg), # validation_box
        plan, # pending_plan
        gr.update(visible=True), # validation_title
        gr.update(visible=True), # validation_section
        gr.update(visible=True), # apply_updates_btn
        gr.update(visible=True), # regenerate_btn
        gr.update(visible=True), # continue_btn
        gr.update(visible=True), # discard2_btn
        final_status, # status_strip
        final_log # status_log
    )

