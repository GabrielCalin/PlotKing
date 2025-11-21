# ui/tabs/editor/chat.py
import gradio as gr
import difflib
from markdownify import markdownify as md
import ui.editor_handlers as H
from ui.tabs.editor.utils import append_status
from pipeline.steps.chat_editor.llm import call_llm_chat

def chat_handler(section, message, history, current_text, initial_text, current_log):
    """
    Handles the chat interaction with the Plot King.
    """
    if not message:
        return (
            gr.update(value=""), # clear input
            history,
            gr.update(), # viewer_md
            gr.update(), # validate_btn
            gr.update(), # discard_btn
            gr.update(), # force_edit_btn
            gr.update(), # diff_btn
            current_log,
            gr.update(), # status_strip
            current_text, # current_md
        )

    # Append user message to history immediately for UI responsiveness
    new_history = history + [[message, None]]
    
    # Prepare conversation history for LLM (excluding the current new message which is passed separately)
    # Format for LLM: [{"role": "user", "content": "msg"}, {"role": "assistant", "content": "msg"}]
    llm_history = []
    for user_msg, bot_msg in history:
        if user_msg:
            llm_history.append({"role": "user", "content": user_msg})
        if bot_msg:
            llm_history.append({"role": "assistant", "content": bot_msg})

    new_log, status_update = append_status(current_log, f"💬 ({section}) Asking Plot King...")
    
    # Yield loading state
    yield (
        gr.update(value=""), # clear input
        new_history,
        gr.update(), # viewer_md
        gr.update(), # validate_btn
        gr.update(), # discard_btn
        gr.update(), # force_edit_btn
        gr.update(), # diff_btn
        new_log,
        status_update,
        current_text,
    )

    # Call LLM
    try:
        result = call_llm_chat(
            section_name=section,
            initial_content=initial_text,
            current_content=current_text,
            conversation_history=llm_history,
            user_message=message
        )
        
        response_text = result.get("response", "I'm speechless!")
        new_content = result.get("new_content")
        
        # Update history with bot response
        new_history[-1][1] = response_text
        
        if new_content:
            # Edits were made
            final_log, final_status = append_status(new_log, f"✅ ({section}) Plot King made edits.")
            yield (
                gr.update(value=""),
                new_history,
                gr.update(value=new_content), # viewer_md updated with new content
                gr.update(visible=True), # validate_btn
                gr.update(visible=True), # discard_btn
                gr.update(visible=True), # force_edit_btn
                gr.update(visible=True, value="Diff"), # diff_btn
                final_log,
                final_status,
                new_content, # update current_md
            )
        else:
            # No edits, just chat
            final_log, final_status = append_status(new_log, f"✅ ({section}) Plot King replied.")
            yield (
                gr.update(value=""),
                new_history,
                gr.update(), # viewer_md unchanged
                gr.update(), # validate_btn unchanged
                gr.update(), # discard_btn unchanged
                gr.update(), # force_edit_btn unchanged
                gr.update(), # diff_btn unchanged
                final_log,
                final_status,
                current_text, # current_md unchanged
            )
            
    except Exception as e:
        error_msg = f"Error talking to Plot King: {str(e)}"
        new_history[-1][1] = error_msg
        final_log, final_status = append_status(new_log, f"❌ ({section}) Chat error: {str(e)}")
        yield (
            gr.update(value=""),
            new_history,
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            final_log,
            final_status,
            current_text,
        )

def clear_chat(current_log):
    """Resets the chat history."""
    new_log, status_update = append_status(current_log, "🧹 Chat cleared.")
    return [], new_log, status_update

def diff_handler(current_text, initial_text, diff_btn_label):
    """
    Toggles between Draft view and Diff view.
    """
    if diff_btn_label == "Diff":
        # Calculate Diff
        # We use difflib to get HTML diff, then convert to markdown
        diff = difflib.HtmlDiff().make_file(
            initial_text.splitlines(),
            current_text.splitlines(),
            fromdesc="Original",
            todesc="Draft",
            context=True,
            numlines=3
        )
        # Convert HTML diff to Markdown
        markdown_diff = md(diff)
        
        return (
            gr.update(value=markdown_diff), # viewer_md shows diff
            gr.update(value="Show Draft"), # Toggle button label
        )
    else:
        # Revert to Draft view
        return (
            gr.update(value=current_text), # viewer_md shows draft
            gr.update(value="Diff"), # Toggle button label
        )

def validate_handler(section, current_text, current_log):
    """
    Starts validation for the chat edits. Hides Chat UI.
    """
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
        gr.update(visible=True, value=current_text), # viewer_md
        new_log,
        status_update
    )
    
    msg, plan = H.editor_validate(section, current_text)
    final_log, final_status = append_status(new_log, f"✅ ({section}) Validation completed.")
    
    yield (
        gr.update(visible=False), # chat_group
        gr.update(visible=True), # validation_title
        gr.update(value=msg, visible=True), # validation_box
        gr.update(visible=True), # apply_updates_btn
        gr.update(visible=True), # regenerate_btn
        gr.update(visible=True), # continue_btn
        gr.update(visible=True), # discard2_btn
        gr.update(visible=True, value=current_text), # viewer_md
        final_log,
        final_status
    )

def discard_handler(section, current_log):
    """
    Discards chat edits and reverts to checkpoint.
    """
    clean_text = H.editor_get_section_content(section) or "_Empty_"
    new_log, status_update = append_status(current_log, f"🗑️ ({section}) Chat edits discarded.")
    
    return (
        gr.update(value=clean_text), # viewer_md
        gr.update(visible=False), # validate_btn
        gr.update(visible=False), # discard_btn
        gr.update(visible=False), # force_edit_btn
        gr.update(visible=False, value="Diff"), # diff_btn (reset label too)
        clean_text, # current_md
        new_log,
        status_update
    )

def force_edit_handler(section, current_text, current_log, create_epoch):
    """
    Force saves the chat edits to checkpoint.
    """
    updated_text = H.force_edit(section, current_text)
    new_log, status_update = append_status(current_log, f"⚡ ({section}) Synced (forced from Chat).")
    new_create_epoch = (create_epoch or 0) + 1
    
    return (
        gr.update(value=updated_text), # viewer_md
        gr.update(visible=False), # validate_btn
        gr.update(visible=False), # discard_btn
        gr.update(visible=False), # force_edit_btn
        gr.update(visible=False, value="Diff"), # diff_btn
        updated_text, # current_md
        new_log,
        status_update,
        new_create_epoch
    )

def continue_edit(section, current_log, current_md):
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
        gr.update(visible=True, value=current_md),  # show viewer_md
        gr.update(visible=False),   # hide editor_tb
        gr.update(value="Chat", interactive=False), # keep Mode locked to Chat
        gr.update(interactive=False), # keep Section locked
        status_update,
        new_log,
        gr.update(visible=True),    # SHOW Chat Section
    )
