import gradio as gr
from ui.tabs.editor.validate_commons import editor_validate
from ui.tabs.editor.utils import append_status, remove_highlight
from ui.tabs.editor.constants import Components, States
from pipeline.checkpoint_manager import get_section_content, save_section

def start_edit(curr_text, section, current_log):
    """Switch to edit mode — locks Section + Mode."""
    new_log, status_update = append_status(current_log, f"✍️ ({section}) Editing started.")
    return (
        gr.update(visible=False),     # hide Start
        gr.update(visible=False),     # hide Rewrite Section
        gr.update(visible=True),      # show Confirm
        gr.update(visible=True),      # show Discard
        gr.update(visible=True),      # show Force Edit
        gr.update(visible=False),     # hide Markdown viewer
        gr.update(visible=True, value=curr_text, interactive=True),  # show Textbox editor and enable editing
        gr.update(interactive=False), # lock Mode
        gr.update(interactive=False), # lock Section
        status_update,
        new_log,
    )

def confirm_edit(section, draft, current_log):
    """Send text for validation — shows Validation Result in place of buttons."""
    new_log, status_update = append_status(current_log, f"🔍 ({section}) Validation started.")
    
    # Manual mode settings
    editor_visible = True
    viewer_visible = False
    draft_clean = draft
    viewer_text = draft
    
    # Yield imediat cu butoanele ascunse și log-ul "Validation started"
    yield (
        "",  # validation_box value (placeholder)
        None,  # pending_plan (placeholder)
        gr.update(visible=True),    # show Validation Title
        gr.update(value="🔄 Validating...", visible=True),   # show Validation Box with loading message
        gr.update(visible=False),   # hide Apply Updates (until validation completes)
        gr.update(visible=False),   # hide Regenerate (until validation completes)
        gr.update(visible=False),   # hide Continue Editing (until validation completes)
        gr.update(visible=False),   # hide Discard2 (until validation completes)
        gr.update(visible=False),   # hide Validate
        gr.update(visible=False),   # hide Discard
        gr.update(visible=False),   # hide Force Edit
        gr.update(visible=False),   # hide Start Editing
        gr.update(visible=False),   # hide Rewrite Section
        gr.update(visible=viewer_visible, value=viewer_text),  # show/hide viewer_md based on mode
        gr.update(visible=editor_visible, interactive=False),  # show/hide Editor based on mode
        gr.update(interactive=False), # keep Mode locked
        gr.update(interactive=False), # lock Section dropdown
        gr.update(value=new_log, visible=True),  # show Process Log with "Validation started"
        new_log,  # status_log state
        gr.update(visible=False), # status_row (hidden)
    )
    
    # Apelează validarea (blocant) - folosim draft_clean (fără highlight-uri)
    msg, plan = editor_validate(section, draft_clean)
    final_log, _ = append_status(new_log, f"✅ ({section}) Validation completed.")
    
    # Yield cu rezultatul validării
    yield (
        msg,  # validation_box value
        plan,  # pending_plan
        gr.update(visible=True),    # show Validation Title
        gr.update(value=msg, visible=True),   # show Validation Box with message
        gr.update(visible=True),    # show Apply Updates
        gr.update(visible=True),    # show Regenerate
        gr.update(visible=True),    # show Continue Editing
        gr.update(visible=True),    # show Discard2
        gr.update(visible=False),   # hide Validate
        gr.update(visible=False),   # hide Discard
        gr.update(visible=False),   # hide Force Edit
        gr.update(visible=False),   # hide Start Editing
        gr.update(visible=False),   # hide Rewrite Section
        gr.update(visible=viewer_visible, value=viewer_text),  # show/hide viewer_md based on mode
        gr.update(visible=editor_visible, interactive=False),  # show/hide Editor based on mode
        gr.update(interactive=False), # keep Mode locked
        gr.update(interactive=False), # keep Section locked
        gr.update(value=final_log, visible=True),  # show Process Log with "Validation completed"
        final_log,  # status_log state
        gr.update(visible=False), # status_row (hidden)
    )

def force_edit(section, draft, current_log, create_epoch):
    """Apply changes directly without validation — unlocks controls after."""
    save_section(section, draft)
    updated_text = draft
    new_log, status_update = append_status(current_log, f"⚡ ({section}) Synced (forced).")
    new_create_epoch = (create_epoch or 0) + 1  # Bump create_sections_epoch to notify Create tab
    return (
        gr.update(value=updated_text, visible=True),  # update and show Viewer
        status_update,
        gr.update(visible=False),   # hide Editor
        gr.update(visible=False),   # hide Confirm
        gr.update(visible=False),   # hide Discard
        gr.update(visible=False),   # hide Force Edit
        gr.update(visible=True),    # show Start Editing (will be hidden by _toggle_mode if not Manual mode)
        gr.update(visible=False),   # hide Rewrite Section (will be shown by _toggle_mode if Rewrite mode)
        gr.update(interactive=True),# unlock Mode
        gr.update(interactive=True),# unlock Section
        updated_text,  # update current_md state with the new text
        new_log,
        new_create_epoch,  # bump create_sections_epoch to notify Create tab
        gr.update(visible=True), # status_row (visible)
    )

def discard_from_manual(section, current_log):
    """Revert changes from Manual edit mode — unlock Section + Mode, show Start Editing button."""
    text = get_section_content(section) or "_Empty_"
    new_log, status_update = append_status(current_log, f"🗑️ ({section}) Changes discarded.")
    return (
        gr.update(value=text, visible=True),  # update and show Viewer
        gr.update(value="", visible=False),   # clear and hide Editor
        gr.update(value="", visible=False),  # clear and hide Validation Box
        None,  # clear pending_plan
        gr.update(visible=False),   # hide Validation Title
        gr.update(visible=False),   # hide Apply Updates
        gr.update(visible=False),   # hide Regenerate
        gr.update(visible=False),   # hide Continue Editing
        gr.update(visible=False),   # hide Discard2
        gr.update(visible=True),    # show Start Editing (will be hidden by _toggle_mode if not Manual mode)
        gr.update(visible=False),   # hide Validate
        gr.update(visible=False),   # hide Discard
        gr.update(visible=False),   # hide Force Edit
        gr.update(visible=False),   # hide Rewrite Section (will be shown by _toggle_mode if Rewrite mode)
        gr.update(interactive=True),# unlock Mode
        gr.update(interactive=True),# unlock Section
        status_update,
        new_log,
        gr.update(visible=True), # status_row (visible)
    )

def continue_edit(section, current_log):
    """Return to editing mode. If Manual mode, show Validate/Discard/Force Edit."""
    new_log, status_update = append_status(current_log, f"🔁 ({section}) Continue editing.")
    
    return (
        gr.update(visible=False),   # hide Validation Title
        gr.update(visible=False),   # hide Validation Box
        gr.update(visible=False),   # hide Apply Updates
        gr.update(visible=False),   # hide Regenerate
        gr.update(visible=False),   # hide Continue Editing
        gr.update(visible=False),   # hide Discard2
        gr.update(visible=True),    # show Validate
        gr.update(visible=True),    # show Discard
        gr.update(visible=True),    # show Force Edit
        gr.update(visible=False),   # hide Rewrite Section
        gr.update(visible=False),   # hide viewer_md
        gr.update(visible=True, interactive=True),  # show Editor and enable editing
        gr.update(interactive=False), # keep Mode locked
        gr.update(interactive=False), # keep Section locked
        status_update,
        new_log,
        gr.update(visible=False),   # hide Chat Section
        gr.update(visible=False),   # status_row (hidden)
    )

def create_manual_ui():
    """Create UI components for Manual mode."""
    start_edit_btn = gr.Button("✍️ Start Editing", variant="primary", visible=False)
    confirm_btn = gr.Button("✅ Validate", visible=False)
    discard_btn = gr.Button("🗑️ Discard", visible=False)
    force_edit_btn = gr.Button("⚡ Force Edit", visible=False)
    
    return start_edit_btn, confirm_btn, discard_btn, force_edit_btn

def create_manual_handlers(components, states):
    """Wire events for Manual mode components."""
    start_edit_btn = components[Components.START_EDIT_BTN]
    confirm_btn = components[Components.CONFIRM_BTN]
    discard_btn = components[Components.DISCARD_BTN]
    force_edit_btn = components[Components.FORCE_EDIT_BTN]
    
    # Shared components
    current_md = states[States.CURRENT_MD]
    selected_section = states[States.SELECTED_SECTION]
    status_log = states[States.STATUS_LOG]
    editor_tb = components[Components.EDITOR_TB]
    create_sections_epoch = states[States.CREATE_SECTIONS_EPOCH]
    
    start_edit_btn.click(
        fn=lambda *args: (*start_edit(*args), gr.update(visible=False)), # Wrap to hide status row
        inputs=[current_md, selected_section, status_log],
        outputs=[
            start_edit_btn,
            components[Components.REWRITE_SECTION],
            confirm_btn,
            discard_btn,
            force_edit_btn,
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
            components[Components.APPLY_UPDATES_BTN], components[Components.REGENERATE_BTN], components[Components.CONTINUE_BTN], components[Components.DISCARD2_BTN],
            confirm_btn, discard_btn, force_edit_btn,
            start_edit_btn,
            components[Components.REWRITE_SECTION],
            components[Components.VIEWER_MD],
            editor_tb,
            components[Components.MODE_RADIO], components[Components.SECTION_DROPDOWN],
            components[Components.STATUS_STRIP],
            status_log,
            components[Components.STATUS_ROW],
        ],
        queue=True,
        show_progress=False,
    )

    discard_btn.click(
        fn=discard_from_manual,
        inputs=[selected_section, status_log],
        outputs=[
            components[Components.VIEWER_MD], editor_tb, components[Components.VALIDATION_BOX], states[States.PENDING_PLAN],
            components[Components.VALIDATION_TITLE],
            components[Components.APPLY_UPDATES_BTN], components[Components.REGENERATE_BTN], components[Components.CONTINUE_BTN], components[Components.DISCARD2_BTN],
            start_edit_btn,
            confirm_btn, discard_btn, force_edit_btn,
            components[Components.REWRITE_SECTION],
            components[Components.MODE_RADIO], components[Components.SECTION_DROPDOWN], components[Components.STATUS_STRIP],
            status_log,
            components[Components.STATUS_ROW],
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
            current_md,
            status_log,
            create_sections_epoch,
            components[Components.STATUS_ROW],
        ],
    )
