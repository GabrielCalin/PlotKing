# ui/tabs/editor/manual_ui.py
import gradio as gr
from handlers.editor.constants import Components, States

def create_manual_ui():
    """Create UI components for Manual mode."""
    with gr.Column(visible=False) as manual_section:
        start_edit_btn = gr.Button("✍️ Start Editing", variant="primary", visible=False)
        
        with gr.Row():
            confirm_btn = gr.Button("✅ Validate", visible=False, scale=1, min_width=0)
            force_edit_btn = gr.Button("⚡ Force Edit", visible=False, scale=1, min_width=0)
        
        with gr.Row():
            keep_draft_btn = gr.Button("💾 Keep Draft", visible=False, scale=1, min_width=0)
            discard_btn = gr.Button("🗑️ Discard", visible=False, scale=1, min_width=0)
    
    return manual_section, start_edit_btn, confirm_btn, discard_btn, force_edit_btn, keep_draft_btn

def create_manual_handlers(components, states):
    """Wire events for Manual mode components."""
    from handlers.editor.manual import start_edit, confirm_edit, discard_from_manual, force_edit
    from handlers.editor.utils import keep_draft_handler
    
    start_edit_btn = components[Components.START_EDIT_BTN]
    confirm_btn = components[Components.CONFIRM_BTN]
    discard_btn = components[Components.DISCARD_BTN]
    force_edit_btn = components[Components.FORCE_EDIT_BTN]
    keep_draft_btn = components[Components.KEEP_DRAFT_BTN]
    
    # Shared components
    selected_section = states[States.SELECTED_SECTION]
    status_log = states[States.STATUS_LOG]
    editor_tb = components[Components.EDITOR_TB]
    create_sections_epoch = states[States.CREATE_SECTIONS_EPOCH]
    
    start_edit_btn.click(
        fn=lambda *args: (*start_edit(*args), gr.update(visible=False)), # Wrap to hide status row
        inputs=[selected_section, status_log],
        outputs=[
            start_edit_btn,
            components[Components.REWRITE_SECTION],
            confirm_btn,
            discard_btn,
            force_edit_btn,
            keep_draft_btn,
            components[Components.VIEWER_MD],
            editor_tb,
            components[Components.MODE_RADIO],
            components[Components.SECTION_DROPDOWN],
            components[Components.STATUS_STRIP],
            status_log,
            components[Components.STATUS_ROW],
        ],
    )

    confirm_btn.click(
        fn=confirm_edit,
        inputs=[selected_section, editor_tb, status_log],
        outputs=[
            components[Components.VALIDATION_BOX], states[States.PENDING_PLAN],
            components[Components.VALIDATION_TITLE], components[Components.VALIDATION_BOX],
            components[Components.VALIDATION_SECTION],
            components[Components.APPLY_UPDATES_BTN], components[Components.REGENERATE_BTN], components[Components.CONTINUE_BTN], components[Components.DISCARD2_BTN],
            confirm_btn, discard_btn, force_edit_btn,
            start_edit_btn,
            components[Components.MANUAL_SECTION],
            components[Components.REWRITE_SECTION],
            components[Components.VIEWER_MD],
            editor_tb,
            components[Components.MODE_RADIO], components[Components.SECTION_DROPDOWN],
            components[Components.STATUS_STRIP],
            status_log,
            components[Components.STATUS_ROW],
            keep_draft_btn
        ],
        queue=True,
        show_progress=False,
    )

    discard_btn.click(
        fn=discard_from_manual,
        inputs=[selected_section, status_log],
        outputs=[
            components[Components.VIEWER_MD], editor_tb, components[Components.VALIDATION_BOX], states[States.PENDING_PLAN],
            components[Components.VALIDATION_TITLE], components[Components.VALIDATION_SECTION],
            components[Components.APPLY_UPDATES_BTN], components[Components.REGENERATE_BTN], components[Components.CONTINUE_BTN], components[Components.DISCARD2_BTN],
            start_edit_btn,
            confirm_btn, discard_btn, force_edit_btn,
            components[Components.REWRITE_SECTION],
            components[Components.MODE_RADIO], components[Components.SECTION_DROPDOWN], components[Components.STATUS_STRIP],
            status_log,
            components[Components.STATUS_ROW],
            keep_draft_btn,
        ],
    )

    force_edit_btn.click(
        fn=force_edit,
        inputs=[selected_section, editor_tb, status_log, create_sections_epoch],
        outputs=[
            components[Components.VIEWER_MD], components[Components.STATUS_STRIP], editor_tb,
            confirm_btn, discard_btn, force_edit_btn, start_edit_btn,
            components[Components.REWRITE_SECTION],
            components[Components.MODE_RADIO], components[Components.SECTION_DROPDOWN],
            status_log,
            create_sections_epoch,
            components[Components.STATUS_ROW],
            keep_draft_btn,
            components[Components.STATUS_LABEL],
            components[Components.BTN_CHECKPOINT],
            components[Components.BTN_DRAFT],
            components[Components.BTN_DIFF],
            states[States.CURRENT_VIEW_STATE],
            components[Components.BTN_UNDO],
            components[Components.BTN_REDO],
        ],
    )
    
    keep_draft_btn.click(
        fn=keep_draft_handler,
        inputs=[selected_section, editor_tb, status_log],
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
            start_edit_btn,
            confirm_btn,
            discard_btn,
            force_edit_btn,
            keep_draft_btn,
            # Rewrite Mode items to hide
            components[Components.REWRITE_SECTION],
            # Chat Mode items to hide
            components[Components.CHAT_SECTION],
        ]
    )



