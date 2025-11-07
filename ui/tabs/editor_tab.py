# -*- coding: utf-8 -*-
# ui/tabs/editor_tab.py — MVP Manual Editing (sincronizat prin sections_epoch)

import gradio as gr
import ui.editor_handlers as H  # logica specifică editorului


def render_editor_tab(sections_epoch):
    """Render the Editor tab (manual editing mode only)."""

    # ====== States ======
    selected_section = gr.State(None)
    current_md = gr.State("")
    draft_text = gr.State("")
    validation_msg = gr.State("")
    pending_plan = gr.State(None)

    # ====== Layout ======
    gr.Markdown("## ✏️ Editor")

    # ---- (1) Sticky Header — Section Picker ----
    with gr.Row(elem_id="editor-header", elem_classes=["sticky-header"]):
        section_dropdown = gr.Dropdown(
            label="Select Section",
            choices=[],
            value=None,
            interactive=True,
            scale=2,
        )

    # ---- (2) Sticky Action Bar ----
    with gr.Row(elem_id="editor-actionbar", elem_classes=["sticky-bar"]):
        mode_radio = gr.Radio(
            label="Mode",
            choices=["View", "Manual"],
            value="View",
            interactive=True,
            scale=1,
        )
        start_edit_btn = gr.Button("✍️ Start Editing", variant="primary", scale=1)
        confirm_btn = gr.Button("✅ Confirm Edit", visible=False, scale=1)
        discard_btn = gr.Button("🗑️ Discard", visible=False, scale=1)

    # ---- (3) Work Area ----
    with gr.Column():
        gr.Markdown("### 📖 Content Viewer / Editor")
        viewer_md = gr.Markdown(
            value="_Nothing selected_",
            elem_id="editor-viewer",
            height=400,
        )
        editor_tb = gr.Textbox(
            label="Edit Section",
            lines=20,
            visible=False,
            interactive=True,
        )

    # ---- (4) Validation Area ----
    with gr.Accordion("🔎 Validation Result", open=False, elem_id="editor-validation") as accordion:
        validation_box = gr.Textbox(
            label="Validation Output",
            lines=8,
            interactive=False,
            placeholder="Validation results will appear here after confirming edits.",
        )
        with gr.Row():
            apply_updates_btn = gr.Button("✅ Apply Updates", visible=False)
            continue_btn = gr.Button("🔁 Continue Editing", visible=False)
            discard2_btn = gr.Button("🗑️ Discard", visible=False)

    # ---- (5) Status Strip ----
    status_strip = gr.Markdown("_Ready._", elem_id="editor-status")

    # ====== Helper functions ======

    def _refresh_sections(_):
        """Repopulate dropdown when sections_epoch changes."""
        sections = H.editor_list_sections()
        default = "Expanded Plot" if "Expanded Plot" in sections else (sections[0] if sections else None)
        return gr.update(choices=sections, value=default)

    def _load_section_content(name):
        """Load content of selected section."""
        if not name:
            return "_Empty_", None, "", "Mode: View"
        text = H.editor_get_section_content(name) or "_Empty_"
        return text, name, text, "Mode: View"

    def _start_edit(curr_text):
        """Switch to edit mode."""
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=True, value=curr_text),
            "Editing started.",
        )

    def _confirm_edit(section, draft):
        """Send text for validation."""
        msg, plan = H.editor_validate(section, draft)
        return (
            msg,
            plan,
            gr.Accordion("🔎 Validation Result", open=True),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=True),
            f"Validation complete for {section}.",
        )

    def _apply_updates(section, draft, plan):
        """Apply updates — may trigger pipeline + tab switch."""
        saved_text, preview_text = H.editor_apply(section, draft, plan)
        return (
            preview_text,
            "_Synced._",
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.Accordion("🔎 Validation Result", open=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
        )

    def _continue_edit():
        """Return to editing mode after validation."""
        return (
            gr.Accordion("🔎 Validation Result", open=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=True),
            "Continue editing.",
        )

    def _discard(section):
        """Revert changes."""
        text = H.editor_get_section_content(section) or "_Empty_"
        return (
            text,
            "",
            "",
            None,
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.Accordion("🔎 Validation Result", open=False),
            "Changes discarded.",
        )

    # ====== Wiring ======

    # 🔁 Refresh dropdown automat când sections_epoch se schimbă
    sections_epoch.change(fn=_refresh_sections, inputs=[sections_epoch], outputs=[section_dropdown])

    # 🔄 Când userul selectează o secțiune
    section_dropdown.change(
        fn=_load_section_content,
        inputs=[section_dropdown],
        outputs=[viewer_md, selected_section, current_md, mode_radio],
    )

    # 📝 Start Editing
    start_edit_btn.click(
        fn=_start_edit,
        inputs=[current_md],
        outputs=[start_edit_btn, confirm_btn, discard_btn, editor_tb, status_strip],
    )

    # ✅ Confirm Edit
    confirm_btn.click(
        fn=_confirm_edit,
        inputs=[selected_section, editor_tb],
        outputs=[
            validation_box,
            pending_plan,
            accordion,
            apply_updates_btn,
            continue_btn,
            discard2_btn,
            status_strip,
        ],
    )

    # 💾 Apply Updates
    apply_updates_btn.click(
        fn=_apply_updates,
        inputs=[selected_section, editor_tb, pending_plan],
        outputs=[
            viewer_md,
            status_strip,
            apply_updates_btn,
            continue_btn,
            discard2_btn,
            accordion,
            editor_tb,
            confirm_btn,
            discard_btn,
            start_edit_btn,
        ],
    )

    # 🔁 Continue Editing
    continue_btn.click(
        fn=_continue_edit,
        inputs=[],
        outputs=[
            accordion,
            apply_updates_btn,
            continue_btn,
            discard2_btn,
            editor_tb,
            confirm_btn,
            discard_btn,
            start_edit_btn,
            status_strip,
        ],
    )

    # 🗑️ Discard (ambele locuri)
    discard_btn.click(
        fn=_discard,
        inputs=[selected_section],
        outputs=[
            viewer_md,
            editor_tb,
            validation_box,
            pending_plan,
            confirm_btn,
            discard_btn,
            apply_updates_btn,
            continue_btn,
            accordion,
            status_strip,
        ],
    )

    discard2_btn.click(
        fn=_discard,
        inputs=[selected_section],
        outputs=[
            viewer_md,
            editor_tb,
            validation_box,
            pending_plan,
            confirm_btn,
            discard_btn,
            apply_updates_btn,
            continue_btn,
            accordion,
            status_strip,
        ],
    )

    return section_dropdown
