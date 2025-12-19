# ui/tabs/editor/validate_ui.py
import gradio as gr
from handlers.editor.constants import Components, States

def create_validate_ui():
    """Create UI components for Validation and Draft Review."""
    # Validation Result
    validation_title = gr.Markdown("🔎 **Validation Result**", visible=False)
    validation_box = gr.Markdown(
        value="Validation results will appear here after confirming edits.",
        height=400,
        visible=False,
    )

    with gr.Row(elem_classes=["validation-row"]):
        apply_updates_btn = gr.Button("✅ Apply", scale=1, min_width=0, visible=False)
        stop_updates_btn = gr.Button("🛑 Stop", variant="stop", scale=1, min_width=0, visible=False)
        regenerate_btn = gr.Button("🔄 Regenerate", scale=1, min_width=0, visible=False)
    
    # Draft Review Panel
    with gr.Column(visible=False) as draft_review_panel:
        gr.Markdown("### 📝 Draft Review")
        
        # Original Draft (the manually edited section) - now a checkbox
        gr.Markdown("**Original Draft**")
        original_draft_checkbox = gr.CheckboxGroup(
            label="Originally Edited Section",
            choices=[],
            value=[],
            interactive=True
        )
        
        # Auto-Generated Drafts (impacted sections)
        gr.Markdown("**Auto-Generated Drafts**")
        with gr.Row():
            generated_drafts_list = gr.CheckboxGroup(label="AI-Generated Drafts", choices=[], interactive=True)
        
        with gr.Row():
            drafts_to_keep_list = gr.CheckboxGroup(label="Drafts To Keep (if not accepted)", choices=[], interactive=False)
        
        with gr.Row():
            btn_draft_accept_all = gr.Button("✅ Accept All", size="sm", variant="primary", scale=1, min_width=0)
            btn_draft_revert = gr.Button("❌ Revert All", size="sm", variant="stop", scale=1, min_width=0)
        with gr.Row():
            btn_draft_accept_selected = gr.Button("✔️ Accept Selected", size="sm", scale=1, min_width=0, interactive=False)
            btn_draft_regenerate = gr.Button("🔄 Regenerate Selected", size="sm", scale=1, min_width=0, interactive=False)
        with gr.Row():
            mark_keep_btn = gr.Button("📑 Mark Drafts to Keep", size="sm", scale=1, min_width=0)

    with gr.Row(elem_classes=["validation-row"]):
        continue_btn = gr.Button("🔁 Back", scale=1, min_width=0, visible=False)
        discard2_btn = gr.Button("🗑️ Discard", scale=1, min_width=0, visible=False)
        
    return validation_title, validation_box, apply_updates_btn, stop_updates_btn, regenerate_btn, draft_review_panel, original_draft_checkbox, generated_drafts_list, drafts_to_keep_list, mark_keep_btn, btn_draft_accept_all, btn_draft_revert, btn_draft_accept_selected, btn_draft_regenerate, continue_btn, discard2_btn

def create_validate_handlers(components, states):
    """Wire events for Validation and Draft Review components."""
    from handlers.editor.validate import (
        apply_updates, request_stop, discard_from_validate, regenerate_dispatcher,
        draft_accept_all, draft_revert_all, draft_accept_selected, draft_regenerate_selected,
        update_draft_buttons
    )
    
    apply_updates_btn = components[Components.APPLY_UPDATES_BTN]
    stop_updates_btn = components[Components.STOP_UPDATES_BTN]
    regenerate_btn = components[Components.REGENERATE_BTN]
    continue_btn = components[Components.CONTINUE_BTN]
    discard2_btn = components[Components.DISCARD2_BTN]
    btn_draft_accept_all = components[Components.BTN_DRAFT_ACCEPT_ALL]
    btn_draft_revert = components[Components.BTN_DRAFT_REVERT]
    btn_draft_accept_selected = components[Components.BTN_DRAFT_ACCEPT_SELECTED]
    btn_draft_regenerate = components[Components.BTN_DRAFT_REGENERATE]
    original_draft_checkbox = components[Components.ORIGINAL_DRAFT_CHECKBOX]
    generated_drafts_list = components[Components.GENERATED_DRAFTS_LIST]
    drafts_to_keep_list = components[Components.DRAFTS_TO_KEEP_LIST]
    mark_keep_btn = components[Components.MARK_KEEP_BTN]
    
    # Shared components
    section_dropdown = components[Components.SECTION_DROPDOWN]
    editor_tb = components[Components.EDITOR_TB]
    pending_plan = states[States.PENDING_PLAN]
    status_log = states[States.STATUS_LOG]
    create_sections_epoch = states[States.CREATE_SECTIONS_EPOCH]
    mode_radio = components[Components.MODE_RADIO]
    current_md = states[States.CURRENT_MD]
    selected_section = states[States.SELECTED_SECTION]
    
    apply_updates_btn.click(
        fn=apply_updates,
        inputs=[section_dropdown, pending_plan, status_log, create_sections_epoch, mode_radio, current_md],
        outputs=[
            components[Components.VIEWER_MD], components[Components.STATUS_STRIP],
            editor_tb,
            components[Components.VALIDATION_TITLE], components[Components.VALIDATION_BOX],
            apply_updates_btn, stop_updates_btn, regenerate_btn, continue_btn, discard2_btn,
            components[Components.START_EDIT_BTN],
            components[Components.REWRITE_SECTION],
            mode_radio, section_dropdown,
            current_md,
            status_log,
            create_sections_epoch,
            components[Components.DRAFT_REVIEW_PANEL],
            original_draft_checkbox,
            generated_drafts_list,
            components[Components.STATUS_ROW],
            components[Components.STATUS_LABEL],
            components[Components.BTN_CHECKPOINT],
            components[Components.BTN_DRAFT],
            components[Components.BTN_DIFF],
            states[States.CURRENT_VIEW_STATE],
            drafts_to_keep_list,
            components[Components.KEEP_DRAFT_BTN],
            components[Components.REWRITE_KEEP_DRAFT_BTN],
            components[Components.CHAT_KEEP_DRAFT_BTN],
            components[Components.VIEW_ACTIONS_ROW],
        ],
        queue=True,
    )

    stop_updates_btn.click(
        fn=request_stop,
        inputs=None,
        outputs=[stop_updates_btn],
        queue=False
    )
    
    continue_btn.click(
        fn=components[Components._CONTINUE_EDIT_DISPATCHER],
        inputs=[selected_section, status_log, mode_radio, current_md],
        outputs=[
            components[Components.VALIDATION_TITLE], components[Components.VALIDATION_BOX],
            apply_updates_btn, regenerate_btn, continue_btn, discard2_btn,
            components[Components.CONFIRM_BTN], components[Components.DISCARD_BTN], components[Components.FORCE_EDIT_BTN],
            components[Components.REWRITE_SECTION],
            components[Components.VIEWER_MD],
            editor_tb,
            mode_radio, section_dropdown,
            components[Components.STATUS_STRIP],
            status_log,
            components[Components.CHAT_SECTION],
            components[Components.STATUS_ROW],
            components[Components.KEEP_DRAFT_BTN],
            components[Components.REWRITE_KEEP_DRAFT_BTN],
            components[Components.CHAT_KEEP_DRAFT_BTN],
            components[Components.VIEW_ACTIONS_ROW],
        ],
    )

    discard2_btn.click(
        fn=discard_from_validate,
        inputs=[selected_section, status_log],
        outputs=[
            components[Components.VIEWER_MD], editor_tb, components[Components.VALIDATION_BOX], pending_plan,
            components[Components.VALIDATION_TITLE],
            apply_updates_btn, regenerate_btn, continue_btn, discard2_btn,
            components[Components.START_EDIT_BTN],
            components[Components.CONFIRM_BTN], components[Components.DISCARD_BTN], components[Components.FORCE_EDIT_BTN],
            components[Components.REWRITE_SECTION],
            mode_radio, section_dropdown, components[Components.STATUS_STRIP],
            status_log,
            current_md,
            components[Components.DRAFT_REVIEW_PANEL],
            generated_drafts_list,
            components[Components.STATUS_ROW],
            components[Components.STATUS_LABEL],
            components[Components.BTN_CHECKPOINT],
            components[Components.BTN_DRAFT],
            components[Components.BTN_DIFF],
            states[States.CURRENT_VIEW_STATE],
            original_draft_checkbox,
            drafts_to_keep_list,
            components[Components.KEEP_DRAFT_BTN],
            components[Components.REWRITE_KEEP_DRAFT_BTN],
            components[Components.CHAT_KEEP_DRAFT_BTN],
            components[Components.VIEW_ACTIONS_ROW],
        ],
    )

    regenerate_btn.click(
        fn=regenerate_dispatcher,
        inputs=[selected_section, editor_tb, status_log, mode_radio, current_md],
        outputs=[
            components[Components.VALIDATION_BOX],
            pending_plan,
            components[Components.VALIDATION_TITLE],
            apply_updates_btn,
            regenerate_btn,
            continue_btn,
            discard2_btn,
            components[Components.STATUS_STRIP],
            status_log,
        ],
        queue=True,
        show_progress=False,
    )
    
    # Draft Review Handlers
    from handlers.editor.validate import mark_drafts_to_keep_handler

    mark_keep_btn.click(
        fn=mark_drafts_to_keep_handler,
        inputs=[original_draft_checkbox, generated_drafts_list],
        outputs=[drafts_to_keep_list]
    )

    btn_draft_accept_all.click(
        fn=draft_accept_all,
        inputs=[selected_section, status_log, create_sections_epoch],
        outputs=[components[Components.DRAFT_REVIEW_PANEL], components[Components.STATUS_STRIP], status_log, create_sections_epoch, components[Components.STATUS_ROW], components[Components.STATUS_LABEL], components[Components.BTN_CHECKPOINT], components[Components.BTN_DRAFT], components[Components.BTN_DIFF], states[States.CURRENT_VIEW_STATE], components[Components.VIEWER_MD], current_md, mode_radio, components[Components.VIEW_ACTIONS_ROW]]
    )
    
    btn_draft_revert.click(
        fn=draft_revert_all,
        inputs=[selected_section, status_log],
        outputs=[components[Components.DRAFT_REVIEW_PANEL], components[Components.STATUS_STRIP], status_log, components[Components.STATUS_ROW], components[Components.STATUS_LABEL], components[Components.BTN_CHECKPOINT], components[Components.BTN_DRAFT], components[Components.BTN_DIFF], states[States.CURRENT_VIEW_STATE], components[Components.VIEWER_MD], current_md, mode_radio, components[Components.VIEW_ACTIONS_ROW]]
    )
    
    btn_draft_accept_selected.click(
        fn=draft_accept_selected,
        inputs=[selected_section, original_draft_checkbox, generated_drafts_list, status_log, create_sections_epoch, drafts_to_keep_list], # Passed drafts_to_keep
        outputs=[components[Components.DRAFT_REVIEW_PANEL], components[Components.STATUS_STRIP], status_log, create_sections_epoch, components[Components.STATUS_ROW], components[Components.STATUS_LABEL], components[Components.BTN_CHECKPOINT], components[Components.BTN_DRAFT], components[Components.BTN_DIFF], states[States.CURRENT_VIEW_STATE], components[Components.VIEWER_MD], current_md, mode_radio, components[Components.VIEW_ACTIONS_ROW]]
    )
    
    btn_draft_regenerate.click(
        fn=draft_regenerate_selected,
        inputs=[generated_drafts_list, pending_plan, selected_section, status_log, create_sections_epoch],
        outputs=[components[Components.DRAFT_REVIEW_PANEL], original_draft_checkbox, generated_drafts_list, components[Components.STATUS_STRIP], status_log, create_sections_epoch, components[Components.STATUS_ROW], stop_updates_btn],
        queue=True
    )
    
    # Change handlers for checkboxes to enable/disable buttons
    original_draft_checkbox.change(
        fn=update_draft_buttons,
        inputs=[original_draft_checkbox, generated_drafts_list],
        outputs=[btn_draft_accept_selected, btn_draft_regenerate]
    )
    
    generated_drafts_list.change(
        fn=update_draft_buttons,
        inputs=[original_draft_checkbox, generated_drafts_list],
        outputs=[btn_draft_accept_selected, btn_draft_regenerate]
    )



