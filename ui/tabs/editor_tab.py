# -*- coding: utf-8 -*-
# ui/tabs/editor_tab.py — Editor tab with full empty-state handling and lockable controls

import gradio as gr
import ui.editor_handlers as H
from utils.timestamp import ts_prefix
from utils.logger import merge_logs


def render_editor_tab(editor_sections_epoch, create_sections_epoch):
    """Render the Editor tab (manual editing mode only)."""

    # ====== States ======
    selected_section = gr.State(None)
    current_md = gr.State("")
    pending_plan = gr.State(None)
    status_log = gr.State("")  # pentru append la status_strip

    # ---- (0) Empty state message (visible by default) ----
    empty_msg = gr.Markdown(
        "📚 **Nothing to edit yet!**  \n"
        "Your story world is still blank — go craft one in the *Create* tab! ✨",
        elem_id="editor-empty",
        visible=True,  # visible at startup
    )

    # ---- (1) Main Layout ----
    with gr.Row(elem_id="editor-main", visible=False) as editor_main:
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

            start_edit_btn = gr.Button("✍️ Start Editing", variant="primary", visible=False)
            confirm_btn = gr.Button("✅ Validate", visible=False)
            discard_btn = gr.Button("🗑️ Discard", visible=False)
            force_edit_btn = gr.Button("⚡ Force Edit", visible=False)

            # Validation Result (apare în locul butoanelor Validate/Discard/Force Edit)
            validation_title = gr.Markdown("🔎 **Validation Result**", visible=False)
            validation_box = gr.Markdown(
                value="Validation results will appear here after confirming edits.",
                height=400,
                visible=False,
            )

            with gr.Row(elem_classes=["validation-row"]):
                apply_updates_btn = gr.Button("✅ Apply", scale=1, min_width=0, visible=False)
                regenerate_btn = gr.Button("🔄 Regenerate", scale=1, min_width=0, visible=False)

            with gr.Row(elem_classes=["validation-row"]):
                continue_btn = gr.Button("🔁 Back", scale=1, min_width=0, visible=False)
                discard2_btn = gr.Button("🗑️ Discard", scale=1, min_width=0, visible=False)

        # ---- (1b) Right Column: Viewer / Editor ----
        with gr.Column(scale=3):
            viewer_md = gr.Markdown(
                value="_Nothing selected_",
                elem_id="editor-viewer",
                height=600,
            )
            editor_tb = gr.Textbox(
                label="Edit Section",
                lines=35,
                visible=False,
                interactive=True,
            )

    # ---- (3) Status Strip ----
    status_strip = gr.Textbox(
        label="🧠 Process Log",
        lines=15,
        interactive=False,
        visible=False,
        elem_id="editor-status",
    )

    # ====== Helper functions ======

    def _append_status(current_log, message):
        """Append message to status log with timestamp."""
        new_line = ts_prefix(message) + "\n"
        updated_log = (current_log or "") + new_line
        return updated_log, gr.update(value=updated_log)

    def _infer_section_from_counter(counter: str):
        if not counter:
            return None
        if "Expanded Plot" in counter:
            return "Expanded Plot"
        if "Chapters Overview" in counter:
            return "Chapters Overview"
        if "Chapter " in counter:
            # încearcă să extragi numărul
            import re
            m = re.search(r"Chapter\s+(\d+)", counter)
            if m:
                return f"Chapter {m.group(1)}"
        return None

    def _refresh_sections(_):
        """Repopulate dropdown when editor_sections_epoch changes (Create → Editor sync), or show empty state."""
        sections = H.editor_list_sections()

        if not sections:
            # 🔹 hide everything except empty message
            return (
                gr.update(visible=True),   # show empty_msg
                gr.update(visible=False),  # hide editor_main
                gr.update(visible=False),  # hide status strip
                gr.update(choices=[], value=None),  # hide dropdown
            )

        default = "Expanded Plot" if "Expanded Plot" in sections else (sections[0] if sections else None)
        # show everything normally
        return (
            gr.update(visible=False),  # hide empty_msg
            gr.update(visible=True),   # show editor_main
            gr.update(visible=True),   # show status strip
            gr.update(choices=sections, value=default),  # dropdown update
        )

    def _load_section_content(name):
        if not name:
            return "_Empty_", None, "", gr.update(value="View")
        text = H.editor_get_section_content(name) or "_Empty_"
        return text, name, text, gr.update(value="View")

    def _toggle_mode(mode, current_log):
        # Evită duplicatele: verifică dacă ultimul mesaj este deja "Mode changed to"
        last_msg = f"🔄 Mode changed to {mode}."
        if current_log:
            lines = current_log.strip().split("\n")
            if lines:
                # Extrage mesajul din ultima linie (fără timestamp)
                last_line = lines[-1]
                if last_msg in last_line:
                    # Mesajul există deja, nu adăugăm din nou
                    return gr.update(visible=(mode == "Manual")), gr.update(value=current_log), current_log
                if "Adapting" in last_line or "Validation completed" in last_line:
                    return gr.update(visible=(mode == "Manual")), gr.update(value=current_log), current_log
        new_log, status_update = _append_status(current_log, last_msg)
        return gr.update(visible=(mode == "Manual")), status_update, new_log

    def _start_edit(curr_text, section, current_log):
        """Switch to edit mode — locks Section + Mode."""
        new_log, status_update = _append_status(current_log, f"✍️ ({section}) Editing started.")
        return (
            gr.update(visible=False),     # hide Start
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

    def _confirm_edit(section, draft, current_log):
        """Send text for validation — shows Validation Result in place of buttons."""
        new_log, status_update = _append_status(current_log, f"🔍 ({section}) Validation started.")
        
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
            gr.update(visible=True, interactive=False),  # keep Editor visible but disable editing
            gr.update(interactive=False), # keep Mode locked
            gr.update(interactive=False), # lock Section dropdown
            gr.update(value=new_log, visible=True),  # show Process Log with "Validation started"
            new_log,  # status_log state
        )
        
        # Apelează validarea (blocant)
        msg, plan = H.editor_validate(section, draft)
        final_log, _ = _append_status(new_log, f"✅ ({section}) Validation completed.")
        
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
            gr.update(visible=True, interactive=False),  # keep Editor visible but disable editing
            gr.update(interactive=False), # keep Mode locked
            gr.update(interactive=False), # keep Section locked
            gr.update(value=final_log, visible=True),  # show Process Log with "Validation completed"
            final_log,  # status_log state
        )

    def _force_edit(section, draft, current_log, create_epoch):
        """Apply changes directly without validation — unlocks controls after."""
        updated_text = H.force_edit(section, draft)
        new_log, status_update = _append_status(current_log, f"⚡ ({section}) Synced (forced).")
        new_create_epoch = (create_epoch or 0) + 1  # Bump create_sections_epoch to notify Create tab
        return (
            gr.update(value=updated_text, visible=True),  # update and show Viewer
            status_update,
            gr.update(visible=False),   # hide Editor
            gr.update(visible=False),   # hide Confirm
            gr.update(visible=False),   # hide Discard
            gr.update(visible=False),   # hide Force Edit
            gr.update(visible=True),    # show Start Editing
            gr.update(interactive=True),# unlock Mode
            gr.update(interactive=True),# unlock Section
            updated_text,  # update current_md state with the new text
            new_log,
            new_create_epoch,  # bump create_sections_epoch to notify Create tab
        )

    def _apply_updates(section, draft, plan, current_log):
        """
        Aplică modificările și rulează pipeline-ul de editare dacă există secțiuni impactate.
        Este generator dacă există plan, altfel returnează direct.
        """
        if plan and isinstance(plan, dict) and plan.get("impacted_sections"):
            preview_text = draft
            base_log = current_log
            
            for result in H.editor_apply(section, draft, plan):
                if isinstance(result, tuple) and len(result) == 8:
                    expanded_plot, chapters_overview, chapters_full, current_text, dropdown, counter, status_log_text, validation_text = result
                    adapted_section = _infer_section_from_counter(str(counter))
                    
                    if adapted_section == "Expanded Plot":
                        preview_text = expanded_plot or draft
                    elif adapted_section == "Chapters Overview":
                        preview_text = chapters_overview or draft
                    elif adapted_section and adapted_section.startswith("Chapter "):
                        try:
                            chapter_num = int(adapted_section.split(" ")[1])
                            if 1 <= chapter_num <= len(chapters_full):
                                preview_text = chapters_full[chapter_num - 1] or draft
                        except:
                            pass

                    if adapted_section == section:
                        viewer_update = gr.update(value=preview_text, visible=True)  # update and show Viewer
                    else:
                        viewer_update = gr.update(visible=True)  # keep visible, don't change content
                    
                    new_log = merge_logs(base_log, status_log_text)
                    
                    yield (
                        viewer_update,  # <— înlocuiește gr.update(value=preview_text, visible=True)
                        gr.update(value=new_log, visible=True),  # update Process Log
                        gr.update(visible=False),   # hide Editor
                        gr.update(visible=False),   # hide Validation Title
                        gr.update(visible=False),   # hide Validation Box
                        gr.update(visible=False),   # hide Apply Updates
                        gr.update(visible=False),   # hide Regenerate
                        gr.update(visible=False),   # hide Continue Editing
                        gr.update(visible=False),   # hide Discard2
                        gr.update(visible=False),   # hide Start Editing (pipeline running)
                        gr.update(value="View", interactive=False),  # set Mode to View and lock
                        gr.update(interactive=True),  # allow Section change
                        preview_text,  # update current_md state
                        new_log,  # update status_log state
                    )
            
            if new_log and not new_log.endswith("\n"):
                new_log += "\n"
            new_log, status_update = _append_status(new_log, f"✅ ({section}) Synced and sections adapted.")

            adapted_section = _infer_section_from_counter(str(counter)) if 'counter' in locals() else None
            if adapted_section == section:
                final_viewer_update = gr.update(value=preview_text, visible=True)  # update and show Viewer
            else:
                final_viewer_update = gr.update(visible=True)  # keep visible, don't change content

            yield (
                final_viewer_update,  # <— înlocuiește gr.update(value=preview_text, visible=True)
                gr.update(value=new_log, visible=True),  # update Process Log with final message
                gr.update(visible=False),   # hide Editor
                gr.update(visible=False),   # hide Validation Title
                gr.update(visible=False),   # hide Validation Box
                gr.update(visible=False),   # hide Apply Updates
                gr.update(visible=False),   # hide Regenerate
                gr.update(visible=False),   # hide Continue Editing
                gr.update(visible=False),   # hide Discard2
                gr.update(visible=False),  # hide Start Editing (Mode is set to View after Apply)
                gr.update(value="View", interactive=True),  # unlock Mode (pipeline finished)
                gr.update(interactive=True),  # unlock Section (pipeline finished)
                preview_text,  # update current_md state
                new_log,  # update status_log state
            )
        else:
            # Nu există plan sau secțiuni impactate, doar salvează modificarea
            result = H.editor_apply(section, draft, plan)
            # editor_apply poate fi generator sau returnează tuple
            if hasattr(result, '__iter__') and not isinstance(result, (str, tuple)):
                # Este generator, dar nu ar trebui să fie în acest caz
                for item in result:
                    pass  # Consumă generator-ul
                preview_text = draft
            else:
                # Returnează tuple (saved_text, preview_text)
                saved_text, preview_text = result if isinstance(result, tuple) else (draft, draft)
            
            new_log, status_update = _append_status(current_log, f"✅ ({section}) Synced.")
            return (
                gr.update(value=preview_text, visible=True),  # update and show Viewer
                gr.update(value=new_log, visible=True),  # update Process Log
                gr.update(visible=False),   # hide Editor
                gr.update(visible=False),   # hide Validation Title
                gr.update(visible=False),   # hide Validation Box
                gr.update(visible=False),   # hide Apply Updates
                gr.update(visible=False),   # hide Regenerate
                gr.update(visible=False),   # hide Continue Editing
                gr.update(visible=False),   # hide Discard2
                gr.update(visible=False),  # hide Start Editing (Mode is set to View after Apply)
                gr.update(interactive=True), # unlock Mode
                gr.update(interactive=True), # unlock Section
                preview_text,  # update current_md state with the new text
                new_log,  # update status_log state
            )

    def _continue_edit(section, current_log):
        """Return to editing mode with Validate/Discard/Force Edit buttons."""
        new_log, status_update = _append_status(current_log, f"🔁 ({section}) Continue editing.")
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
            gr.update(visible=True, interactive=True),  # show Editor and enable editing
            gr.update(interactive=False), # keep Mode locked
            gr.update(interactive=False), # keep Section locked
            status_update,
            new_log,
        )

    def _discard(section, current_log):
        """Revert changes — unlock Section + Mode."""
        text = H.editor_get_section_content(section) or "_Empty_"
        new_log, status_update = _append_status(current_log, f"🗑️ ({section}) Changes discarded.")
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
            gr.update(visible=True),    # show Start Editing
            gr.update(visible=False),   # hide Validate
            gr.update(visible=False),   # hide Discard
            gr.update(visible=False),   # hide Force Edit
            gr.update(interactive=True),# unlock Mode
            gr.update(interactive=True),# unlock Section
            status_update,
            new_log,
        )

    # ====== Wiring ======

    # ---- Sincronizare Create → Editor: refresh Editor tab când Create modifică checkpoint ----
    editor_sections_epoch.change(
        fn=_refresh_sections,
        inputs=[editor_sections_epoch],
        outputs=[
            empty_msg,        # (1)
            editor_main,      # (2)
            status_strip,     # (3)
            section_dropdown, # actualizare dropdown
        ],
    )

    section_dropdown.change(
        fn=_load_section_content,
        inputs=[section_dropdown],
        outputs=[viewer_md, selected_section, current_md, mode_radio],
    )

    mode_radio.change(fn=_toggle_mode, inputs=[mode_radio, status_log], outputs=[start_edit_btn, status_strip, status_log])

    start_edit_btn.click(
        fn=_start_edit,
        inputs=[current_md, selected_section, status_log],
        outputs=[
            start_edit_btn,
            confirm_btn,
            discard_btn,
            force_edit_btn,
            viewer_md,
            editor_tb,
            mode_radio,
            section_dropdown,
            status_strip,
            status_log,
        ],
    )

    confirm_btn.click(
        fn=_confirm_edit,
        inputs=[selected_section, editor_tb, status_log],
        outputs=[
            validation_box, pending_plan,
            validation_title, validation_box,
            apply_updates_btn, regenerate_btn, continue_btn, discard2_btn,
            confirm_btn, discard_btn, force_edit_btn,
            start_edit_btn,
            editor_tb,
            mode_radio, section_dropdown,
            status_strip,
            status_log,
        ],
        queue=True,
        show_progress=False,
    )

    apply_updates_btn.click(
        fn=_apply_updates,
        inputs=[section_dropdown, editor_tb, pending_plan, status_log],
        outputs=[
            viewer_md, status_strip,
            editor_tb,
            validation_title, validation_box,
            apply_updates_btn, regenerate_btn, continue_btn, discard2_btn,
            start_edit_btn,
            mode_radio, section_dropdown,
            current_md,  # update current_md state
            status_log,
        ],
        queue=True,
    )

    continue_btn.click(
        fn=_continue_edit,
        inputs=[selected_section, status_log],
        outputs=[
            validation_title, validation_box,
            apply_updates_btn, regenerate_btn, continue_btn, discard2_btn,
            confirm_btn, discard_btn, force_edit_btn,
            editor_tb,
            mode_radio, section_dropdown,
            status_strip,
            status_log,
        ],
    )

    discard_btn.click(
        fn=_discard,
        inputs=[selected_section, status_log],
        outputs=[
            viewer_md, editor_tb, validation_box, pending_plan,
            validation_title,
            apply_updates_btn, regenerate_btn, continue_btn, discard2_btn,
            start_edit_btn,
            confirm_btn, discard_btn, force_edit_btn,
            mode_radio, section_dropdown, status_strip,
            status_log,
        ],
    )

    discard2_btn.click(
        fn=_discard,
        inputs=[selected_section, status_log],
        outputs=[
            viewer_md, editor_tb, validation_box, pending_plan,
            validation_title,
            apply_updates_btn, regenerate_btn, continue_btn, discard2_btn,
            start_edit_btn,
            confirm_btn, discard_btn, force_edit_btn,
            mode_radio, section_dropdown, status_strip,
            status_log,
        ],
    )

    force_edit_btn.click(
        fn=_force_edit,
        inputs=[selected_section, editor_tb, status_log, create_sections_epoch],
        outputs=[
            viewer_md, status_strip, editor_tb,
            confirm_btn, discard_btn, force_edit_btn, start_edit_btn,
            mode_radio, section_dropdown,
            current_md,  # update current_md state
            status_log,
            create_sections_epoch,  # bump create_sections_epoch to notify Create tab
        ],
    )

    regenerate_btn.click(
        fn=_confirm_edit,
        inputs=[selected_section, editor_tb, status_log],
        outputs=[
            validation_box, pending_plan,
            validation_title, validation_box,
            apply_updates_btn, regenerate_btn, continue_btn, discard2_btn,
            confirm_btn, discard_btn, force_edit_btn,
            start_edit_btn,
            editor_tb,
            mode_radio, section_dropdown,
            status_strip,
            status_log,
        ],
        queue=True,
        show_progress=False,
    )

    return section_dropdown
