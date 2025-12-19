# ui/tabs/editor/chat.py
import gradio as gr
from handlers.editor.validate_commons import editor_validate
from handlers.editor.utils import append_status
from state.drafts_manager import DraftsManager, DraftType
from handlers.editor.constants import Components, States
from llm.chat_editor.llm import call_llm_chat
from state.checkpoint_manager import get_section_content, save_section

def chat_handler(section, message, history, current_text, initial_text, current_log):
    """
    Handles the chat interaction with the Plot King.
    Uses OpenAI-style messages format: [{'role': 'user', 'content': '...'}, ...]
    """
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
            current_text, # current_md
            gr.update(), # chat_input (no change)
            gr.update(), # chat_clear_btn (no change)
            gr.update(), # status_row
            gr.update(), # status_label
            gr.update(), # btn_checkpoint
            gr.update(), # btn_draft
            gr.update(), # btn_diff
            "Checkpoint", # current_view_state
            gr.update(), # mode_radio (no change)
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
        current_text,
        gr.update(interactive=False), # chat_input disable
        gr.update(interactive=False), # chat_clear_btn disable
        gr.update(), # status_row
        gr.update(), # status_label
        gr.update(), # btn_checkpoint
        gr.update(), # btn_draft
        gr.update(), # btn_diff
        "Checkpoint", # current_view_state
        gr.update(), # mode_radio (no change)
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
            drafts_mgr.add_user_draft(section, new_content)
            
            final_log, final_status = append_status(new_log, f"✅ ({section}) Plot King made edits.")
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
                new_content, # update current_md
                gr.update(interactive=True), # chat_input enable
                gr.update(interactive=True), # chat_clear_btn enable
                gr.update(visible=True), # status_row - show
                gr.update(value="**Viewing:** <span style='color:red;'>Draft</span>"), # status_label - show Draft
                gr.update(visible=True, interactive=True), # btn_checkpoint - visible
                gr.update(visible=True, interactive=True), # btn_draft
                gr.update(visible=True, interactive=True), # btn_diff
                "Draft", # current_view_state
                gr.update(interactive=False), # mode_radio - DISABLED
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
                current_text, # current_md unchanged
                gr.update(interactive=True), # chat_input enable
                gr.update(interactive=True), # chat_clear_btn enable
                gr.update(), # status_row - unchanged
                gr.update(), # status_label - unchanged
                gr.update(), # btn_checkpoint - unchanged
                gr.update(), # btn_draft - unchanged
                gr.update(), # btn_diff - unchanged
                "Checkpoint", # current_view_state - unchanged
                gr.update(), # mode_radio - unchanged
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
            current_text,
            gr.update(interactive=True), # chat_input enable
            gr.update(interactive=True), # chat_clear_btn enable
            gr.update(), # status_row - unchanged
            gr.update(), # status_label - unchanged
            gr.update(), # btn_checkpoint - unchanged
            gr.update(), # btn_draft - unchanged
            gr.update(), # btn_diff - unchanged
            "Checkpoint", # current_view_state - unchanged
            gr.update(), # mode_radio - unchanged
        )


def clear_chat(section, current_log):
    """Resets the chat history to the initial greeting."""
    from ui.tabs.editor.chat_ui import PLOT_KING_GREETING
    initial_greeting = [{"role": "assistant", "content": PLOT_KING_GREETING}]
    new_log, status_update = append_status(current_log, f"🧹 ({section}) Chat cleared.")
    return initial_greeting, new_log, status_update, initial_greeting



def validate_handler(section, current_text, current_log):
    """
    Starts validation for the chat edits. Hides Chat UI.
    Uses existing draft from DraftsManager if available, otherwise uses current_text.
    """
    drafts_manager = DraftsManager()
    draft_to_validate = drafts_manager.get_content(section) or current_text
    
    new_log, status_update = append_status(current_log, f"🔍 ({section}) Validation started (from Chat).")
    
    # Hide Chat UI, Show Validation UI
    yield (
        gr.update(visible=False), # chat_group
        gr.update(visible=True), # validation_title
        gr.update(value="🔄 Validating...", visible=True), # validation_box
        gr.update(visible=False), # apply_updates_btn
        gr.update(visible=False), # regenerate_btn
        gr.update(visible=False), # continue_btn
        gr.update(visible=False), # discard2_btn
        gr.update(), # viewer_md - NO CHANGE
        new_log,
        status_update,
        None, # pending_plan placeholder
        gr.update(interactive=False), # mode_radio - DISABLED
    )
    
    msg, plan = editor_validate(section, draft_to_validate)
    final_log, final_status = append_status(new_log, f"✅ ({section}) Validation completed.")
    
    yield (
        gr.update(visible=False), # chat_group
        gr.update(visible=True), # validation_title
        gr.update(value=msg, visible=True), # validation_box
        gr.update(visible=True), # apply_updates_btn
        gr.update(visible=True), # regenerate_btn
        gr.update(visible=True), # continue_btn
        gr.update(visible=True), # discard2_btn
        gr.update(), # viewer_md - NO CHANGE
        final_log,
        final_status,
        plan, # pending_plan
        gr.update(interactive=False), # mode_radio - DISABLED
    )

def discard_handler(section, current_log):
    """
    Discards chat edits and reverts to checkpoint. Removes draft from DraftsManager.
    """
    drafts_manager = DraftsManager()
    if drafts_manager.has(section):
        drafts_manager.remove(section)

    clean_text = get_section_content(section) or "_Empty_"
    new_log, status_update = append_status(current_log, f"🗑️ ({section}) Chat edits discarded.")
    
    return (
        gr.update(value=clean_text), # viewer_md
        gr.update(visible=False), # chat_actions_row_1
        gr.update(visible=False), # chat_discard_btn
        gr.update(visible=False), # chat_force_edit_btn
        gr.update(visible=False), # chat_actions_row_2
        gr.update(visible=False), # chat_validate_btn
        gr.update(visible=False), # chat_keep_draft_btn
        clean_text, # current_md
        new_log,
        status_update,
        gr.update(visible=True), # status_row - show (but buttons hidden if no drafts)
        gr.update(value="**Viewing:** <span style='color:red;'>Checkpoint</span>"), # status_label - show Checkpoint
        gr.update(visible=False), # btn_checkpoint - hide (no draft = no point showing C only)
        gr.update(visible=False), # btn_draft - hide
        gr.update(visible=False), # btn_diff - hide
        "Checkpoint", # current_view_state
        gr.update(interactive=True), # mode_radio - ENABLED
    )

def force_edit_handler(section, current_text, current_log, create_epoch):
    """
    Force saves the chat edits to checkpoint.
    """
    save_section(section, current_text)
    updated_text = current_text
    new_log, status_update = append_status(current_log, f"⚡ ({section}) Synced (forced from Chat).")
    new_create_epoch = (create_epoch or 0) + 1
    
    # Remove draft for this section since changes are saved to checkpoint
    drafts_manager = DraftsManager()
    if drafts_manager.has(section):
        drafts_manager.remove(section)
    
    return (
        gr.update(value=updated_text), # viewer_md
        gr.update(visible=False), # chat_actions_row_1
        gr.update(visible=False), # chat_discard_btn
        gr.update(visible=False), # chat_force_edit_btn
        gr.update(visible=False), # chat_actions_row_2
        gr.update(visible=False), # chat_validate_btn
        gr.update(visible=False), # chat_keep_draft_btn
        updated_text, # current_md
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
    )

def continue_edit(section, current_log):
    """Return to editing mode. If Chat mode, return to Chat Section."""
    new_log, status_update = append_status(current_log, f"🔁 ({section}) Continue chatting.")
    
    return (
        gr.update(visible=False),   # hide Validation Title
        gr.update(visible=False),   # hide Validation Box
        gr.update(visible=False),   # hide Apply Updates
        gr.update(visible=False),   # hide Regenerate
        gr.update(visible=False),   # hide Continue Editing
        gr.update(visible=False),   # hide Discard2
        gr.update(visible=False),   # hide Validate (Manual)
        gr.update(visible=False),   # hide Discard (Manual)
        gr.update(visible=False),   # hide Force Edit (Manual)
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
    )

