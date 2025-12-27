from handlers.editor.utils import append_status
import gradio as gr
from state.drafts_manager import DraftsManager
from state.checkpoint_manager import get_section_content, save_section

def discard_draft_handler(section, status_log):
    """Discard USER draft and revert view to Checkpoint content."""
    if not section:
        return gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), status_log, gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
        
    drafts_mgr = DraftsManager()
    if drafts_mgr.has(section):
        drafts_mgr.remove(section)
        msg = f"🗑️ Discarded draft for **{section}**."
    else:
        msg = "No draft to discard."
        
    new_log, status_update = append_status(status_log, msg)
    
    # Reload checkpoint content
    original_text = get_section_content(section) or ""
    
    return (
        gr.update(value=original_text), # Viewer MD
        gr.update(value="**Viewing:** <span style='color:red;'>Checkpoint</span>"), # Status Label
        "Checkpoint", # View State
        gr.update(visible=False), # Checkpoint Btn
        gr.update(visible=False), # Draft Btn
        gr.update(visible=False), # Diff Btn
        new_log,
        status_update,
        gr.update(visible=False),  # view_actions_row update
        gr.update(visible=False), # btn_undo - hide
        gr.update(visible=False), # btn_redo - hide
    )

def force_edit_draft_handler(section, status_log, create_sections_epoch):
    """Write draft content directly to Checkpoint and remove draft."""
    if not section:
        return gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), status_log, gr.update(), create_sections_epoch, gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
        
    drafts_mgr = DraftsManager()
    content = drafts_mgr.get_content(section)
    
    if not content:
        msg = f"⚠️ No draft found for **{section}**."
        new_log, status_update = append_status(status_log, msg)
        # Get checkpoint content as fallback
        checkpoint_content = get_section_content(section) or ""
        return gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), new_log, status_update, create_sections_epoch, gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
    
    # Save to checkpoint
    save_section(section, content)
    drafts_mgr.remove(section) # Remove draft after saving
    
    msg = f"⚡ Force Edited **{section}**. Draft saved to checkpoint."
    new_log, status_update = append_status(status_log, msg)
    
    # Trigger refresh
    new_epoch = (create_sections_epoch or 0) + 1
    
    return (
        gr.update(value=content), # Viewer MD
        gr.update(value="**Viewing:** <span style='color:red;'>Checkpoint</span>"), # Status Label
        "Checkpoint", # View State
        gr.update(visible=False), # Checkpoint Btn
        gr.update(visible=False), # Draft Btn
        gr.update(visible=False), # Diff Btn
        new_log,
        status_update,
        new_epoch,
        gr.update(visible=False), # view_actions_row
        gr.update(visible=False), # btn_undo - hide
        gr.update(visible=False), # btn_redo - hide
    )

def validate_draft_handler(section, current_log):
    """Trigger validation using the USER draft content from View mode."""
    from handlers.editor.validate_commons import editor_validate
    
    from state.drafts_manager import DraftType
    
    if not section:
        return [gr.update()] * 13 # Fallback
        
    drafts_mgr = DraftsManager()
    if not drafts_mgr.has_type(section, DraftType.USER.value):
        new_log, status_update = append_status(current_log, f"⚠️ No user draft found for validation in {section}.")
        return [gr.update(), None, gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), status_update, new_log, gr.update()]

    draft_content = drafts_mgr.get_content(section, DraftType.USER.value)
    
    # Initial status
    new_log, status_update = append_status(current_log, f"🔎 ({section}) Validating user draft...")
    
    # Yield loading state immediately
    yield (
        gr.update(value="🔄 Validating...", visible=True), # validation_box
        {}, # pending_plan - placeholder to indicate validation is running
        gr.update(visible=True), # validation_title
        gr.update(visible=True), # validation_section
        gr.update(visible=False), # apply_updates_btn
        gr.update(visible=False), # regenerate_btn
        gr.update(visible=False), # continue_btn
        gr.update(visible=False), # discard2_btn
        gr.update(), # viewer_md
        gr.update(visible=False), # editor_tb
        gr.update(interactive=False), # mode_radio
        gr.update(interactive=False), # section_dropdown
        status_update, # status_strip
        new_log, # status_log
        gr.update(visible=False), # view_actions_row (hide immediately)
        gr.update(visible=False), # btn_undo - hide during validation
        gr.update(visible=False), # btn_redo - hide during validation
    )

    # Run validation
    msg, plan = editor_validate(section, draft_content)
    final_log, final_status = append_status(new_log, f"✅ ({section}) Validation completed.")
    
    # Preparation for Validation Box
    yield (
        gr.update(value=msg, visible=True), # validation_box
        plan, # pending_plan
        gr.update(visible=True), # validation_title
        gr.update(visible=True), # validation_section
        gr.update(visible=True), # apply_updates_btn
        gr.update(visible=True), # regenerate_btn
        gr.update(visible=True), # continue_btn
        gr.update(visible=True), # discard2_btn
        gr.update(), # viewer_md (stay as is)
        gr.update(visible=False), # editor_tb
        gr.update(interactive=False), # mode_radio (lock while validating)
        gr.update(interactive=False), # section_dropdown
        final_status, # status_strip
        final_log, # status_log
        gr.update(visible=False), # view_actions_row (hide while looking at validation results)
        gr.update(visible=False), # btn_undo - hide during validation
        gr.update(visible=False), # btn_redo - hide during validation
    )
    
def continue_edit(section, current_log):
    """Return to View mode after validation."""
    new_log, status_update = append_status(current_log, f"🔁 ({section}) Return to view.")
    
    from state.drafts_manager import DraftsManager, DraftType
    from state.undo_manager import UndoManager
    
    drafts_mgr = DraftsManager()
    is_user_draft = drafts_mgr.has_type(section, DraftType.USER.value)
    
    # Calculate undo/redo visibility for the draft that remains
    um = UndoManager()
    draft_type = None
    if is_user_draft:
        draft_type = DraftType.USER.value
    elif drafts_mgr.has(section):
        draft_type = drafts_mgr.get_type(section)
    
    undo_visible, redo_visible, undo_icon, redo_icon, _ = um.get_undo_redo_state(
        section, draft_type, draft_type is not None
    )

    return (
        gr.update(visible=False),   # hide Validation Title
        gr.update(visible=False),   # hide Validation Box
        gr.update(visible=False),   # hide Validation Section
        gr.update(visible=False),   # hide Apply Updates
        gr.update(visible=False),   # hide Regenerate
        gr.update(visible=False),   # hide Continue Editing
        gr.update(visible=False),   # hide Discard2
        gr.update(visible=False),   # hide Validate (Manual)
        gr.update(visible=False),   # hide Discard (Manual)
        gr.update(visible=False),   # hide Force Edit (Manual)
        gr.update(visible=False),   # hide Manual Section
        gr.update(visible=False),   # hide Rewrite Section
        gr.update(visible=True),    # SHOW viewer_md
        gr.update(visible=False),   # hide editor_tb
        gr.update(value="View", interactive=True), # unlock Mode/Set to View
        gr.update(interactive=True), # unlock Section
        status_update,
        new_log,
        gr.update(visible=False),   # hide Chat Section
        gr.update(visible=True),    # SHOW status_row
        gr.update(visible=False),   # hide Keep Draft (Manual)
        gr.update(visible=False),   # hide rewrite keep draft
        gr.update(visible=False),   # hide chat keep draft
        gr.update(visible=is_user_draft), # SHOW view actions row if it was a user draft
        None,  # 23. pending_plan - clear plan when going back
        gr.update(visible=undo_visible, value=undo_icon), # btn_undo - show if available
        gr.update(visible=redo_visible, value=redo_icon), # btn_redo - show if available
    )
