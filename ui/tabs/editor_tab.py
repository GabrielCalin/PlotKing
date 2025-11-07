# -*- coding: utf-8 -*-
# ui/tabs/editor_tab.py — control panel compact, all components grouped & top-aligned

import gradio as gr
import ui.editor_handlers as H


def render_editor_tab(sections_epoch):
    """Render the Editor tab (manual editing mode only)."""

    # ====== States ======
    selected_section = gr.State(None)
    current_md = gr.State("")
    draft_text = gr.State("")
    validation_msg = gr.State("")
    pending_plan = gr.State(None)

    # ---- (1) Main Layout: two-column row ----
    with gr.Row(elem_id="editor-main", equal_height=False):
        # ---- (1a) Left Column: Compact Control Panel ----
        with gr.Column(scale=1, min_width=280, elem_classes=["tight-group"]):

            section_dropdown = gr.Dropdown(
                label="Section",
                choices=[],
                value=None,
                interactive=True,
            )

            mode_radio = gr.Radio(
                label="Editing Mode",
                choices=["View", "Manual"],
                value="View",
                interactive=True,
            )

            # butoanele direct sub mode_radio
            start_edit_btn = gr.Button("✍️ Start Editing", variant="primary", visible=False)
            confirm_btn = gr.Button("✅ Confirm Edit", visible=False)
            discard_btn = gr.Button("🗑️ Discard", visible=False)

        # ---- (1b) Right Column: Viewer / Editor ----
        with gr.Column(scale=3):
            viewer_md = gr.Markdown(
                value="_Nothing selected_",
                elem_id="editor-viewer",
                height=480,
            )
            editor_tb = gr.Textbox(
                label="Edit Section",
                lines=20,
                visible=False,
                interactive=True,
            )

    # ---- (2) Validation Area ----
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

    # ---- (3) Status Strip ----
    status_strip = gr.Markdown("_Ready._", elem_id="editor-status")

    # ====== Helper functions ======

    def _refresh_sections(_):
        sections = H.editor_list_sections()
        default = "Expanded Plot" if "Expanded Plot" in sections else (sections[0] if sections else None)
        return gr.update(choices=sections, value=default)

    def _load_section_content(name):
        if not name:
            return "_Empty_", None, "", "View"
        text = H.editor_get_section_content(name) or "_Empty_"
        return text, name, text, "View"

    def _toggle_mode(mode):
        return gr.update(visible=(mode == "Manual")), f"Mode changed to {mode}."

    def _start_edit(curr_text):
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=True, value=curr_text),
            gr.update(interactive=False),
            "Editing started.",
        )

    def _confirm_edit(section, draft):
        msg, plan = H.editor_validate(section, draft)
        return (
            msg,
            plan,
            gr.Accordion("🔎 Validation Result", open=True),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(interactive=True),
            f"Validation complete for {section}.",
        )

    def _apply_updates(section, draft, plan):
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
        text = H.editor_get_section_content(section) or "_Empty_"
        return (
            text,
            "", "", None,
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.Accordion("🔎 Validation Result", open=False),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(interactive=True),
            "Changes discarded.",
        )

    # ====== Wiring ======

    sections_epoch.change(fn=_refresh_sections, inputs=[sections_epoch], outputs=[section_dropdown])

    section_dropdown.change(
        fn=_load_section_content,
        inputs=[section_dropdown],
        outputs=[viewer_md, selected_section, current_md, mode_radio],
    )

    mode_radio.change(fn=_toggle_mode, inputs=[mode_radio], outputs=[start_edit_btn, status_strip])

    start_edit_btn.click(
        fn=_start_edit,
        inputs=[current_md],
        outputs=[
            start_edit_btn,
            confirm_btn,
            discard_btn,
            viewer_md,
            editor_tb,
            mode_radio,
            status_strip,
        ],
    )

    confirm_btn.click(
        fn=_confirm_edit,
        inputs=[selected_section, editor_tb],
        outputs=[
            validation_box, pending_plan, accordion,
            apply_updates_btn, continue_btn, discard2_btn,
            start_edit_btn, editor_tb, viewer_md,
            confirm_btn, discard_btn, mode_radio,
            status_strip,
        ],
    )

    apply_updates_btn.click(
        fn=_apply_updates,
        inputs=[selected_section, editor_tb, pending_plan],
        outputs=[
            viewer_md, status_strip,
            apply_updates_btn, continue_btn, discard2_btn,
            accordion, editor_tb, confirm_btn, discard_btn, start_edit_btn,
        ],
    )

    continue_btn.click(
        fn=_continue_edit,
        inputs=[],
        outputs=[
            accordion, apply_updates_btn, continue_btn, discard2_btn,
            editor_tb, confirm_btn, discard_btn, start_edit_btn, status_strip,
        ],
    )

    discard_btn.click(
        fn=_discard,
        inputs=[selected_section],
        outputs=[
            viewer_md, editor_tb, validation_box, pending_plan,
            confirm_btn, discard_btn, apply_updates_btn, continue_btn,
            accordion, viewer_md, editor_tb, start_edit_btn,
            mode_radio, status_strip,
        ],
    )

    discard2_btn.click(
        fn=_discard,
        inputs=[selected_section],
        outputs=[
            viewer_md, editor_tb, validation_box, pending_plan,
            confirm_btn, discard_btn, apply_updates_btn, continue_btn,
            accordion, viewer_md, editor_tb, start_edit_btn,
            mode_radio, status_strip,
        ],
    )

    return section_dropdown
