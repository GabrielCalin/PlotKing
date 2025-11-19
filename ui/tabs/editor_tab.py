# -*- coding: utf-8 -*-
# ui/tabs/editor_tab.py — Editor tab with full empty-state handling and lockable controls

import gradio as gr
import ui.editor_handlers as H
from utils.timestamp import ts_prefix
from utils.logger import merge_logs
from ui.rewrite_presets import REWRITE_PRESETS


def render_editor_tab(editor_sections_epoch, create_sections_epoch):
    """Render the Editor tab (manual editing mode only)."""

    # ====== States ======
    selected_section = gr.State(None)
    current_md = gr.State("")
    pending_plan = gr.State(None)
    status_log = gr.State("")  # pentru append la status_strip
    selected_text = gr.State("")  # textul selectat de user
    selected_indices = gr.State(None)  # [start, end] indices pentru selectie
    original_text_before_rewrite = gr.State("")  # textul original inainte de rewrite

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
                choices=["View", "Manual", "Rewrite"],
                value="View",
                interactive=True,
            )

            start_edit_btn = gr.Button("✍️ Start Editing", variant="primary", visible=False)
            
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
            return "_Empty_", None, "", gr.update(value="View"), ""
        text = H.editor_get_section_content(name) or "_Empty_"
        return text, name, text, gr.update(value="View"), text

    def _toggle_mode(mode, current_log, current_text):
        # Evită duplicatele: verifică dacă ultimul mesaj este deja "Mode changed to"
        last_msg = f"🔄 Mode changed to {mode}."
        if mode == "Rewrite":
            editor_update = gr.update(visible=True, interactive=False, value=current_text) if current_text else gr.update(visible=True, interactive=False)
            viewer_update = gr.update(visible=False)
        elif mode == "Manual":
            editor_update = gr.update(visible=False)
            viewer_update = gr.update(visible=True, value=current_text) if current_text else gr.update(visible=True)
        else:  # View mode
            editor_update = gr.update(visible=False)
            viewer_update = gr.update(visible=True, value=current_text) if current_text else gr.update(visible=True)
        
        if current_log:
            lines = current_log.strip().split("\n")
            if lines:
                # Extrage mesajul din ultima linie (fără timestamp)
                last_line = lines[-1]
                if last_msg in last_line:
                    # Mesajul există deja, nu adăugăm din nou
                    return (
                        gr.update(visible=(mode == "Manual")),
                        gr.update(visible=(mode == "Rewrite")),
                        gr.update(value=current_log),
                        current_log,
                        editor_update,
                        viewer_update,
                    )
                if "Adapting" in last_line or "Validation completed" in last_line:
                    return (
                        gr.update(visible=(mode == "Manual")),
                        gr.update(visible=(mode == "Rewrite")),
                        gr.update(value=current_log),
                        current_log,
                        editor_update,
                        viewer_update,
                    )
        new_log, status_update = _append_status(current_log, last_msg)
        return (
            gr.update(visible=(mode == "Manual")),
            gr.update(visible=(mode == "Rewrite")),
            status_update,
            new_log,
            editor_update,
            viewer_update,
        )

    def _start_edit(curr_text, section, current_log):
        """Switch to edit mode — locks Section + Mode."""
        new_log, status_update = _append_status(current_log, f"✍️ ({section}) Editing started.")
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

    def _confirm_edit(section, draft, current_log, current_mode, current_md):
        """Send text for validation — shows Validation Result in place of buttons."""
        new_log, status_update = _append_status(current_log, f"🔍 ({section}) Validation started.")
        
        # Determine visibility and text based on mode
        if current_mode == "Rewrite":
            editor_visible = False
            viewer_visible = True
            draft_clean = _remove_highlight(current_md) if current_md else draft
            viewer_text = current_md if current_md else draft
        else:  # Manual mode
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
        )
        
        # Apelează validarea (blocant) - folosim draft_clean (fără highlight-uri)
        msg, plan = H.editor_validate(section, draft_clean)
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
            gr.update(visible=False),   # hide Rewrite Section
            gr.update(visible=viewer_visible, value=viewer_text),  # show/hide viewer_md based on mode
            gr.update(visible=editor_visible, interactive=False),  # show/hide Editor based on mode
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
            gr.update(visible=True),    # show Start Editing (will be hidden by _toggle_mode if not Manual mode)
            gr.update(visible=False),   # hide Rewrite Section (will be shown by _toggle_mode if Rewrite mode)
            gr.update(interactive=True),# unlock Mode
            gr.update(interactive=True),# unlock Section
            updated_text,  # update current_md state with the new text
            new_log,
            new_create_epoch,  # bump create_sections_epoch to notify Create tab
        )

    def _apply_updates(section, draft, plan, current_log, create_epoch, current_mode, current_md):
        """
        Aplică modificările și rulează pipeline-ul de editare dacă există secțiuni impactate.
        Este generator dacă există plan, altfel returnează direct.
        """
        # In Rewrite mode, use current_md (without highlights) instead of draft from editor_tb
        if current_mode == "Rewrite" and current_md:
            draft_clean = _remove_highlight(current_md)
            draft_to_save = draft_clean
        else:
            draft_to_save = draft
        
        if plan and isinstance(plan, dict) and plan.get("impacted_sections"):
            base_log = current_log
            current_epoch = create_epoch or 0
            
            # Yield imediat cu draft-ul salvat pentru a actualiza markdown-ul
            new_log, status_update = _append_status(current_log, f"✅ ({section}) Changes saved. Adapting impacted sections...")
            yield (
                gr.update(value=draft_to_save, visible=True),  # afișează draft-ul salvat imediat
                status_update,  # update Process Log
                gr.update(visible=False),   # hide Editor
                gr.update(visible=False),   # hide Validation Title
                gr.update(visible=False),   # hide Validation Box
                gr.update(visible=False),   # hide Apply Updates
                gr.update(visible=False),   # hide Regenerate
                gr.update(visible=False),   # hide Continue Editing
                gr.update(visible=False),   # hide Discard2
                gr.update(visible=False),   # hide Start Editing (pipeline running)
                gr.update(visible=False),   # hide Rewrite Section
                gr.update(value="View", interactive=False),  # set Mode to View and lock
                gr.update(interactive=True),  # allow Section change
                draft_to_save,  # update current_md state with draft (without highlights)
                new_log,  # update status_log state
                current_epoch,  # bump create_sections_epoch
            )
            
            for result in H.editor_apply(section, draft_to_save, plan):
                if isinstance(result, tuple) and len(result) == 8:
                    expanded_plot, chapters_overview, chapters_full, current_text, dropdown, counter, status_log_text, validation_text = result
                    
                    new_log = merge_logs(base_log, status_log_text)
                    current_epoch += 1  # Bump create_sections_epoch at each iteration
                    
                    yield (
                        gr.update(visible=True),  # keep viewer visible, don't change content
                        gr.update(value=new_log, visible=True),  # update Process Log
                        gr.update(visible=False),   # hide Editor
                        gr.update(visible=False),   # hide Validation Title
                        gr.update(visible=False),   # hide Validation Box
                        gr.update(visible=False),   # hide Apply Updates
                        gr.update(visible=False),   # hide Regenerate
                        gr.update(visible=False),   # hide Continue Editing
                        gr.update(visible=False),   # hide Discard2
                        gr.update(visible=False),   # hide Start Editing (pipeline running)
                        gr.update(visible=False),   # hide Rewrite Section
                        gr.update(value="View", interactive=False),  # set Mode to View and lock
                        gr.update(interactive=True),  # allow Section change
                        gr.update(),  # keep current_md state unchanged
                        new_log,  # update status_log state
                        current_epoch,  # bump create_sections_epoch to notify Create tab at each iteration
                    )
            
            if new_log and not new_log.endswith("\n"):
                new_log += "\n"
            new_log, status_update = _append_status(new_log, f"✅ ({section}) Synced and sections adapted.")

            current_epoch += 1  # Bump create_sections_epoch at final yield too
            yield (
                gr.update(visible=True),  # keep viewer visible, don't change content
                gr.update(value=new_log, visible=True),  # update Process Log with final message
                gr.update(visible=False),   # hide Editor
                gr.update(visible=False),   # hide Validation Title
                gr.update(visible=False),   # hide Validation Box
                gr.update(visible=False),   # hide Apply Updates
                gr.update(visible=False),   # hide Regenerate
                gr.update(visible=False),   # hide Continue Editing
                gr.update(visible=False),   # hide Discard2
                gr.update(visible=False),  # hide Start Editing (Mode is set to View after Apply)
                gr.update(visible=False),   # hide Rewrite Section
                gr.update(value="View", interactive=True),  # unlock Mode (pipeline finished)
                gr.update(interactive=True),  # unlock Section (pipeline finished)
                gr.update(),  # keep current_md state unchanged
                new_log,  # update status_log state
                current_epoch,  # bump create_sections_epoch to notify Create tab at final yield
            )
        else:
            # Nu există plan sau secțiuni impactate, doar salvează modificarea
            result = H.editor_apply(section, draft_to_save, plan)
            # editor_apply poate fi generator sau returnează tuple
            if hasattr(result, '__iter__') and not isinstance(result, (str, tuple)):
                # Este generator, dar nu ar trebui să fie în acest caz
                for item in result:
                    pass  # Consumă generator-ul
            
            new_log, status_update = _append_status(current_log, f"✅ ({section}) Synced.")
            new_create_epoch = (create_epoch or 0) + 1  # Bump create_sections_epoch AFTER save completes

            yield (
                gr.update(value=draft_to_save, visible=True),  # update and show Viewer with draft (without highlights)
                gr.update(value=new_log, visible=True),  # update Process Log
                gr.update(visible=False),   # hide Editor
                gr.update(visible=False),   # hide Validation Title
                gr.update(visible=False),   # hide Validation Box
                gr.update(visible=False),   # hide Apply Updates
                gr.update(visible=False),   # hide Regenerate
                gr.update(visible=False),   # hide Continue Editing
                gr.update(visible=False),   # hide Discard2
                gr.update(visible=False),  # hide Start Editing (Mode is set to View after Apply)
                gr.update(visible=False),   # hide Rewrite Section
                gr.update(value="View", interactive=True), # reset Mode to View and unlock
                gr.update(interactive=True), # unlock Section
                draft_to_save,  # update current_md state with draft (without highlights)
                new_log,  # update status_log state
                new_create_epoch,  # bump create_sections_epoch to notify Create tab
            )

    def _continue_edit(section, current_log, current_mode, current_md):
        """Return to editing mode. If Manual mode, show Validate/Discard/Force Edit. If Rewrite mode, return to Rewrite Section."""
        new_log, status_update = _append_status(current_log, f"🔁 ({section}) Continue editing.")
        
        if current_mode == "Rewrite":
            return (
                gr.update(visible=False),   # hide Validation Title
                gr.update(visible=False),   # hide Validation Box
                gr.update(visible=False),   # hide Apply Updates
                gr.update(visible=False),   # hide Regenerate
                gr.update(visible=False),   # hide Continue Editing
                gr.update(visible=False),   # hide Discard2
                gr.update(visible=False),   # hide Validate
                gr.update(visible=False),   # hide Discard
                gr.update(visible=False),   # hide Force Edit
                gr.update(visible=True),    # show Rewrite Section
                gr.update(visible=True, value=current_md),  # show viewer_md with highlighted text
                gr.update(visible=False),   # hide editor_tb
                gr.update(value="Rewrite", interactive=False), # keep Mode locked to Rewrite
                gr.update(interactive=False), # keep Section locked
                status_update,
                new_log,
            )
        else:
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
            )
            
    def _update_instructions_from_preset(preset_name):
        """Update instructions text area based on selected preset."""
        # "None" is now in REWRITE_PRESETS with value "", so we just get it.
        # If preset_name is None (e.g. unselected), we default to empty string or do nothing.
        if preset_name is None:
             return gr.update()
        text = REWRITE_PRESETS.get(preset_name, "")
        return gr.update(value=text)

    def _format_selected_preview(selected_txt):
        """Format selected text preview - first 25 chars + ... if longer."""
        if not selected_txt:
            return ""
        if len(selected_txt) <= 25:
            return selected_txt
        return selected_txt[:25] + "..."

    def _handle_text_selection(evt: gr.SelectData):
        """Handle text selection in editor_tb and store selected text and indices."""
        raw_value = evt.value if hasattr(evt, 'value') else ""
        raw_index = evt.index if hasattr(evt, 'index') else None
        
        if not raw_value or not isinstance(raw_index, (list, tuple)) or len(raw_index) != 2:
            return "", None, "", gr.update(interactive=False)

        start, end = raw_index
        
        # Calculate leading/trailing whitespace
        l_stripped = raw_value.lstrip()
        leading_spaces = len(raw_value) - len(l_stripped)
        
        stripped_value = raw_value.strip()
        trailing_spaces = len(raw_value) - len(raw_value.rstrip())
        
        # Adjust indices
        new_start = start + leading_spaces
        new_end = end - trailing_spaces
        
        # If selection was only whitespace, it becomes empty
        if not stripped_value:
            return "", None, "", gr.update(interactive=False)
            
        preview_text = _format_selected_preview(stripped_value)
        return stripped_value, [new_start, new_end], preview_text, gr.update(interactive=True)

    def _replace_text_with_highlight(full_text, start_idx, end_idx, new_text):
        """Replace selected text with new text and wrap new text in red markdown (line by line)."""
        if start_idx is None or end_idx is None:
            return full_text
        
        before = full_text[:start_idx]
        after = full_text[end_idx:]
        
        # Wrap each line individually to ensure highlighting persists across newlines
        lines = new_text.split('\n')
        highlighted_lines = [f'<span style="color: red;">{line}</span>' if line.strip() else line for line in lines]
        highlighted_new = '\n'.join(highlighted_lines)
        
        return before + highlighted_new + after

    def _remove_highlight(text):
        """Remove red highlighting from text."""
        import re
        # Remove span tags but keep content
        return re.sub(r'<span style="color: red;">(.*?)</span>', r'\1', text, flags=re.DOTALL)

    def _rewrite_handler(section, selected_txt, selected_idx, instructions, current_text, current_log, original_text):
        """Handle rewrite button click - call handler and replace selected text."""
        start_idx, end_idx = selected_idx if isinstance(selected_idx, (list, tuple)) and len(selected_idx) == 2 else (None, None)
        
        original_text = H.editor_get_section_content(section)
        
        new_log, status_update = _append_status(current_log, f"🔄 ({section}) Rewriting selected text...")
        
        # Yield loading state
        yield (
            gr.update(visible=False),  # editor_tb
            gr.update(visible=True, value="🔄 Rewriting..."),  # viewer_md
            gr.update(visible=False),  # rewrite_validate_btn
            gr.update(visible=False),  # rewrite_discard_btn
            gr.update(visible=False),  # rewrite_force_edit_btn
            gr.update(visible=False),  # rewrite_btn
            status_update,
            current_log,
            original_text,
            selected_txt,
            selected_idx,
            original_text,
        )
        
        result = H.editor_rewrite(section, selected_txt, instructions)
        
        if result.get("success"):
            rewritten_text = result.get("edited_text", "")
            new_text_with_highlight = _replace_text_with_highlight(original_text, start_idx, end_idx, rewritten_text)
            final_log, final_status = _append_status(new_log, f"✅ ({section}) Rewrite completed.")
            
            yield (
                gr.update(visible=False),  # editor_tb
                gr.update(visible=True, value=new_text_with_highlight),  # viewer_md
                gr.update(visible=True),   # rewrite_validate_btn
                gr.update(visible=True),   # rewrite_discard_btn
                gr.update(visible=True),   # rewrite_force_edit_btn
                gr.update(visible=True),   # rewrite_btn
                final_status,
                final_log,
                new_text_with_highlight,
                selected_txt,
                selected_idx,
                original_text,
            )
        else:
            message = result.get("message", "Rewrite failed.")
            final_log, final_status = _append_status(new_log, f"❌ ({section}) Rewrite failed: {message}")
            
            # Revert to original text (no highlights)
            yield (
                gr.update(visible=False),  # editor_tb
                gr.update(visible=True, value=original_text),  # viewer_md
                gr.update(visible=False),  # rewrite_validate_btn
                gr.update(visible=False),  # rewrite_discard_btn
                gr.update(visible=False),  # rewrite_force_edit_btn
                gr.update(visible=True),   # rewrite_btn
                final_status,
                final_log,
                original_text,
                selected_txt,
                selected_idx,
                original_text,
            )

    def _rewrite_discard(section, current_log):
        """Discard rewrite changes - switch back to Text Box non-interactive. Always use checkpoint as source of truth."""
        new_log, status_update = _append_status(current_log, f"🗑️ ({section}) Rewrite discarded.")
        clean_text = H.editor_get_section_content(section) or "_Empty_"
        return (
            gr.update(visible=True, value=clean_text, interactive=False),  # editor_tb
            gr.update(visible=False, value=clean_text),  # viewer_md - resetat la textul curat din checkpoint
            gr.update(visible=False),  # rewrite_validate_btn
            gr.update(visible=False),  # rewrite_discard_btn
            gr.update(visible=False),  # rewrite_force_edit_btn
            gr.update(visible=True, interactive=False),  # rewrite_btn - disabled pentru că selected_text este empty
            gr.update(value=""),  # rewrite_selected_preview
            status_update,  # status_strip
            new_log,  # status_log
            "",  # selected_text
            None,  # selected_indices
            clean_text,  # current_md - resetat la textul din checkpoint
            clean_text,  # original_text_before_rewrite - resetat la textul din checkpoint
        )

    def _rewrite_force_edit(section, draft_with_highlight, current_log, create_epoch):
        """Force edit with rewritten text - remove highlight and update checkpoint."""
        draft_clean = _remove_highlight(draft_with_highlight)
        updated_text = H.force_edit(section, draft_clean)
        new_log, status_update = _append_status(current_log, f"⚡ ({section}) Synced (forced from rewrite).")
        new_create_epoch = (create_epoch or 0) + 1
        return (
            gr.update(value=updated_text, visible=True),  # viewer_md
            status_update,  # status_strip
            gr.update(visible=False),  # editor_tb
            gr.update(visible=False),  # validation_title
            gr.update(visible=False),  # validation_box
            gr.update(visible=False),  # apply_updates_btn
            gr.update(visible=False),  # regenerate_btn
            gr.update(visible=False),  # continue_btn
            gr.update(visible=False),  # discard2_btn
            gr.update(visible=False),  # confirm_btn
            gr.update(visible=False),  # discard_btn
            gr.update(visible=False),  # force_edit_btn
            gr.update(visible=False),  # start_edit_btn
            gr.update(visible=False),  # rewrite_section
            gr.update(value="View", interactive=True),  # mode_radio
            gr.update(interactive=True),  # section_dropdown
            updated_text,  # current_md
            new_log,  # status_log
            new_create_epoch,  # create_sections_epoch
            "",  # selected_text
            None,  # selected_indices
        )

    def _rewrite_validate(section, draft_with_highlight, current_log):
        """Validate rewritten text - remove highlight and start validation."""
        draft_clean = _remove_highlight(draft_with_highlight)
        new_log, status_update = _append_status(current_log, f"🔍 ({section}) Validation started (from rewrite).")
        
        yield (
            "",  # validation_box (Markdown)
            None,  # pending_plan (State)
            gr.update(visible=True),  # validation_title (Markdown)
            gr.update(value="🔄 Validating...", visible=True),  # validation_box (Markdown)
            gr.update(visible=False),  # apply_updates_btn (Button)
            gr.update(visible=False),  # regenerate_btn (Button)
            gr.update(visible=False),  # continue_btn (Button)
            gr.update(visible=False),  # discard2_btn (Button)
            gr.update(visible=False),  # rewrite_section (Column)
            gr.update(visible=True, value=draft_with_highlight),  # viewer_md (Markdown) - keep highlights
            gr.update(interactive=False),  # editor_tb (Textbox)
            gr.update(interactive=False),  # mode_radio (Radio)
            gr.update(interactive=False),  # section_dropdown (Dropdown)
            gr.update(value=new_log, visible=True),  # status_strip (Textbox)
            new_log,  # status_log (State)
        )
        
        msg, plan = H.editor_validate(section, draft_clean)
        final_log, _ = _append_status(new_log, f"✅ ({section}) Validation completed.")
        
        yield (
            msg,  # validation_box (Markdown)
            plan,  # pending_plan (State)
            gr.update(visible=True),  # validation_title (Markdown)
            gr.update(value=msg, visible=True),  # validation_box (Markdown)
            gr.update(visible=True),  # apply_updates_btn (Button)
            gr.update(visible=True),  # regenerate_btn (Button)
            gr.update(visible=True),  # continue_btn (Button)
            gr.update(visible=True),  # discard2_btn (Button)
            gr.update(visible=False),  # rewrite_section (Column)
            gr.update(visible=True, value=draft_with_highlight),  # viewer_md (Markdown) - keep highlights
            gr.update(interactive=False),  # editor_tb (Textbox)
            gr.update(interactive=False),  # mode_radio (Radio)
            gr.update(interactive=False),  # section_dropdown (Dropdown)
            gr.update(value=final_log, visible=True),  # status_strip (Textbox)
            final_log,  # status_log (State)
        )

    def _discard_from_manual(section, current_log):
        """Revert changes from Manual edit mode — unlock Section + Mode, show Start Editing button."""
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
            gr.update(visible=True),    # show Start Editing (will be hidden by _toggle_mode if not Manual mode)
            gr.update(visible=False),   # hide Validate
            gr.update(visible=False),   # hide Discard
            gr.update(visible=False),   # hide Force Edit
            gr.update(visible=False),   # hide Rewrite Section (will be shown by _toggle_mode if Rewrite mode)
            gr.update(interactive=True),# unlock Mode
            gr.update(interactive=True),# unlock Section
            status_update,
            new_log,
        )

    def _discard_from_validate(section, current_log):
        """Revert changes from validation — return to View mode with no buttons visible. Always use checkpoint as source of truth."""
        clean_text = H.editor_get_section_content(section) or "_Empty_"
        new_log, status_update = _append_status(current_log, f"🗑️ ({section}) Changes discarded.")
        return (
            gr.update(value=clean_text, visible=True),  # update and show Viewer with clean text from checkpoint
            gr.update(value="", visible=False),   # clear and hide Editor
            gr.update(value="", visible=False),  # clear and hide Validation Box
            None,  # clear pending_plan
            gr.update(visible=False),   # hide Validation Title
            gr.update(visible=False),   # hide Apply Updates
            gr.update(visible=False),   # hide Regenerate
            gr.update(visible=False),   # hide Continue Editing
            gr.update(visible=False),   # hide Discard2
            gr.update(visible=False),   # hide Start Editing (View mode - no buttons)
            gr.update(visible=False),   # hide Validate
            gr.update(visible=False),   # hide Discard
            gr.update(visible=False),   # hide Force Edit
            gr.update(visible=False),   # hide Rewrite Section
            gr.update(value="View", interactive=True),  # set Mode to View and unlock
            gr.update(interactive=True),# unlock Section
            status_update,
            new_log,
            clean_text,  # current_md - resetat la textul curat din checkpoint
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
        outputs=[viewer_md, selected_section, current_md, mode_radio, original_text_before_rewrite],
    )

    editor_tb.select(
        fn=_handle_text_selection,
        inputs=None,
        outputs=[selected_text, selected_indices, rewrite_selected_preview, rewrite_btn],
    )

    preset_dropdown.change(
        fn=_update_instructions_from_preset,
        inputs=[preset_dropdown],
        outputs=[rewrite_instructions_tb]
    )

    mode_radio.change(
        fn=_toggle_mode,
        inputs=[mode_radio, status_log, current_md],
        outputs=[start_edit_btn, rewrite_section, status_strip, status_log, editor_tb, viewer_md]
    )

    start_edit_btn.click(
        fn=_start_edit,
        inputs=[current_md, selected_section, status_log],
        outputs=[
            start_edit_btn,
            rewrite_section,
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
        inputs=[selected_section, editor_tb, status_log, mode_radio, current_md],
        outputs=[
            validation_box, pending_plan,
            validation_title, validation_box,
            apply_updates_btn, regenerate_btn, continue_btn, discard2_btn,
            confirm_btn, discard_btn, force_edit_btn,
            start_edit_btn,
            rewrite_section,
            viewer_md,
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
        inputs=[section_dropdown, editor_tb, pending_plan, status_log, create_sections_epoch, mode_radio, current_md],
        outputs=[
            viewer_md, status_strip,
            editor_tb,
            validation_title, validation_box,
            apply_updates_btn, regenerate_btn, continue_btn, discard2_btn,
            start_edit_btn,
            rewrite_section,
            mode_radio, section_dropdown,
            current_md,  # update current_md state
            status_log,
            create_sections_epoch,  # bump create_sections_epoch to notify Create tab
        ],
        queue=True,
    )

    continue_btn.click(
        fn=_continue_edit,
        inputs=[selected_section, status_log, mode_radio, current_md],
        outputs=[
            validation_title, validation_box,
            apply_updates_btn, regenerate_btn, continue_btn, discard2_btn,
            confirm_btn, discard_btn, force_edit_btn,
            rewrite_section,
            viewer_md,
            editor_tb,
            mode_radio, section_dropdown,
            status_strip,
            status_log,
        ],
    )

    discard_btn.click(
        fn=_discard_from_manual,
        inputs=[selected_section, status_log],
        outputs=[
            viewer_md, editor_tb, validation_box, pending_plan,
            validation_title,
            apply_updates_btn, regenerate_btn, continue_btn, discard2_btn,
            start_edit_btn,
            confirm_btn, discard_btn, force_edit_btn,
            rewrite_section,
            mode_radio, section_dropdown, status_strip,
            status_log,
        ],
    )

    discard2_btn.click(
        fn=_discard_from_validate,
        inputs=[selected_section, status_log],
        outputs=[
            viewer_md, editor_tb, validation_box, pending_plan,
            validation_title,
            apply_updates_btn, regenerate_btn, continue_btn, discard2_btn,
            start_edit_btn,
            confirm_btn, discard_btn, force_edit_btn,
            rewrite_section,
            mode_radio, section_dropdown, status_strip,
            status_log,
            current_md,
        ],
    )

    force_edit_btn.click(
        fn=_force_edit,
        inputs=[selected_section, editor_tb, status_log, create_sections_epoch],
        outputs=[
            viewer_md, status_strip, editor_tb,
            confirm_btn, discard_btn, force_edit_btn, start_edit_btn,
            rewrite_section,
            mode_radio, section_dropdown,
            current_md,  # update current_md state
            status_log,
            create_sections_epoch,  # bump create_sections_epoch to notify Create tab
        ],
    )

    regenerate_btn.click(
        fn=_confirm_edit,
        inputs=[selected_section, editor_tb, status_log, mode_radio, current_md],
        outputs=[
            validation_box, pending_plan,
            validation_title, validation_box,
            apply_updates_btn, regenerate_btn, continue_btn, discard2_btn,
            confirm_btn, discard_btn, force_edit_btn,
            start_edit_btn,
            rewrite_section,
            viewer_md,
            editor_tb,
            mode_radio, section_dropdown,
            status_strip,
            status_log,
        ],
        queue=True,
        show_progress=False,
    )

    rewrite_btn.click(
        fn=_rewrite_handler,
        inputs=[selected_section, selected_text, selected_indices, rewrite_instructions_tb, current_md, status_log, original_text_before_rewrite],
        outputs=[
            editor_tb,
            viewer_md,
            rewrite_validate_btn,
            rewrite_discard_btn,
            rewrite_force_edit_btn,
            rewrite_btn,
            status_strip,
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
        fn=_rewrite_discard,
        inputs=[selected_section, status_log],
        outputs=[
            editor_tb,
            viewer_md,
            rewrite_validate_btn,
            rewrite_discard_btn,
            rewrite_force_edit_btn,
            rewrite_btn,
            rewrite_selected_preview,
            status_strip,
            status_log,
            selected_text,
            selected_indices,
            current_md,
            original_text_before_rewrite,
        ],
    )

    rewrite_force_edit_btn.click(
        fn=_rewrite_force_edit,
        inputs=[selected_section, current_md, status_log, create_sections_epoch],
        outputs=[
            viewer_md,
            status_strip,
            editor_tb,
            validation_title,
            validation_box,
            apply_updates_btn,
            regenerate_btn,
            continue_btn,
            discard2_btn,
            confirm_btn,
            discard_btn,
            force_edit_btn,
            start_edit_btn,
            rewrite_section,
            mode_radio,
            section_dropdown,
            current_md,
            status_log,
            create_sections_epoch,
            selected_text,
            selected_indices,
        ],
    )

    rewrite_validate_btn.click(
        fn=_rewrite_validate,
        inputs=[selected_section, current_md, status_log],
        outputs=[
            validation_box,
            pending_plan,
            validation_title,
            validation_box,
            apply_updates_btn,
            regenerate_btn,
            continue_btn,
            discard2_btn,
            rewrite_section,
            viewer_md,
            editor_tb,
            mode_radio,
            section_dropdown,
            status_strip,
            status_log,
        ],
        queue=True,
        show_progress=False,
    )

    return section_dropdown
