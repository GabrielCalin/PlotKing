# ui/tabs/editor/chat.py
import gradio as gr
import ui.editor_handlers as H
from ui.tabs.editor.utils import append_status
from pipeline.steps.chat_editor.llm import call_llm_chat

def chat_handler(section, message, history, current_text, initial_text, current_log, current_drafts):
    """
    Handles the chat interaction with the Plot King.
    Uses OpenAI-style messages format: [{'role': 'user', 'content': '...'}, ...]
    """
    if not message:
        drafts = current_drafts or {}
        return (
            gr.update(value=""), # clear input
            history,
            history, # chatbot update
            gr.update(), # viewer_md
            gr.update(), # validate_btn
            gr.update(), # discard_btn
            gr.update(), # force_edit_btn
            current_log,
            gr.update(), # status_strip
            current_text, # current_md
            gr.update(), # chat_input (no change)
            gr.update(), # chat_clear_btn (no change)
            drafts, # current_drafts
            gr.update(), # status_row
            gr.update(), # status_label
            gr.update(), # btn_checkpoint
            gr.update(), # btn_draft
            gr.update(), # btn_diff
            "Checkpoint", # current_view_state
        )

    # Append user message to history
    new_history = history + [{"role": "user", "content": message}]
    
    new_log, status_update = append_status(current_log, f"💬 ({section}) Asking Plot King...")
    
    drafts = current_drafts.copy() if current_drafts else {}
    
    # Yield loading state
    yield (
        gr.update(value="", interactive=False), # clear input and disable
        new_history,
        new_history, # chatbot update
        gr.update(), # viewer_md
        gr.update(), # validate_btn
        gr.update(), # discard_btn
        gr.update(), # force_edit_btn
        new_log,
        status_update,
        current_text,
        gr.update(interactive=False), # chat_input disable
        gr.update(interactive=False), # chat_clear_btn disable
        drafts, # current_drafts
        gr.update(), # status_row
        gr.update(), # status_label
        gr.update(), # btn_checkpoint
        gr.update(), # btn_draft
        gr.update(), # btn_diff
        "Checkpoint", # current_view_state
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
            drafts[section] = new_content
            final_log, final_status = append_status(new_log, f"✅ ({section}) Plot King made edits.")
            yield (
                gr.update(value="", interactive=True),
                new_history,
                new_history, # chatbot update
                gr.update(value=new_content), # viewer_md updated with new content
                gr.update(visible=True), # validate_btn
                gr.update(visible=True), # discard_btn
                gr.update(visible=True), # force_edit_btn
                final_log,
                final_status,
                new_content, # update current_md
                gr.update(interactive=True), # chat_input enable
                gr.update(interactive=True), # chat_clear_btn enable
                drafts, # current_drafts - updated with draft
                gr.update(visible=True), # status_row - show
                gr.update(value="**Viewing:** <span style='color:red;'>Draft</span>"), # status_label - show Draft
                gr.update(visible=True, interactive=True), # btn_checkpoint - visible
                gr.update(visible=True, interactive=True), # btn_draft - visible
                gr.update(visible=True, interactive=True), # btn_diff - visible
                "Draft", # current_view_state
            )
        else:
            # No edits, just chat
            final_log, final_status = append_status(new_log, f"✅ ({section}) Plot King replied.")
            yield (
                gr.update(value="", interactive=True),
                new_history,
                new_history, # chatbot update
                gr.update(), # viewer_md unchanged
                gr.update(), # validate_btn unchanged
                gr.update(), # discard_btn unchanged
                gr.update(), # force_edit_btn unchanged
                final_log,
                final_status,
                current_text, # current_md unchanged
                gr.update(interactive=True), # chat_input enable
                gr.update(interactive=True), # chat_clear_btn enable
                drafts, # current_drafts - unchanged
                gr.update(), # status_row - unchanged
                gr.update(), # status_label - unchanged
                gr.update(), # btn_checkpoint - unchanged
                gr.update(), # btn_draft - unchanged
                gr.update(), # btn_diff - unchanged
                "Checkpoint", # current_view_state - unchanged
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
            gr.update(), # validate_btn
            gr.update(), # discard_btn
            gr.update(), # force_edit_btn
            final_log,
            final_status,
            current_text,
            gr.update(interactive=True), # chat_input enable
            gr.update(interactive=True), # chat_clear_btn enable
            drafts, # current_drafts - unchanged
            gr.update(), # status_row - unchanged
            gr.update(), # status_label - unchanged
            gr.update(), # btn_checkpoint - unchanged
            gr.update(), # btn_draft - unchanged
            gr.update(), # btn_diff - unchanged
            "Checkpoint", # current_view_state - unchanged
        )


PLOT_KING_GREETING = "Hello! I'm Plot King, your friendly creative sidekick. How can I help you today?"

def clear_chat(section, current_log):
    """Resets the chat history to the initial greeting."""
    initial_greeting = [{"role": "assistant", "content": PLOT_KING_GREETING}]
    new_log, status_update = append_status(current_log, f"🧹 ({section}) Chat cleared.")
    return initial_greeting, new_log, status_update, initial_greeting



def validate_handler(section, current_text, current_log, current_drafts):
    """
    Starts validation for the chat edits. Hides Chat UI.
    Uses existing draft from current_drafts if available, otherwise uses current_text.
    """
    # Use existing draft if available, otherwise use current_text
    drafts = current_drafts or {}
    draft_to_validate = drafts.get(section, current_text)
    
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
        gr.update(visible=True, value=draft_to_validate), # viewer_md - show draft if exists
        new_log,
        status_update,
        None, # pending_plan placeholder
    )
    
    msg, plan = H.editor_validate(section, draft_to_validate)
    final_log, final_status = append_status(new_log, f"✅ ({section}) Validation completed.")
    
    yield (
        gr.update(visible=False), # chat_group
        gr.update(visible=True), # validation_title
        gr.update(value=msg, visible=True), # validation_box
        gr.update(visible=True), # apply_updates_btn
        gr.update(visible=True), # regenerate_btn
        gr.update(visible=True), # continue_btn
        gr.update(visible=True), # discard2_btn
        gr.update(visible=True, value=draft_to_validate), # viewer_md - show draft if exists
        final_log,
        final_status,
        plan, # pending_plan
    )

def discard_handler(section, current_log, current_drafts):
    """
    Discards chat edits and reverts to checkpoint. Removes draft from current_drafts.
    """
    clean_text = H.editor_get_section_content(section) or "_Empty_"
    new_log, status_update = append_status(current_log, f"🗑️ ({section}) Chat edits discarded.")
    
    # Remove draft for this section
    drafts = current_drafts.copy() if current_drafts else {}
    if section in drafts:
        del drafts[section]
    
    return (
        gr.update(value=clean_text), # viewer_md
        gr.update(visible=False), # validate_btn - hide (no active changes)
        gr.update(visible=False), # discard_btn - hide (no active changes)
        gr.update(visible=False), # force_edit_btn - hide (no active changes)
        clean_text, # current_md
        new_log,
        status_update,
        drafts, # current_drafts - removed draft for this section
        gr.update(visible=True), # status_row - show (but buttons hidden if no drafts)
        gr.update(value="**Viewing:** <span style='color:red;'>Checkpoint</span>"), # status_label - show Checkpoint
        gr.update(visible=False), # btn_checkpoint - hide (no draft = no point showing C only)
        gr.update(visible=False), # btn_draft - hide
        gr.update(visible=False), # btn_diff - hide
        "Checkpoint", # current_view_state
    )

def force_edit_handler(section, current_text, current_log, create_epoch, current_drafts):
    """
    Force saves the chat edits to checkpoint.
    """
    updated_text = H.force_edit(section, current_text)
    new_log, status_update = append_status(current_log, f"⚡ ({section}) Synced (forced from Chat).")
    new_create_epoch = (create_epoch or 0) + 1
    
    # Remove draft for this section since changes are saved to checkpoint
    drafts = current_drafts.copy() if current_drafts else {}
    if section in drafts:
        del drafts[section]
    
    return (
        gr.update(value=updated_text), # viewer_md
        gr.update(visible=False), # validate_btn - hide (no active changes)
        gr.update(visible=False), # discard_btn - hide (no active changes)
        gr.update(visible=False), # force_edit_btn - hide (no active changes)
        updated_text, # current_md
        new_log,
        status_update,
        new_create_epoch,
        drafts, # current_drafts - removed draft for this section
        gr.update(visible=True), # status_row - show
        gr.update(value="**Viewing:** <span style='color:red;'>Checkpoint</span>"), # status_label - show Checkpoint
        gr.update(visible=False), # btn_checkpoint - hide (no draft = no point showing C only)
        gr.update(visible=False), # btn_draft - hide
        gr.update(visible=False), # btn_diff - hide
        "Checkpoint", # current_view_state
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
        gr.update(value="Chat", interactive=True), # unlock Mode
        gr.update(interactive=True), # unlock Section
        status_update,
        new_log,
        gr.update(visible=True),    # SHOW Chat Section
        gr.update(visible=True),    # status_row - show (draft exists after validate)
    )
