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

def _get_generated_drafts_list(plan, drafts, exclude_section):
    """Helper to generate the list of auto-generated drafts from plan and current drafts."""
    if not plan:
        return []
    impacted_sections = plan.get("impacted_sections", [])
    generated_drafts = [s for s in impacted_sections if s != exclude_section]
    # Ensure any other drafts are also included (just in case)
    for s in drafts.keys():
        if s != exclude_section and s not in generated_drafts:
            generated_drafts.append(s)
    return generated_drafts

def _save_section_to_checkpoint(section, content):
    """Helper to save a single section's content to checkpoint. Returns True if saved successfully."""
    checkpoint = get_checkpoint()
    if not checkpoint:
        return False
    
    updated_checkpoint = checkpoint.copy()
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
            return False
    
    save_checkpoint(updated_checkpoint)
    return True


def apply_updates(section, draft, plan, current_log, create_epoch, current_mode, current_md, current_drafts):
    """
    Aplică modificările și rulează pipeline-ul de editare dacă există secțiuni impactate.
    Este generator dacă există plan, altfel returnează direct.
    For Chat mode, current_md already contains the draft, so we use it directly.
    current_drafts is used to preserve existing drafts state (for other sections) and update it after apply.
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
    # Start with existing drafts to preserve drafts for other sections
    drafts = (current_drafts or {}).copy()

    # If no plan (no major plot changes), save directly to checkpoint
    if not plan:
        # Reuse draft_accept_selected to save and get common return values
        draft_panel, status_strip_upd, status_log_val, epoch_val, drafts_dict, status_row_upd, status_label_upd, btn_cp_upd, btn_dr_upd, btn_df_upd, view_state, viewer_upd, current_md_val, mode_radio_upd = draft_accept_selected(
            current_section=section,
            original_selected=[section],
            generated_selected=[],
            current_drafts={section: draft_to_save},
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
            drafts_dict, # current_drafts - from draft_accept_selected (should be {})
            status_row_upd, # status_row - from draft_accept_selected
            status_label_upd, # status_label - from draft_accept_selected
            btn_cp_upd, # btn_checkpoint - from draft_accept_selected
            btn_dr_upd, # btn_draft - from draft_accept_selected
            btn_df_upd, # btn_diff - from draft_accept_selected
            view_state # current_view_state - from draft_accept_selected
        )
        return

    # Yield initial status
    new_log, status_update = append_status(current_log, f"✅ ({section}) Starting update pipeline...")
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
        drafts, # current_drafts - preserve existing drafts
        gr.update(visible=True), # status_row - SHOW
        gr.update(value="**Viewing:** <span style='color:red;'>Draft</span>"), # status_label
        gr.update(visible=True, interactive=True), # btn_checkpoint - VISIBLE
        gr.update(visible=True, interactive=True), # btn_draft
        gr.update(visible=True, interactive=True), # btn_diff
        "Draft" # current_view_state
    )

    # Call editor_apply which now yields drafts
    for result in H.editor_apply(section, draft_to_save, plan):
        if isinstance(result, dict):
            # Initial drafts yield (just the user edit)
            drafts.update(result)
        elif isinstance(result, tuple) and len(result) >= 9:
            expanded_plot, chapters_overview, chapters_full, current_text, dropdown, counter, status_log_text, validation_text, pipeline_drafts = result
            
            new_log = merge_logs(base_log, status_log_text)
            current_epoch += 1
            drafts.update(pipeline_drafts)
            
            # Determine content to show in viewer:
            # User requested NOT to update viewer during generation for other sections.
            # We only updated it initially.
            
            viewer_content = drafts.get(section, draft_to_save)
            
            # Split drafts for UI - use plan to show ALL impacted sections even if not generated yet
            generated_drafts = _get_generated_drafts_list(plan, drafts, section)

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
                viewer_content, # current_md - keep updating state just in case
                new_log,
                current_epoch,
                gr.update(visible=False), # draft_review_panel
                gr.update(choices=[section], value=[section]), # original_draft_checkbox - auto-select
                gr.update(choices=generated_drafts, value=generated_drafts), # generated_drafts_list - auto-select
                drafts,
                gr.update(), # status_row - NO CHANGE
                gr.update(), # status_label - NO CHANGE
                gr.update(), # btn_checkpoint - NO CHANGE
                gr.update(), # btn_draft - NO CHANGE
                gr.update(), # btn_diff - NO CHANGE
                gr.update() # current_view_state - NO CHANGE
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
    # Split drafts into original (the edited section) and generated (impacted sections)
    viewer_content = drafts.get(section, draft_to_save)
    
    # Separate original draft from generated drafts
    generated_drafts = _get_generated_drafts_list(plan, drafts, section)
    
    yield (
        gr.update(), # viewer_md - NO CHANGE

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
        gr.update(choices=[section], value=[section]), # original_draft_checkbox - auto-select
        gr.update(choices=generated_drafts, value=generated_drafts), # generated_drafts_list - auto-select all
        drafts, # Update state
        gr.update(), # status_row - NO CHANGE
        gr.update(), # status_label - NO CHANGE
        gr.update(), # btn_checkpoint - NO CHANGE
        gr.update(), # btn_draft - NO CHANGE
        gr.update(), # btn_diff - NO CHANGE
        gr.update() # current_view_state - NO CHANGE
    )

def draft_accept_all(current_section, current_drafts, current_log, create_epoch):
    """Save all drafts to checkpoint."""
    if not current_drafts:
        return gr.update(visible=False), gr.update(visible=False), current_log, create_epoch, {}, gr.update(visible=True), gr.update(value="**Viewing:** <span style='color:red;'>Checkpoint</span>"), gr.update(interactive=True), gr.update(visible=False), gr.update(visible=False), "Checkpoint", gr.update(), gr.update(interactive=True)


    for section, content in current_drafts.items():
        _save_section_to_checkpoint(section, content)
    
    new_log, status_update = append_status(current_log, "✅ All drafts accepted and saved.")
    new_epoch = (create_epoch or 0) + 1
    
    # Get fresh content for viewer
    fresh_content = H.editor_get_section_content(current_section) or ""
    
    return (
        gr.update(visible=False), # Hide draft panel
        status_update,
        new_log,
        new_epoch,
        {}, # Clear drafts
        gr.update(visible=True), # status_row
        gr.update(value="**Viewing:** <span style='color:red;'>Checkpoint</span>"), # status_label
        gr.update(visible=False), # btn_checkpoint - HIDDEN (no draft = no point showing C only)
        gr.update(visible=False), # btn_draft
        gr.update(visible=False), # btn_diff
        "Checkpoint", # current_view_state
        gr.update(value=fresh_content), # Update viewer with fresh content
        fresh_content, # Update current_md
        gr.update(interactive=True) # mode_radio - ENABLED
    )

def draft_revert_all(current_section, current_log):
    """Discard all drafts."""
    new_log, status_update = append_status(current_log, "❌ All drafts reverted.")
    
    # Get fresh content for viewer (original checkpoint content)
    fresh_content = H.editor_get_section_content(current_section) or ""
    
    return (
        gr.update(visible=False), # Hide draft panel
        status_update,
        new_log,
        {}, # Clear drafts
        gr.update(visible=True), # status_row
        gr.update(value="**Viewing:** <span style='color:red;'>Checkpoint</span>"), # status_label
        gr.update(visible=False), # btn_checkpoint - HIDDEN
        gr.update(visible=False), # btn_draft
        gr.update(visible=False), # btn_diff
        "Checkpoint", # current_view_state
        gr.update(value=fresh_content), # Update viewer with fresh content
        fresh_content, # Update current_md
        gr.update(interactive=True) # mode_radio - ENABLED
    )

def draft_accept_selected(current_section, original_selected, generated_selected, current_drafts, current_log, create_epoch):
    """Save selected drafts to checkpoint, discard unselected, and close panel."""
    if not current_drafts:
        return gr.update(visible=False), gr.update(), current_log, create_epoch, {}, gr.update(visible=True), gr.update(value="**Viewing:** <span style='color:red;'>Checkpoint</span>"), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), "Checkpoint", gr.update(), gr.update(interactive=True)


    # Combine selections from both checkboxes
    sections_to_save = set()
    if original_selected:
        sections_to_save.update(original_selected)
    if generated_selected:
        sections_to_save.update(generated_selected)
    
    # Only save what user actually selected
    for section in sections_to_save:
        if section in current_drafts:
            _save_section_to_checkpoint(section, current_drafts[section])
    
    # Count how many selected
    new_log, status_update = append_status(current_log, f"✅ Accepted {len(sections_to_save)} drafts. Unselected drafts discarded.")
    new_epoch = (create_epoch or 0) + 1
    
    # Get fresh content for viewer (checkpoint content)
    viewer_val = H.editor_get_section_content(current_section) or ""

    # ALWAYS close the panel and clear drafts
    return (
        gr.update(visible=False), # Hide panel
        status_update,
        new_log,
        new_epoch,
        {}, # Clear ALL drafts
        gr.update(visible=True), # status_row
        gr.update(value="**Viewing:** <span style='color:red;'>Checkpoint</span>"), # status_label
        gr.update(visible=False), # btn_checkpoint - HIDDEN
        gr.update(visible=False), # btn_draft
        gr.update(visible=False), # btn_diff
        "Checkpoint", # current_view_state
        gr.update(value=viewer_val), # Update viewer
        viewer_val, # Update current_md
        gr.update(interactive=True) # mode_radio - ENABLED
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
    
    edited_section = plan.get("edited_section", section)
    diff_data = plan.get("diff_data", {})
    impact_data = plan.get("impact_data", {})
    
    # Prepare initial UI updates
    # Use edited_section as the source of truth for the original draft
    generated_drafts = _get_generated_drafts_list(plan, drafts, edited_section)
    
    yield (
        gr.update(visible=False), # Hide draft panel during regen
        gr.update(choices=[edited_section], value=[edited_section]), # original_draft_checkbox
        gr.update(choices=generated_drafts, value=generated_drafts), # generated_drafts_list
        status_update,
        new_log,
        current_epoch,
        drafts,
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
            # Update drafts with NEW values for regenerated sections
            drafts.update(pipeline_drafts)
            
            # Update generated drafts list
            generated_drafts = _get_generated_drafts_list(plan, drafts, edited_section)
            
            yield (
                gr.update(visible=False),
                gr.update(choices=[edited_section], value=[edited_section]), # original_draft_checkbox
                gr.update(choices=generated_drafts, value=generated_drafts), # generated_drafts_list
                gr.update(value=new_log, visible=True),
                new_log,
                current_epoch,
                drafts,
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
    generated_drafts = _get_generated_drafts_list(plan, drafts, edited_section)

    yield (
        gr.update(visible=True), # Show panel again
        gr.update(choices=[edited_section], value=[edited_section]), # original_draft_checkbox
        gr.update(choices=generated_drafts, value=generated_drafts), # generated_drafts_list
        status_update,
        new_log,
        current_epoch,
        drafts,
        gr.update(visible=True), # status_row
        gr.update(visible=False) # Hide stop button
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
        gr.update(choices=[], value=[]), # clear generated_drafts_list
        {}, # clear drafts
        gr.update(visible=True), # status_row
        gr.update(value="**Viewing:** <span style='color:red;'>Checkpoint</span>"), # status_label
        gr.update(interactive=True), # btn_checkpoint
        gr.update(visible=False), # btn_draft
        gr.update(visible=False), # btn_diff
        "Checkpoint" # current_view_state
    )

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
    msg, plan = H.editor_validate(section, text_to_validate)
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

def create_validate_ui():
    """Create UI components for Validation and Draft Review."""
    # Validation Result
    validation_title = gr.Markdown("🔎 **Validation Result**", visible=False)
    validation_box = gr.Markdown(
        value="Validation results will appear here after confirming edits.",
        height=400,
        visible=False,
    )

    with gr.Row(elem_classes=["validation-row"]):
        apply_updates_btn = gr.Button("✅ Apply", scale=1, min_width=0, visible=False)
        stop_updates_btn = gr.Button("🛑 Stop", variant="stop", scale=1, min_width=0, visible=False)
        regenerate_btn = gr.Button("🔄 Regenerate", scale=1, min_width=0, visible=False)
    
    # Draft Review Panel
    with gr.Column(visible=False) as draft_review_panel:
        gr.Markdown("### 📝 Draft Review")
        
        # Original Draft (the manually edited section) - now a checkbox
        gr.Markdown("**Original Draft**")
        original_draft_checkbox = gr.CheckboxGroup(
            label="Originally Edited Section",
            choices=[],
            value=[],
            interactive=True
        )
        
        # Auto-Generated Drafts (impacted sections)
        gr.Markdown("**Auto-Generated Drafts**")
        generated_drafts_list = gr.CheckboxGroup(
            label="AI-Generated Sections",
            choices=[],
            value=[],
            interactive=True
        )
        
        with gr.Row():
            btn_draft_accept_all = gr.Button("✅ Accept All", size="sm", variant="primary", scale=1, min_width=0)
            btn_draft_revert = gr.Button("❌ Revert All", size="sm", variant="stop", scale=1, min_width=0)
        with gr.Row():
            btn_draft_accept_selected = gr.Button("✔️ Accept Selected", size="sm", scale=1, min_width=0, interactive=False)
            btn_draft_regenerate = gr.Button("🔄 Regenerate Selected", size="sm", scale=1, min_width=0, interactive=False)

    with gr.Row(elem_classes=["validation-row"]):
        continue_btn = gr.Button("🔁 Back", scale=1, min_width=0, visible=False)
        discard2_btn = gr.Button("🗑️ Discard", scale=1, min_width=0, visible=False)
        
    return validation_title, validation_box, apply_updates_btn, stop_updates_btn, regenerate_btn, draft_review_panel, original_draft_checkbox, generated_drafts_list, btn_draft_accept_all, btn_draft_revert, btn_draft_accept_selected, btn_draft_regenerate, continue_btn, discard2_btn

def create_validate_handlers(components, states):
    """Wire events for Validation and Draft Review components."""
    apply_updates_btn = components["apply_updates_btn"]
    stop_updates_btn = components["stop_updates_btn"]
    regenerate_btn = components["regenerate_btn"]
    continue_btn = components["continue_btn"]
    discard2_btn = components["discard2_btn"]
    btn_draft_accept_all = components["btn_draft_accept_all"]
    btn_draft_revert = components["btn_draft_revert"]
    btn_draft_accept_selected = components["btn_draft_accept_selected"]
    btn_draft_regenerate = components["btn_draft_regenerate"]
    original_draft_checkbox = components["original_draft_checkbox"]
    generated_drafts_list = components["generated_drafts_list"]
    
    # Shared components
    section_dropdown = components["section_dropdown"]
    editor_tb = components["editor_tb"]
    pending_plan = states["pending_plan"]
    status_log = states["status_log"]
    create_sections_epoch = states["create_sections_epoch"]
    mode_radio = components["mode_radio"]
    current_md = states["current_md"]
    current_drafts = states["current_drafts"]
    selected_section = states["selected_section"]
    
    apply_updates_btn.click(
        fn=apply_updates,
        inputs=[section_dropdown, editor_tb, pending_plan, status_log, create_sections_epoch, mode_radio, current_md, current_drafts],
        outputs=[
            components["viewer_md"], components["status_strip"],
            editor_tb,
            components["validation_title"], components["validation_box"],
            apply_updates_btn, stop_updates_btn, regenerate_btn, continue_btn, discard2_btn,
            components["start_edit_btn"],
            components["rewrite_section"],
            mode_radio, section_dropdown,
            current_md,  # update current_md state
            status_log,
            create_sections_epoch,  # bump create_sections_epoch to notify Create tab
            components["draft_review_panel"], # Added
            original_draft_checkbox, # Added
            generated_drafts_list, # Added
            current_drafts, # Added
            components["status_row"], # Added
            components["status_label"], # Added
            components["btn_checkpoint"], # Added
            components["btn_draft"], # Added
            components["btn_diff"], # Added
            states["current_view_state"], # Added
        ],
        queue=True,
    )

    stop_updates_btn.click(
        fn=request_stop,
        inputs=None,
        outputs=[stop_updates_btn],
        queue=False
    )
    
    continue_btn.click(
        fn=components["_continue_edit_dispatcher"], # Passed from main file
        inputs=[selected_section, status_log, mode_radio, current_md],
        outputs=[
            components["validation_title"], components["validation_box"],
            apply_updates_btn, regenerate_btn, continue_btn, discard2_btn,
            components["confirm_btn"], components["discard_btn"], components["force_edit_btn"],
            components["rewrite_section"],
            components["viewer_md"],
            editor_tb,
            mode_radio, section_dropdown,
            components["status_strip"],
            status_log,
            components["chat_section"], # Added output
            components["status_row"], # Added
        ],
    )

    discard2_btn.click(
        fn=discard_from_validate,
        inputs=[selected_section, status_log],
        outputs=[
            components["viewer_md"], editor_tb, components["validation_box"], pending_plan,
            components["validation_title"],
            apply_updates_btn, regenerate_btn, continue_btn, discard2_btn,
            components["start_edit_btn"],
            components["confirm_btn"], components["discard_btn"], components["force_edit_btn"],
            components["rewrite_section"],
            mode_radio, section_dropdown, components["status_strip"],
            status_log,
            current_md,
            components["draft_review_panel"], # Added
            generated_drafts_list, # Added
            current_drafts, # Added
            components["status_row"], # Added: show status row
            components["status_label"], # Added
            components["btn_checkpoint"], # Added
            components["btn_draft"], # Added
            components["btn_diff"], # Added
            states["current_view_state"], # Added
        ],
    )

    regenerate_btn.click(
        fn=regenerate_dispatcher,
        inputs=[selected_section, editor_tb, status_log, mode_radio, current_md],
        outputs=[
            components["validation_box"],
            pending_plan,
            components["validation_title"],
            apply_updates_btn,
            regenerate_btn,
            continue_btn,
            discard2_btn,
            components["status_strip"],
            status_log,
        ],
        queue=True,
        show_progress=False,
    )
    
    # Draft Review Handlers
    btn_draft_accept_all.click(
        fn=draft_accept_all,
        inputs=[selected_section, current_drafts, status_log, create_sections_epoch],
        outputs=[components["draft_review_panel"], components["status_strip"], status_log, create_sections_epoch, current_drafts, components["status_row"], components["status_label"], components["btn_checkpoint"], components["btn_draft"], components["btn_diff"], states["current_view_state"], components["viewer_md"], current_md, mode_radio]
    )
    
    btn_draft_revert.click(
        fn=draft_revert_all,
        inputs=[selected_section, status_log],
        outputs=[components["draft_review_panel"], components["status_strip"], status_log, current_drafts, components["status_row"], components["status_label"], components["btn_checkpoint"], components["btn_draft"], components["btn_diff"], states["current_view_state"], components["viewer_md"], current_md, mode_radio]
    )
    
    btn_draft_accept_selected.click(
        fn=draft_accept_selected,
        inputs=[selected_section, original_draft_checkbox, generated_drafts_list, current_drafts, status_log, create_sections_epoch],
        outputs=[components["draft_review_panel"], components["status_strip"], status_log, create_sections_epoch, current_drafts, components["status_row"], components["status_label"], components["btn_checkpoint"], components["btn_draft"], components["btn_diff"], states["current_view_state"], components["viewer_md"], current_md, mode_radio]
    )
    
    btn_draft_regenerate.click(
        fn=draft_regenerate_selected,
        inputs=[generated_drafts_list, current_drafts, pending_plan, selected_section, status_log, create_sections_epoch],
        outputs=[components["draft_review_panel"], original_draft_checkbox, generated_drafts_list, components["status_strip"], status_log, create_sections_epoch, current_drafts, components["status_row"], stop_updates_btn],
        queue=True
    )
    
    # Change handlers for checkboxes to enable/disable buttons
    original_draft_checkbox.change(
        fn=update_draft_buttons,
        inputs=[original_draft_checkbox, generated_drafts_list],
        outputs=[btn_draft_accept_selected, btn_draft_regenerate]
    )
    
    generated_drafts_list.change(
        fn=update_draft_buttons,
        inputs=[original_draft_checkbox, generated_drafts_list],
        outputs=[btn_draft_accept_selected, btn_draft_regenerate]
    )
