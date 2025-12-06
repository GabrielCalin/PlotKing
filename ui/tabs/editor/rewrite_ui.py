# ui/tabs/editor/rewrite_ui.py
import gradio as gr
from ui.tabs.editor.rewrite_presets import REWRITE_PRESETS
from ui.tabs.editor.utils import update_instructions_from_preset
from ui.tabs.editor.constants import Components, States

def create_rewrite_ui():
    """Create UI components for Rewrite mode."""
    with gr.Column(visible=False) as rewrite_section:
        rewrite_selected_preview = gr.Textbox(
            label="Selected Text",
            value="",
            lines=1,
            interactive=False,
            max_lines=1,
        )
        preset_dropdown = gr.Dropdown(
            label="Presets",
            choices=list(REWRITE_PRESETS.keys()),
            value="None",
            interactive=True,
        )
        rewrite_instructions_tb = gr.Textbox(
            label="Rewrite Instructions",
            placeholder="Enter instructions on how to rewrite this section...",
            lines=3,
            interactive=True,
        )
        rewrite_btn = gr.Button("🔄 Rewrite", variant="primary", interactive=False)
        rewrite_validate_btn = gr.Button("✅ Validate", visible=False)
        rewrite_discard_btn = gr.Button("🗑️ Discard", visible=False)
        rewrite_force_edit_btn = gr.Button("⚡ Force Edit", visible=False)
        
    return rewrite_section, rewrite_selected_preview, preset_dropdown, rewrite_instructions_tb, rewrite_btn, rewrite_validate_btn, rewrite_discard_btn, rewrite_force_edit_btn

def create_rewrite_handlers(components, states):
    """Wire events for Rewrite mode components."""
    from ui.tabs.editor.rewrite import handle_text_selection, rewrite_handler, rewrite_discard, rewrite_force_edit, rewrite_validate
    
    rewrite_section = components[Components.REWRITE_SECTION]
    rewrite_selected_preview = components[Components.REWRITE_SELECTED_PREVIEW]
    preset_dropdown = components[Components.PRESET_DROPDOWN]
    rewrite_instructions_tb = components[Components.REWRITE_INSTRUCTIONS_TB]
    rewrite_btn = components[Components.REWRITE_BTN]
    rewrite_validate_btn = components[Components.REWRITE_VALIDATE_BTN]
    rewrite_discard_btn = components[Components.REWRITE_DISCARD_BTN]
    rewrite_force_edit_btn = components[Components.REWRITE_FORCE_EDIT_BTN]
    
    # Shared components
    editor_tb = components[Components.EDITOR_TB]
    selected_text = states[States.SELECTED_TEXT]
    selected_indices = states[States.SELECTED_INDICES]
    selected_section = states[States.SELECTED_SECTION]
    current_md = states[States.CURRENT_MD]
    status_log = states[States.STATUS_LOG]
    original_text_before_rewrite = states[States.ORIGINAL_TEXT_BEFORE_REWRITE]
    create_sections_epoch = states[States.CREATE_SECTIONS_EPOCH]
    
    editor_tb.select(
        fn=handle_text_selection,
        inputs=None,
        outputs=[selected_text, selected_indices, rewrite_selected_preview, rewrite_btn],
    )

    preset_dropdown.change(
        fn=update_instructions_from_preset,
        inputs=[preset_dropdown],
        outputs=[rewrite_instructions_tb]
    )

    rewrite_btn.click(
        fn=rewrite_handler,
        inputs=[selected_section, selected_text, selected_indices, rewrite_instructions_tb, current_md, status_log, original_text_before_rewrite],
        outputs=[
            editor_tb,
            components[Components.VIEWER_MD],
            rewrite_validate_btn,
            rewrite_discard_btn,
            rewrite_force_edit_btn,
            rewrite_btn,
            components[Components.STATUS_STRIP],
            status_log,
            current_md,
            selected_text,
            selected_indices,
            original_text_before_rewrite,
        ],
        queue=True,
        show_progress=False,
    )

    rewrite_discard_btn.click(
        fn=rewrite_discard,
        inputs=[selected_section, status_log],
        outputs=[
            editor_tb,
            components[Components.VIEWER_MD],
            rewrite_validate_btn,
            rewrite_discard_btn,
            rewrite_force_edit_btn,
            rewrite_btn,
            rewrite_selected_preview,
            components[Components.STATUS_STRIP],
            status_log,
            selected_text,
            selected_indices,
            current_md,
            original_text_before_rewrite,
        ],
    )

    rewrite_force_edit_btn.click(
        fn=rewrite_force_edit,
        inputs=[selected_section, current_md, status_log, create_sections_epoch],
        outputs=[
            components[Components.VIEWER_MD],
            components[Components.STATUS_STRIP],
            editor_tb,
            components[Components.VALIDATION_TITLE],
            components[Components.VALIDATION_BOX],
            components[Components.APPLY_UPDATES_BTN],
            components[Components.REGENERATE_BTN],
            components[Components.CONTINUE_BTN],
            components[Components.DISCARD2_BTN],
            components[Components.CONFIRM_BTN],
            components[Components.DISCARD_BTN],
            components[Components.FORCE_EDIT_BTN],
            components[Components.START_EDIT_BTN],
            rewrite_section,
            components[Components.MODE_RADIO],
            components[Components.SECTION_DROPDOWN],
            current_md,
            status_log,
            create_sections_epoch,
            selected_text,
            selected_indices,
            components[Components.STATUS_ROW],
        ],
    )

    rewrite_validate_btn.click(
        fn=rewrite_validate,
        inputs=[selected_section, current_md, status_log],
        outputs=[
            components[Components.VALIDATION_BOX],
            states[States.PENDING_PLAN],
            components[Components.VALIDATION_TITLE],
            components[Components.VALIDATION_BOX],
            components[Components.APPLY_UPDATES_BTN],
            components[Components.REGENERATE_BTN],
            components[Components.CONTINUE_BTN],
            components[Components.DISCARD2_BTN],
            rewrite_section,
            components[Components.VIEWER_MD],
            editor_tb,
            components[Components.MODE_RADIO],
            components[Components.SECTION_DROPDOWN],
            components[Components.STATUS_STRIP],
            status_log,
        ],
        queue=True,
        show_progress=False,
    )



