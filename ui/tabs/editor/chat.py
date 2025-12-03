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
            gr.update(), # chat_actions_row_1
            gr.update(), # chat_discard_btn
            gr.update(), # chat_force_edit_btn
            gr.update(), # chat_actions_row_2
            gr.update(), # chat_validate_btn
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
        gr.update(), # chat_actions_row_1
        gr.update(), # chat_discard_btn
        gr.update(), # chat_force_edit_btn
        gr.update(), # chat_actions_row_2
        gr.update(), # chat_validate_btn
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
                gr.update(visible=True), # chat_actions_row_1
                gr.update(visible=True), # chat_discard_btn
                gr.update(visible=True), # chat_force_edit_btn
                gr.update(visible=True), # chat_actions_row_2
                gr.update(visible=True), # chat_validate_btn
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
                gr.update(), # chat_actions_row_1
                gr.update(), # chat_discard_btn
                gr.update(), # chat_force_edit_btn
                gr.update(), # chat_actions_row_2
                gr.update(), # chat_validate_btn
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
            gr.update(), # chat_actions_row_1
            gr.update(), # chat_discard_btn
            gr.update(), # chat_force_edit_btn
            gr.update(), # chat_actions_row_2
            gr.update(), # chat_validate_btn
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
        gr.update(), # viewer_md - NO CHANGE
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
        gr.update(), # viewer_md - NO CHANGE
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
        gr.update(visible=False), # chat_actions_row_1
        gr.update(visible=False), # chat_discard_btn
        gr.update(visible=False), # chat_force_edit_btn
        gr.update(visible=False), # chat_actions_row_2
        gr.update(visible=False), # chat_validate_btn
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
        gr.update(visible=False), # chat_actions_row_1
        gr.update(visible=False), # chat_discard_btn
        gr.update(visible=False), # chat_force_edit_btn
        gr.update(visible=False), # chat_actions_row_2
        gr.update(visible=False), # chat_validate_btn
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

def create_chat_ui():
    """Create UI components for Chat mode."""
    with gr.Column(visible=False) as chat_section:
        chatbot = gr.Chatbot(
            label="Plot King",
            value=[{"role": "assistant", "content": PLOT_KING_GREETING}],
            height=350,
            elem_id="editor-chatbot",
            avatar_images=(None, "https://api.dicebear.com/7.x/bottts/svg?seed=PlotKing"),
            bubble_full_width=False,
            type="messages"
        )
        chat_input = gr.Textbox(
            label="Message Plot King",
            placeholder="Ask for suggestions or request edits...",
            lines=1,
            max_lines=10,
            interactive=True,
            elem_id="chat-input",
        )
        with gr.Row():
            chat_send_btn = gr.Button("📩 Send", variant="primary", interactive=False, scale=1, min_width=0)
            chat_clear_btn = gr.Button("🧹 Clear", scale=1, min_width=0)
        
        with gr.Row(visible=False) as chat_actions_row_1:
            chat_discard_btn = gr.Button("🗑️ Discard", scale=1, min_width=0)
            chat_force_edit_btn = gr.Button("⚡ Force Edit", scale=1, min_width=0)
        
        with gr.Row(visible=False) as chat_actions_row_2:
            chat_validate_btn = gr.Button("✅ Validate", scale=1, min_width=0)

    return chat_section, chatbot, chat_input, chat_send_btn, chat_clear_btn, chat_actions_row_1, chat_discard_btn, chat_force_edit_btn, chat_actions_row_2, chat_validate_btn

def create_chat_handlers(components, states):
    """Wire events for Chat mode components."""
    chat_input = components["chat_input"]
    chat_send_btn = components["chat_send_btn"]
    chat_clear_btn = components["chat_clear_btn"]
    chat_discard_btn = components["chat_discard_btn"]
    chat_force_edit_btn = components["chat_force_edit_btn"]
    chat_validate_btn = components["chat_validate_btn"]
    chatbot = components["chatbot"]
    
    # Shared components
    selected_section = states["selected_section"]
    chat_history = states["chat_history"]
    current_md = states["current_md"]
    initial_text_before_chat = states["initial_text_before_chat"]
    status_log = states["status_log"]
    current_drafts = states["current_drafts"]
    create_sections_epoch = states["create_sections_epoch"]
    
    # Chat Input Change Event to toggle Send button
    chat_input.change(
        fn=lambda x: gr.update(interactive=bool(x.strip())),
        inputs=[chat_input],
        outputs=[chat_send_btn]
    )

    chat_send_btn.click(
        fn=chat_handler,
        inputs=[selected_section, chat_input, chat_history, current_md, initial_text_before_chat, status_log, current_drafts],
        outputs=[
            chat_input,
            chat_history,
            components["chatbot"], # Update chatbot component
            components["viewer_md"],
            components["chat_actions_row_1"], # validate/discard row
            chat_discard_btn, # redundant but for safety if handled individually
            chat_force_edit_btn, # redundant but for safety if handled individually
            components["chat_actions_row_2"], # force/diff row
            chat_validate_btn,
            status_log,
            components["status_strip"],
            current_md,
            chat_input, # Added output
            chat_clear_btn, # Added output
            current_drafts, # Added output
            components["status_row"], # Added output
            components["status_label"],
            components["btn_checkpoint"],
            components["btn_draft"],
            components["btn_diff"],
            states["current_view_state"],
        ],
    )
    
    # Also trigger send on Enter in chat_input
    chat_input.submit(
        fn=chat_handler,
        inputs=[selected_section, chat_input, chat_history, current_md, initial_text_before_chat, status_log, current_drafts],
        outputs=[
            chat_input,
            chat_history,
            components["chatbot"], # Update chatbot component
            components["viewer_md"],
            components["chat_actions_row_1"], # validate/discard row
            chat_discard_btn, # redundant but for safety if handled individually
            chat_force_edit_btn, # redundant but for safety if handled individually
            components["chat_actions_row_2"], # force/diff row
            chat_validate_btn,
            status_log,
            components["status_strip"],
            current_md,
            chat_input, # Added output
            chat_clear_btn, # Added output
            current_drafts, # Added output
            components["status_row"], # Added output
            components["status_label"],
            components["btn_checkpoint"],
            components["btn_draft"],
            components["btn_diff"],
            states["current_view_state"],
        ],
    )
    
    chat_clear_btn.click(
        fn=clear_chat,
        inputs=[selected_section, status_log],
        outputs=[chat_history, status_log, components["status_strip"], components["chatbot"]]
    )

    chatbot.clear(
        fn=clear_chat,
        inputs=[selected_section, status_log],
        outputs=[chat_history, status_log, components["status_strip"], components["chatbot"]]
    )
    
    chat_discard_btn.click(
        fn=discard_handler,
        inputs=[selected_section, status_log, current_drafts],
        outputs=[
            components["viewer_md"],
            components["chat_actions_row_1"],
            chat_discard_btn,
            chat_force_edit_btn,
            components["chat_actions_row_2"],
            chat_validate_btn,
            current_md,
            status_log,
            components["status_strip"],
            current_drafts,
            components["status_row"],
            components["status_label"],
            components["btn_checkpoint"],
            components["btn_draft"],
            components["btn_diff"],
            states["current_view_state"],
        ]
    )
    
    chat_force_edit_btn.click(
        fn=force_edit_handler,
        inputs=[selected_section, current_md, status_log, create_sections_epoch, current_drafts],
        outputs=[
            components["viewer_md"],
            components["chat_actions_row_1"],
            chat_discard_btn,
            chat_force_edit_btn,
            components["chat_actions_row_2"],
            chat_validate_btn,
            current_md,
            status_log,
            components["status_strip"],
            create_sections_epoch,
            current_drafts,
            components["status_row"],
            components["status_label"],
            components["btn_checkpoint"],
            components["btn_draft"],
            components["btn_diff"],
            states["current_view_state"],
        ]
    )
    
    chat_validate_btn.click(
        fn=validate_handler,
        inputs=[selected_section, current_md, status_log, current_drafts],
        outputs=[
            components["chat_section"],
            components["validation_title"],
            components["validation_box"],
            components["apply_updates_btn"],
            components["regenerate_btn"],
            components["continue_btn"],
            components["discard2_btn"],
            components["viewer_md"],
            status_log,
            components["status_strip"],
            states["pending_plan"],
        ]
    )
