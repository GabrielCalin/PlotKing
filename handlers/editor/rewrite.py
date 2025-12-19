import gradio as gr
from handlers.editor.validate_commons import editor_validate
from handlers.editor.rewrite_presets import REWRITE_PRESETS
from handlers.editor.utils import append_status, replace_text_with_highlight, remove_highlight, format_selected_preview, update_instructions_from_preset
from handlers.editor.constants import Components, States
from state.checkpoint_manager import get_section_content, save_section
from llm.rewrite_editor.llm import call_llm_rewrite_editor

def editor_rewrite(section, selected_text, instructions):
    """
    Rewrite selected text based on instructions using LLM.
    Returns a dict with success status and result/message.
    """
    if not selected_text:
        return {"success": False, "message": "No text selected."}
    
    full_content = get_section_content(section)
    
    context_before = ""
    context_after = ""
    
    if len(selected_text) < 50:
        try:
            idx = full_content.find(selected_text)
            if idx != -1:
                start = max(0, idx - 25)
                end = min(len(full_content), idx + len(selected_text) + 25)
                
                context_before = full_content[start:idx]
                context_after = full_content[idx + len(selected_text):end]
        except Exception:
            pass

    result = call_llm_rewrite_editor(
        section_content=full_content,
        selected_text=selected_text,
        instructions=instructions,
        context_before=context_before,
        context_after=context_after,
    )
    
    return result

def handle_text_selection(evt: gr.SelectData):
    """Handle text selection in editor_tb and store selected text and indices."""
    raw_value = evt.value if hasattr(evt, 'value') else ""
    raw_index = evt.index if hasattr(evt, 'index') else None
    
    if not raw_value or not isinstance(raw_index, (list, tuple)) or len(raw_index) != 2:
        return "", None, "", gr.update(interactive=False)

    start, end = raw_index
    
    # Calculate leading/trailing whitespace
    l_stripped = raw_value.lstrip()
    leading_spaces = len(raw_value) - len(l_stripped)
    
    stripped_value = raw_value.strip()
    trailing_spaces = len(raw_value) - len(raw_value.rstrip())
    
    # Adjust indices
    new_start = start + leading_spaces
    new_end = end - trailing_spaces
    
    # If selection was only whitespace, it becomes empty
    if not stripped_value:
        return "", None, "", gr.update(interactive=False)
        
    preview_text = format_selected_preview(stripped_value)
    return stripped_value, [new_start, new_end], preview_text, gr.update(interactive=True)

def rewrite_handler(section, selected_txt, selected_idx, instructions, current_text, current_log, original_text):
    """Handle rewrite button click - call handler and replace selected text."""
    start_idx, end_idx = selected_idx if isinstance(selected_idx, (list, tuple)) and len(selected_idx) == 2 else (None, None)
    
    original_text = get_section_content(section)
    
    new_log, status_update = append_status(current_log, f"🔄 ({section}) Rewriting selected text...")
    
    # Yield loading state
    yield (
        gr.update(visible=False),  # editor_tb
        gr.update(visible=True, value="🔄 Rewriting..."),  # viewer_md
        gr.update(visible=False),  # rewrite_validate_btn
        gr.update(visible=False),  # rewrite_discard_btn
        gr.update(visible=False),  # rewrite_force_edit_btn
        gr.update(visible=False),  # rewrite_keep_draft_btn
        gr.update(visible=False),  # rewrite_btn
        status_update,
        current_log,
        original_text,
        selected_txt,
        selected_idx,
        original_text,
    )
    
    result = editor_rewrite(section, selected_txt, instructions)
    
    if result.get("success"):
        rewritten_text = result.get("edited_text", "")
        new_text_with_highlight = replace_text_with_highlight(original_text, start_idx, end_idx, rewritten_text)
        final_log, final_status = append_status(new_log, f"✅ ({section}) Rewrite completed.")
        
        yield (
            gr.update(visible=False),  # editor_tb
            gr.update(visible=True, value=new_text_with_highlight),  # viewer_md
            gr.update(visible=True),   # rewrite_validate_btn
            gr.update(visible=True),   # rewrite_discard_btn
            gr.update(visible=True),   # rewrite_force_edit_btn
            gr.update(visible=True),   # rewrite_keep_draft_btn
            gr.update(visible=True),   # rewrite_btn
            final_status,
            final_log,
            new_text_with_highlight,
            selected_txt,
            selected_idx,
            original_text,
        )
    else:
        message = result.get("message", "Rewrite failed.")
        final_log, final_status = append_status(new_log, f"❌ ({section}) Rewrite failed: {message}")
        
        # Revert to original text (no highlights)
        yield (
            gr.update(visible=False),  # editor_tb
            gr.update(visible=True, value=original_text),  # viewer_md
            gr.update(visible=False),  # rewrite_validate_btn
            gr.update(visible=False),  # rewrite_discard_btn
            gr.update(visible=False),  # rewrite_force_edit_btn
            gr.update(visible=False),  # rewrite_keep_draft_btn
            gr.update(visible=True),   # rewrite_btn
            final_status,
            final_log,
            original_text,
            selected_txt,
            selected_idx,
            original_text,
        )

def rewrite_discard(section, current_log):
    """Discard rewrite changes - switch back to Text Box non-interactive. Always use checkpoint as source of truth."""
    new_log, status_update = append_status(current_log, f"🗑️ ({section}) Rewrite discarded.")
    clean_text = get_section_content(section) or "_Empty_"
    return (
        gr.update(visible=True, value=clean_text, interactive=False),  # editor_tb
        gr.update(visible=False, value=clean_text),  # viewer_md - resetat la textul curat din checkpoint
        gr.update(visible=False),  # rewrite_validate_btn
        gr.update(visible=False),  # rewrite_discard_btn
        gr.update(visible=False),  # rewrite_force_edit_btn
        gr.update(visible=False),  # rewrite_keep_draft_btn
        gr.update(visible=True, interactive=False),  # rewrite_btn - disabled pentru că selected_text este empty
        gr.update(value=""),  # rewrite_selected_preview
        status_update,  # status_strip
        new_log,  # status_log
        "",  # selected_text
        None,  # selected_indices
        clean_text,  # current_md - resetat la textul din checkpoint
        clean_text,  # original_text_before_rewrite - resetat la textul din checkpoint
    )

def rewrite_force_edit(section, draft_with_highlight, current_log, create_epoch):
    """Force edit with rewritten text - remove highlight and update checkpoint."""
    draft_clean = remove_highlight(draft_with_highlight)
    save_section(section, draft_clean)
    updated_text = draft_clean
    new_log, status_update = append_status(current_log, f"⚡ ({section}) Synced (forced from rewrite).")
    new_create_epoch = (create_epoch or 0) + 1
    return (
        gr.update(value=updated_text, visible=True),  # viewer_md
        status_update,  # status_strip
        gr.update(visible=False),  # editor_tb
        gr.update(visible=False),  # validation_title
        gr.update(visible=False),  # validation_box
        gr.update(visible=False),  # apply_updates_btn
        gr.update(visible=False),  # regenerate_btn
        gr.update(visible=False),  # continue_btn
        gr.update(visible=False),  # discard2_btn
        gr.update(visible=False),  # confirm_btn
        gr.update(visible=False),  # discard_btn
        gr.update(visible=False),  # force_edit_btn
        gr.update(visible=False),  # start_edit_btn
        gr.update(visible=False),  # rewrite_section
        gr.update(value="View", interactive=True),  # mode_radio
        gr.update(interactive=True),  # section_dropdown
        updated_text,  # current_md
        new_log,  # status_log
        new_create_epoch,  # create_sections_epoch
        "",  # selected_text
        None,  # selected_indices
        gr.update(visible=True), # status_row (visible)
    )

def rewrite_validate(section, draft_with_highlight, current_log):
    """Validate rewritten text - remove highlight and start validation."""
    draft_clean = remove_highlight(draft_with_highlight)
    new_log, status_update = append_status(current_log, f"🔍 ({section}) Validation started (from rewrite).")
    
    yield (
        "",  # validation_box (Markdown)
        None,  # pending_plan (State)
        gr.update(visible=True),  # validation_title (Markdown)
        gr.update(value="🔄 Validating...", visible=True),  # validation_box (Markdown)
        gr.update(visible=False),  # apply_updates_btn (Button)
        gr.update(visible=False),  # regenerate_btn (Button)
        gr.update(visible=False),  # continue_btn (Button)
        gr.update(visible=False),  # discard2_btn (Button)
        gr.update(visible=False),  # rewrite_section (Column)
        gr.update(visible=True, value=draft_with_highlight),  # viewer_md (Markdown) - keep highlights
        gr.update(interactive=False),  # editor_tb (Textbox)
        gr.update(interactive=False),  # mode_radio (Radio)
        gr.update(interactive=False),  # section_dropdown (Dropdown)
        gr.update(value=new_log, visible=True),  # status_strip (Textbox)
        new_log,  # status_log (State)
        gr.update(visible=False), # status_row (hidden)
        draft_with_highlight # 16. current_md state update (WITH HIGHLIGHTS)
    )
    
    msg, plan = editor_validate(section, draft_clean)
    final_log, _ = append_status(new_log, f"✅ ({section}) Validation completed.")
    
    yield (
        msg,  # validation_box (Markdown)
        plan,  # pending_plan (State)
        gr.update(visible=True),  # validation_title (Markdown)
        gr.update(value=msg, visible=True),  # validation_box (Markdown)
        gr.update(visible=True),  # apply_updates_btn (Button)
        gr.update(visible=True),  # regenerate_btn (Button)
        gr.update(visible=True),  # continue_btn (Button)
        gr.update(visible=True),  # discard2_btn (Button)
        gr.update(visible=False),  # rewrite_section (Column)
        gr.update(visible=True, value=draft_with_highlight),  # viewer_md (Markdown) - keep highlights
        gr.update(interactive=False),  # editor_tb (Textbox)
        gr.update(interactive=False),  # mode_radio (Radio)
        gr.update(interactive=False),  # section_dropdown (Dropdown)
        gr.update(value=final_log, visible=True),  # status_strip (Textbox)
        final_log,  # status_log (State)
        gr.update(visible=False), # status_row (hidden)
        draft_with_highlight # 16. current_md state update (WITH HIGHLIGHTS)
    )

def confirm_edit(section, draft, current_log):
    """Send text for validation (Rewrite mode) — shows Validation Result in place of buttons."""
    # This is essentially the same as rewrite_validate but called from the main confirm button if needed
    # But in Rewrite mode, we usually use the specific Rewrite Validate button.
    # However, if the user clicks the main Validate button while in Rewrite mode (if visible), we should handle it.
    # Based on the original code, confirm_edit handled both modes.
    
    # For Rewrite mode, draft is current_md (with highlights)
    return rewrite_validate(section, draft, current_log)

def continue_edit(section, current_log, current_md):
    """Return to editing mode. If Rewrite mode, return to Rewrite Section."""
    new_log, status_update = append_status(current_log, f"🔁 ({section}) Continue editing.")
    
    return (
        gr.update(visible=False),   # hide Validation Title
        gr.update(visible=False),   # hide Validation Box
        gr.update(visible=False),   # hide Apply Updates
        gr.update(visible=False),   # hide Regenerate
        gr.update(visible=False),   # hide Continue Editing
        gr.update(visible=False),   # hide Discard2
        gr.update(visible=False),   # hide Validate
        gr.update(visible=False),   # hide Discard
        gr.update(visible=False),   # hide Force Edit
        gr.update(visible=True),    # show Rewrite Section
        gr.update(visible=True, value=current_md),  # show viewer_md with highlighted text
        gr.update(visible=False),   # hide editor_tb
        gr.update(value="Rewrite", interactive=False), # keep Mode locked to Rewrite
        gr.update(interactive=False), # keep Section locked
        status_update,
        new_log,
        gr.update(visible=False),   # 17. hide Chat Section
        gr.update(visible=False),   # 18. status_row (hidden while editing)
        gr.update(visible=False),   # 19. hide manual keep draft
        gr.update(visible=True),    # 20. show Rewrite Keep Draft
        gr.update(visible=False),   # 21. hide chat keep draft
        gr.update(visible=False),   # 22. hide view actions row
    )

