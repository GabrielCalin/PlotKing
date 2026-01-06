# ui/tabs/editor/chat_ui.py
import gradio as gr
from handlers.editor.constants import Components, States

PLOT_KING_GREETING = "Hello! I'm Plot King, your friendly creative sidekick. How can I help you today?"

def create_chat_ui():
    """Create UI components for Chat mode."""
    with gr.Column(visible=False) as chat_section:
        chat_type_dropdown = gr.Dropdown(
            label="Chat Type",
            choices=["Chapter", "Fill"],
            value="Chapter",
            visible=False, # Initially hidden, shown only for Fills
            interactive=True,
            elem_id="chat-type-dropdown"
        )
        chatbot = gr.Chatbot(
            label="Plot King",
            value=[{"role": "assistant", "content": PLOT_KING_GREETING}],
            height=350,
            elem_id="editor-chatbot",
            avatar_images=("images/user_avatar.png", "images/plotking_avatar.png"),
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
            chat_keep_draft_btn = gr.Button("💾 Keep Draft", scale=1, min_width=0)
            chat_validate_btn = gr.Button("✅ Validate", scale=1, min_width=0)

    return chat_section, chatbot, chat_input, chat_send_btn, chat_clear_btn, chat_actions_row_1, chat_discard_btn, chat_force_edit_btn, chat_actions_row_2, chat_validate_btn, chat_keep_draft_btn, chat_type_dropdown

def create_chat_handlers(components, states):
    """Wire events for Chat mode components."""
    from handlers.editor.chat import chat_handler, clear_chat, validate_handler, discard_handler, force_edit_handler, handle_chat_type_change
    from handlers.editor.utils import keep_draft_handler
    
    chat_input = components[Components.CHAT_INPUT]
    chat_send_btn = components[Components.CHAT_SEND_BTN]
    chat_clear_btn = components[Components.CHAT_CLEAR_BTN]
    chat_discard_btn = components[Components.CHAT_DISCARD_BTN]
    chat_force_edit_btn = components[Components.CHAT_FORCE_EDIT_BTN]
    chat_validate_btn = components[Components.CHAT_VALIDATE_BTN]
    chat_keep_draft_btn = components[Components.CHAT_KEEP_DRAFT_BTN]
    chatbot = components[Components.CHATBOT]
    
    # Shared components
    selected_section = states[States.SELECTED_SECTION]
    chat_history = states[States.CHAT_HISTORY]
    status_log = states[States.STATUS_LOG]
    create_sections_epoch = states[States.CREATE_SECTIONS_EPOCH]
    mode_radio = components[Components.MODE_RADIO]
    
    # Chat Input Change Event to toggle Send button
    chat_input.change(
        fn=lambda x: gr.update(interactive=bool(x.strip())),
        inputs=[chat_input],
        outputs=[chat_send_btn]
    )

    chat_type_dropdown = components[Components.CHAT_TYPE_DROPDOWN]

    chat_type_dropdown.change(
        fn=handle_chat_type_change,
        inputs=[selected_section, status_log, chat_type_dropdown],
        outputs=[chat_history, status_log, components[Components.STATUS_STRIP], components[Components.CHATBOT]]
    ).then(
        fn=clear_chat,
        inputs=[selected_section, status_log, chat_type_dropdown],
        outputs=[chat_history, status_log, components[Components.STATUS_STRIP], components[Components.CHATBOT]]
    )

    chat_send_btn.click(
        fn=chat_handler,
        inputs=[selected_section, chat_input, chat_history, status_log, chat_type_dropdown],
        outputs=[
            chat_input,
            chat_history,
            components[Components.CHATBOT],
            components[Components.VIEWER_MD],
            components[Components.CHAT_ACTIONS_ROW_1],
            chat_discard_btn,
            chat_force_edit_btn,
            components[Components.CHAT_ACTIONS_ROW_2],
            chat_validate_btn,
            chat_keep_draft_btn,
            status_log,
            components[Components.STATUS_STRIP],
            chat_input,
            chat_clear_btn,
            components[Components.STATUS_ROW],
            components[Components.STATUS_LABEL],
            components[Components.BTN_CHECKPOINT],
            components[Components.BTN_DRAFT],
            components[Components.BTN_DIFF],
            states[States.CURRENT_VIEW_STATE],
            mode_radio,
            components[Components.BTN_UNDO],
            components[Components.BTN_REDO],
            components[Components.ADD_FILL_BTN],
            chat_type_dropdown,
        ],
    )
    
    # Also trigger send on Enter in chat_input
    chat_input.submit(
        fn=chat_handler,
        inputs=[selected_section, chat_input, chat_history, status_log, chat_type_dropdown],
        outputs=[
            chat_input,
            chat_history,
            components[Components.CHATBOT],
            components[Components.VIEWER_MD],
            components[Components.CHAT_ACTIONS_ROW_1],
            chat_discard_btn,
            chat_force_edit_btn,
            components[Components.CHAT_ACTIONS_ROW_2],
            chat_validate_btn,
            chat_keep_draft_btn,
            status_log,
            components[Components.STATUS_STRIP],
            chat_input,
            chat_clear_btn,
            components[Components.STATUS_ROW],
            components[Components.STATUS_LABEL],
            components[Components.BTN_CHECKPOINT],
            components[Components.BTN_DRAFT],
            components[Components.BTN_DIFF],
            states[States.CURRENT_VIEW_STATE],
            mode_radio,
            components[Components.BTN_UNDO],
            components[Components.BTN_REDO],
            components[Components.ADD_FILL_BTN],
            chat_type_dropdown,
        ],
    )
    
    chat_clear_btn.click(
        fn=clear_chat,
        inputs=[selected_section, status_log, chat_type_dropdown],
        outputs=[chat_history, status_log, components[Components.STATUS_STRIP], components[Components.CHATBOT]]
    )

    chatbot.clear(
        fn=clear_chat,
        inputs=[selected_section, status_log, chat_type_dropdown],
        outputs=[chat_history, status_log, components[Components.STATUS_STRIP], components[Components.CHATBOT]]
    )
    
    chat_discard_btn.click(
        fn=discard_handler,
        inputs=[selected_section, status_log],
        outputs=[
            components[Components.VIEWER_MD],
            components[Components.CHAT_ACTIONS_ROW_1],
            chat_discard_btn,
            chat_force_edit_btn,
            components[Components.CHAT_ACTIONS_ROW_2],
            chat_validate_btn,
            chat_keep_draft_btn,
            status_log,
            components[Components.STATUS_STRIP],
            components[Components.STATUS_ROW],
            components[Components.STATUS_LABEL],
            components[Components.BTN_CHECKPOINT],
            components[Components.BTN_DRAFT],
            components[Components.BTN_DIFF],
            states[States.CURRENT_VIEW_STATE],
            mode_radio,
            components[Components.BTN_UNDO],
            components[Components.BTN_REDO],
            components[Components.ADD_FILL_BTN],
            chat_type_dropdown,
        ]
    )
    
    chat_force_edit_btn.click(
        fn=force_edit_handler,
        inputs=[selected_section, status_log, create_sections_epoch],
        outputs=[
            components[Components.VIEWER_MD],
            components[Components.CHAT_ACTIONS_ROW_1],
            chat_discard_btn,
            chat_force_edit_btn,
            components[Components.CHAT_ACTIONS_ROW_2],
            chat_validate_btn,
            chat_keep_draft_btn,
            status_log,
            components[Components.STATUS_STRIP],
            create_sections_epoch,
            components[Components.STATUS_ROW],
            components[Components.STATUS_LABEL],
            components[Components.BTN_CHECKPOINT],
            components[Components.BTN_DRAFT],
            components[Components.BTN_DIFF],
            states[States.CURRENT_VIEW_STATE],
            mode_radio,
            components[Components.SECTION_DROPDOWN],
            components[Components.BTN_UNDO],
            components[Components.BTN_REDO],
            components[Components.ADD_FILL_BTN],
        ]
    )
    
    chat_validate_btn.click(
        fn=validate_handler,
        inputs=[selected_section, status_log],
        outputs=[
            components[Components.CHAT_SECTION],
            components[Components.VALIDATION_TITLE],
            components[Components.VALIDATION_BOX],
            components[Components.VALIDATION_SECTION],
            components[Components.APPLY_UPDATES_BTN],
            components[Components.REGENERATE_BTN],
            components[Components.CONTINUE_BTN],
            components[Components.DISCARD2_BTN],
            components[Components.VIEWER_MD],
            status_log,
            components[Components.STATUS_STRIP],
            states[States.PENDING_PLAN],
            mode_radio,
            components[Components.BTN_UNDO],
            components[Components.BTN_REDO],
            components[Components.ADD_FILL_BTN],
        ]
    )

    def chat_keep_draft_wrapper(section, status_log):
        from state.overall_state import get_current_section_content
        content = get_current_section_content(section)
        return keep_draft_handler(section, content, status_log)
    
    chat_keep_draft_btn.click(
        fn=chat_keep_draft_wrapper,
        inputs=[selected_section, status_log],
        outputs=[
            components[Components.VIEWER_MD],
            components[Components.STATUS_LABEL],
            states[States.CURRENT_VIEW_STATE],
            components[Components.BTN_CHECKPOINT],
            components[Components.BTN_DRAFT],
            components[Components.BTN_DIFF],
            components[Components.MODE_RADIO],
            components[Components.SECTION_DROPDOWN],
            components[Components.VIEW_ACTIONS_ROW],
            states[States.STATUS_LOG],    # new_log
            components[Components.STATUS_STRIP], # status_log component
            # Manual Mode UI items to hide
            components[Components.START_EDIT_BTN],
            components[Components.CONFIRM_BTN],
            components[Components.DISCARD_BTN],
            components[Components.FORCE_EDIT_BTN],
            components[Components.KEEP_DRAFT_BTN],
            # Rewrite Mode items to hide
            components[Components.REWRITE_SECTION],
            # Chat Mode items to hide
            components[Components.CHAT_SECTION],
            components[Components.ADD_FILL_BTN],
        ]
    )



