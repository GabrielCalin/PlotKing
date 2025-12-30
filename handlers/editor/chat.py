# ui/tabs/editor/chat.py
import gradio as gr
from handlers.editor.validate_commons import editor_validate
from handlers.editor.utils import append_status
from state.drafts_manager import DraftsManager, DraftType
from handlers.editor.constants import Components, States
from llm.chat_editor.llm import call_llm_chat
from state.checkpoint_manager import get_section_content, save_section

def chat_handler(section, message, history, current_log):
    """
    Handles the chat interaction with the Plot King.
    Uses OpenAI-style messages format: [{'role': 'user', 'content': '...'}, ...]
    """
    from state.overall_state import get_current_section_content
    from state.checkpoint_manager import get_section_content
    
    # Get current and initial content
    # initial_text = checkpoint only (reference for LLM)
    # current_text = with draft priority (active draft)
    initial_text = get_section_content(section) or ""
    current_text = get_current_section_content(section)
    
    if not message:
        return (
            gr.update(value=""), # clear input
            history,
            history, # chatbot update
            gr.update(), # viewer_md
            gr.update(), # chat_actions_row_1
            gr.update(), # chat_discard_btn
            gr.update(), # chat_force_edit_btn
            gr.update(), # chat_actions_row_2
            gr.update(), # chat_validate_btn
            gr.update(), # chat_keep_draft_btn
            current_log,
            gr.update(), # status_strip
            gr.update(), # chat_input (no change)
            gr.update(), # chat_clear_btn (no change)
            gr.update(), # status_row
            gr.update(), # status_label
            gr.update(), # btn_checkpoint
            gr.update(), # btn_draft
            gr.update(), # btn_diff
            "Checkpoint", # current_view_state
            gr.update(), # mode_radio (no change)
            gr.update(), # btn_undo - unchanged
            gr.update(), # btn_redo - unchanged
        )

    # Append user message to history
    new_history = history + [{"role": "user", "content": message}]
    
    new_log, status_update = append_status(current_log, f"💬 ({section}) Asking Plot King...")
    
    # Yield loading state
    yield (
        gr.update(value="", interactive=False), # clear input and disable
        new_history,
        new_history, # chatbot update
        gr.update(), # viewer_md
        gr.update(), # chat_actions_row_1
        gr.update(), # chat_discard_btn
        gr.update(), # chat_force_edit_btn
        gr.update(), # chat_actions_row_2
        gr.update(), # chat_validate_btn
        gr.update(), # chat_keep_draft_btn
        new_log,
        status_update,
        gr.update(interactive=False), # chat_input disable
        gr.update(interactive=False), # chat_clear_btn disable
        gr.update(), # status_row
        gr.update(), # status_label
        gr.update(), # btn_checkpoint
        gr.update(), # btn_draft
        gr.update(), # btn_diff
        "Checkpoint", # current_view_state
        gr.update(), # mode_radio (no change)
        gr.update(), # btn_undo - unchanged
        gr.update(), # btn_redo - unchanged
    )

    # Call LLM
    try:
        # Pass the full history (including the new message) to the LLM
        # The LLM step expects a list of dicts, which matches our new format
        result = call_llm_chat(
            section_name=section,
            initial_content=initial_text,
            current_content=current_text,
            conversation_history=new_history, # Pass full history including current msg
            user_message=message # Still pass this if the LLM step treats it specially, but usually history is enough
        )
        
        response_text = result.get("response", "I'm speechless!")
        new_content = result.get("new_content")
        
        # Append bot response to history
        new_history.append({"role": "assistant", "content": response_text})
        
        if new_content:
            # Edits were made - create draft and show status_row
            drafts_mgr = DraftsManager()
            drafts_mgr.add_chat(section, new_content)
            
            # Calculate undo/redo visibility - check if undo stack exists for this CHAT draft
            # Note: redo is always False when creating a new draft, as redo stack is cleared on new creation
            from state.undo_manager import UndoManager
            um = UndoManager()
            undo_visible, redo_visible, undo_icon, redo_icon, _ = um.get_undo_redo_state(section, DraftType.CHAT.value, True)
            redo_visible = False  # Redo stack is cleared when creating a new draft
            
            final_log, final_status = append_status(new_log, f"✅ ({section}) Plot King made edits.")
            draft_display_name = DraftsManager.get_display_name(DraftType.CHAT.value)
            yield (
                gr.update(value="", interactive=True),
                new_history,
                new_history, # chatbot update
                gr.update(value=new_content), # viewer_md updated with new content
                gr.update(visible=True), # chat_actions_row_1
                gr.update(visible=True), # chat_discard_btn
                gr.update(visible=True), # chat_force_edit_btn
                gr.update(visible=True), # chat_actions_row_2
                gr.update(visible=True), # chat_validate_btn
                gr.update(visible=True), # chat_keep_draft_btn
                final_log,
                final_status,
                gr.update(interactive=True), # chat_input enable
                gr.update(interactive=True), # chat_clear_btn enable
                gr.update(visible=True), # status_row - show
                gr.update(value=f"**Viewing:** <span style='color:red;'>{draft_display_name}</span>"), # status_label - show Draft
                gr.update(visible=True, interactive=True), # btn_checkpoint - visible
                gr.update(visible=True, interactive=True), # btn_draft
                gr.update(visible=True, interactive=True), # btn_diff
                "Draft", # current_view_state
                gr.update(interactive=False), # mode_radio - DISABLED
                gr.update(visible=undo_visible, value=undo_icon), # btn_undo - show only if undo stack exists
                gr.update(visible=redo_visible, value=redo_icon), # btn_redo - show only if redo stack exists
            )
        else:
            # No edits, just chat
            final_log, final_status = append_status(new_log, f"✅ ({section}) Plot King replied.")
            yield (
                gr.update(value="", interactive=True),
                new_history,
                new_history, # chatbot update
                gr.update(), # viewer_md unchanged
                gr.update(), # chat_actions_row_1
                gr.update(), # chat_discard_btn
                gr.update(), # chat_force_edit_btn
                gr.update(), # chat_actions_row_2
                gr.update(), # chat_validate_btn
                gr.update(), # chat_keep_draft_btn
                final_log,
                final_status,
                gr.update(interactive=True), # chat_input enable
                gr.update(interactive=True), # chat_clear_btn enable
                gr.update(), # status_row - unchanged
                gr.update(), # status_label - unchanged
                gr.update(), # btn_checkpoint - unchanged
                gr.update(), # btn_draft - unchanged
                gr.update(), # btn_diff - unchanged
                "Checkpoint", # current_view_state - unchanged
                gr.update(), # mode_radio - unchanged
                gr.update(), # btn_undo - unchanged
                gr.update(), # btn_redo - unchanged
            )
            
    except Exception as e:
        error_msg = f"Error talking to Plot King: {str(e)}"
        new_history.append({"role": "assistant", "content": error_msg})
        final_log, final_status = append_status(new_log, f"❌ ({section}) Chat error: {str(e)}")
        yield (
            gr.update(value="", interactive=True),
            new_history,
            new_history, # chatbot update
            gr.update(),
            gr.update(), # chat_actions_row_1
            gr.update(), # chat_discard_btn
            gr.update(), # chat_force_edit_btn
            gr.update(), # chat_actions_row_2
            gr.update(), # chat_validate_btn
            gr.update(), # chat_keep_draft_btn
            final_log,
            final_status,
            gr.update(interactive=True), # chat_input enable
            gr.update(interactive=True), # chat_clear_btn enable
            gr.update(), # status_row - unchanged
            gr.update(), # status_label - unchanged
            gr.update(), # btn_checkpoint - unchanged
            gr.update(), # btn_draft - unchanged
            gr.update(), # btn_diff - unchanged
            "Checkpoint", # current_view_state - unchanged
            gr.update(), # mode_radio - unchanged
            gr.update(), # btn_undo - unchanged
            gr.update(), # btn_redo - unchanged
        )


def clear_chat(section, current_log):
    """Resets the chat history to the initial greeting."""
    from ui.tabs.editor.chat_ui import PLOT_KING_GREETING
    initial_greeting = [{"role": "assistant", "content": PLOT_KING_GREETING}]
    new_log, status_update = append_status(current_log, f"🧹 ({section}) Chat cleared.")
    return initial_greeting, new_log, status_update, initial_greeting



def validate_handler(section, current_log):
    """
    Starts validation for the chat edits. Hides Chat UI.
    Uses get_current_section_content to get draft content.
    """
    from state.overall_state import get_current_section_content
    draft_to_validate = get_current_section_content(section)
    
    new_log, status_update = append_status(current_log, f"🔍 ({section}) Validation started (from Chat).")
    
    # Hide Chat UI, Show Validation UI
    yield (
        gr.update(visible=False), # chat_group
        gr.update(visible=True), # validation_title
        gr.update(value="🔄 Validating...", visible=True), # validation_box
        gr.update(visible=True), # validation_section
        gr.update(visible=False), # apply_updates_btn
        gr.update(visible=False), # regenerate_btn
        gr.update(visible=False), # continue_btn
        gr.update(visible=False), # discard2_btn
        gr.update(), # viewer_md - NO CHANGE
        new_log,
        status_update,
        {}, # pending_plan - placeholder to indicate validation is running
        gr.update(interactive=False), # mode_radio - DISABLED
        gr.update(visible=False), # btn_undo - hide during validation
        gr.update(visible=False), # btn_redo - hide during validation
    )
    
    msg, plan = editor_validate(section, draft_to_validate)
    final_log, final_status = append_status(new_log, f"✅ ({section}) Validation completed.")
    
    yield (
        gr.update(visible=False), # chat_group
        gr.update(visible=True), # validation_title
        gr.update(value=msg, visible=True), # validation_box
        gr.update(visible=True), # validation_section
        gr.update(visible=True), # apply_updates_btn
        gr.update(visible=True), # regenerate_btn
        gr.update(visible=True), # continue_btn
        gr.update(visible=True), # discard2_btn
        gr.update(), # viewer_md - NO CHANGE
        final_log,
        final_status,
        plan, # pending_plan
        gr.update(interactive=False), # mode_radio - DISABLED
        gr.update(visible=False), # btn_undo - hide during validation
        gr.update(visible=False), # btn_redo - hide during validation
    )

def discard_handler(section, current_log):
    """
    Discards Chat draft. Falls back to USER draft if exists, otherwise Checkpoint.
    """
    drafts_manager = DraftsManager()
    
    # 1. Remove ONLY Chat draft
    if drafts_manager.has_type(section, DraftType.CHAT.value):
        drafts_manager.remove(section, DraftType.CHAT.value)
        msg_text = f"🗑️ ({section}) Chat edits discarded."
    else:
        msg_text = f"⚠️ ({section}) No chat edits found."
        
    new_log, status_update = append_status(current_log, msg_text)

    # 2. Determine fallback content
    user_draft_content = drafts_manager.get_content(section, DraftType.USER.value)
    
    # Calculate undo/redo visibility based on what remains after discard
    from state.undo_manager import UndoManager
    um = UndoManager()
    
    if user_draft_content:
        # Fallback to User Draft
        updated_text = user_draft_content
        draft_display_name = DraftsManager.get_display_name(DraftType.USER.value)
        mode_label = f"**Viewing:** <span style='color:red;'>{draft_display_name}</span>"
        view_state = "Draft"
        btns_visible = True
        undo_visible, redo_visible, undo_icon, redo_icon, _ = um.get_undo_redo_state(section, DraftType.USER.value, True)
        
    else:
        # Fallback to Checkpoint - no undo/redo available
        updated_text = get_section_content(section) or ""
        mode_label = "**Viewing:** <span style='color:red;'>Checkpoint</span>"
        view_state = "Checkpoint"
        btns_visible = False
        undo_visible, redo_visible, undo_icon, redo_icon, _ = um.get_undo_redo_state(section, None, False)
    
    return (
        gr.update(value=updated_text), # viewer_md
        gr.update(visible=False), # chat_actions_row_1
        gr.update(visible=False), # chat_discard_btn
        gr.update(visible=False), # chat_force_edit_btn
        gr.update(visible=False), # chat_actions_row_2
        gr.update(visible=False), # chat_validate_btn
        gr.update(visible=False), # chat_keep_draft_btn
        new_log,
        status_update,
        gr.update(visible=True), # status_row - always visible in Chat
        gr.update(value=mode_label), # status_label
        gr.update(visible=btns_visible), # btn_checkpoint
        gr.update(visible=btns_visible, interactive=btns_visible), # btn_draft
        gr.update(visible=btns_visible, interactive=btns_visible), # btn_diff
        view_state, # current_view_state
        gr.update(interactive=True), # mode_radio
        gr.update(visible=undo_visible, value=undo_icon), # btn_undo - hide if no draft
        gr.update(visible=redo_visible, value=redo_icon), # btn_redo - hide if no draft
    )

def force_edit_handler(section, current_log, create_epoch):
    """
    Force saves the chat edits to checkpoint. For fills, inserts chapter and shifts.
    """
    from state.overall_state import get_current_section_content
    from handlers.editor.utils import force_edit_common_handler
    
    current_text = get_current_section_content(section)
    updated_text, msg, dropdown_update, new_log, status_update = force_edit_common_handler(section, current_text, current_log)
    
    if updated_text is None:
        updated_text = current_text
        new_log, status_update = append_status(current_log, f"⚡ ({section}) Synced (forced from Chat).")
    
    new_create_epoch = (create_epoch or 0) + 1
    
    return (
        gr.update(value=updated_text), # viewer_md
        gr.update(visible=False), # chat_actions_row_1
        gr.update(visible=False), # chat_discard_btn
        gr.update(visible=False), # chat_force_edit_btn
        gr.update(visible=False), # chat_actions_row_2
        gr.update(visible=False), # chat_validate_btn
        gr.update(visible=False), # chat_keep_draft_btn
        new_log,
        status_update,
        new_create_epoch,
        gr.update(visible=True), # status_row - show
        gr.update(value="**Viewing:** <span style='color:red;'>Checkpoint</span>"), # status_label - show Checkpoint
        gr.update(visible=False), # btn_checkpoint - hide (no draft = no point showing C only)
        gr.update(visible=False), # btn_draft - hide
        gr.update(visible=False), # btn_diff - hide
        "Checkpoint", # current_view_state
        gr.update(interactive=True), # mode_radio - ENABLED
        dropdown_update, # section_dropdown update
        gr.update(visible=False), # btn_undo - hide
        gr.update(visible=False), # btn_redo - hide
    )

def continue_edit(section, current_log):
    """Return to editing mode. If Chat mode, return to Chat Section."""
    new_log, status_update = append_status(current_log, f"🔁 ({section}) Continue chatting.")
    
    # Calculate undo/redo visibility for CHAT draft
    from state.drafts_manager import DraftsManager, DraftType
    from state.undo_manager import UndoManager
    
    drafts_mgr = DraftsManager()
    has_chat_draft = drafts_mgr.has_type(section, DraftType.CHAT.value)
    
    um = UndoManager()
    undo_visible, redo_visible, undo_icon, redo_icon, _ = um.get_undo_redo_state(
        section, DraftType.CHAT.value if has_chat_draft else None, has_chat_draft
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
        gr.update(),  # viewer_md - don't update (user might be viewing diff)
        gr.update(visible=False),   # hide editor_tb
        gr.update(value="Chat", interactive=False), # unlock Mode - DISABLED (draft exists)
        gr.update(interactive=True), # unlock Section
        status_update,
        new_log,
        gr.update(visible=True),    # 17. SHOW Chat Section
        gr.update(visible=True),    # 18. status_row - show (draft exists after validate)
        gr.update(visible=False),   # 19. hide manual keep draft
        gr.update(visible=False),   # 20. hide rewrite keep draft
        gr.update(visible=True),    # 21. SHOW Chat Keep Draft
        gr.update(visible=False),   # 22. hide view actions row
        None,  # 23. pending_plan - clear plan when going back
        gr.update(visible=undo_visible, value=undo_icon), # btn_undo - show if available
        gr.update(visible=redo_visible, value=redo_icon), # btn_redo - show if available
    )

