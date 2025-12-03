# -*- coding: utf-8 -*-
# ui/tabs/editor_tab.py — Editor tab with full empty-state handling and lockable controls

import gradio as gr
import ui.editor_handlers as H
from ui.rewrite_presets import REWRITE_PRESETS

# Import helpers and logic from new modules
from ui.tabs.editor.utils import (
    append_status,
    update_instructions_from_preset,
    diff_handler,
)
import ui.tabs.editor.manual as Manual
import ui.tabs.editor.rewrite as Rewrite
import ui.tabs.editor.validate as Validate
import ui.tabs.editor.chat as Chat

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
    current_drafts = gr.State({})  # {section_name: draft_content}
    
    # Chat States
    chat_history = gr.State([{"role": "assistant", "content": Chat.PLOT_KING_GREETING}])
    initial_text_before_chat = gr.State("")
    current_view_state = gr.State("Checkpoint") # Checkpoint, Draft, Diff

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
                choices=["View", "Manual", "Rewrite", "Chat"],
                value="View",
                interactive=True,
            )

            # Manual Mode UI
            start_edit_btn, confirm_btn, discard_btn, force_edit_btn = Manual.create_manual_ui()
            
            # Rewrite Mode UI
            rewrite_section, rewrite_selected_preview, preset_dropdown, rewrite_instructions_tb, rewrite_btn, rewrite_validate_btn, rewrite_discard_btn, rewrite_force_edit_btn = Rewrite.create_rewrite_ui()
            
            # Chat Mode UI
            chat_section, chatbot, chat_input, chat_send_btn, chat_clear_btn, chat_actions_row_1, chat_discard_btn, chat_force_edit_btn, chat_actions_row_2, chat_validate_btn = Chat.create_chat_ui()
            
            # Validation & Draft Review UI
            validation_title, validation_box, apply_updates_btn, stop_updates_btn, regenerate_btn, draft_review_panel, original_draft_checkbox, generated_drafts_list, btn_draft_accept_all, btn_draft_revert, btn_draft_accept_selected, btn_draft_regenerate, continue_btn, discard2_btn = Validate.create_validate_ui()

        # ---- (1b) Right Column: Viewer / Editor ----
        with gr.Column(scale=3):
            # Status Row (New)
            with gr.Row(elem_classes=["editor-status-row"], visible=True) as status_row:
                status_label = gr.Markdown("**Viewing:** Checkpoint")
                with gr.Row(elem_classes=["editor-status-buttons"]):
                    btn_checkpoint = gr.Button("C", size="sm", elem_classes=["status-btn"], interactive=True)
                    btn_draft = gr.Button("D", size="sm", elem_classes=["status-btn"], visible=False)
                    btn_diff = gr.Button("⚖️", size="sm", elem_classes=["status-btn"], visible=False)

            viewer_md = gr.Markdown(
                value="_Nothing selected_",
                elem_id="editor-viewer",
                height=850,
            )
            # Old viewer_controls removed
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

    def _load_section_content(name, drafts):
        if not name:
            return "_Empty_", None, "", gr.update(value="View"), "", [], "", \
                   gr.update(visible=True), gr.update(value="**Viewing:** <span style='color:red;'>Checkpoint</span>"), \
                   gr.update(interactive=False, visible=False), gr.update(visible=False), gr.update(visible=False), "Checkpoint"
        
        # Check if we have a draft for this section
        has_draft = drafts and name in drafts
        
        if has_draft:
            text = drafts[name]
            view_state = "Draft"
            label = "**Viewing:** <span style='color:red;'>Draft</span>"
            # Buttons: Checkpoint (visible, enabled), Draft (visible), Diff (visible)
            btn_cp_upd = gr.update(visible=True, interactive=True)
            btn_dr_upd = gr.update(visible=True, interactive=True)
            btn_df_upd = gr.update(visible=True, interactive=True)
        else:
            text = H.editor_get_section_content(name) or "_Empty_"
            view_state = "Checkpoint"
            label = "**Viewing:** <span style='color:red;'>Checkpoint</span>"
            # Buttons: Checkpoint (HIDDEN - no point showing only C), Draft (hidden), Diff (hidden)
            btn_cp_upd = gr.update(visible=False)
            btn_dr_upd = gr.update(visible=False)
            btn_df_upd = gr.update(visible=False)
            
        # Reset chat history when loading new section
        initial_greeting = [{"role": "assistant", "content": Chat.PLOT_KING_GREETING}]
        
        return text, name, text, gr.update(value="View"), text, initial_greeting, text, \
               gr.update(visible=True), gr.update(value=label), btn_cp_upd, btn_dr_upd, btn_df_upd, view_state




    def _toggle_mode(mode, current_log, current_text):
        # Evită duplicatele: verifică dacă ultimul mesaj este deja "Mode changed to"
        last_msg = f"🔄 Mode changed to {mode}."
        
        # Default updates
        rewrite_btn_upd = gr.update()
        rewrite_action_upd = gr.update()
        
        # Chat updates defaults
        chat_section_upd = gr.update(visible=False)
        
        if mode == "Rewrite":
            editor_update = gr.update(visible=True, interactive=False, value=current_text) if current_text else gr.update(visible=True, interactive=False)
            viewer_update = gr.update(visible=False)
            status_row_upd = gr.update(visible=False)
            rewrite_btn_upd = gr.update(visible=True, interactive=False)
            rewrite_action_upd = gr.update(visible=False)
        elif mode == "Manual":
            editor_update = gr.update(visible=False) # Keep existing
            viewer_update = gr.update(visible=True, value=current_text) if current_text else gr.update(visible=True) # Keep existing
            status_row_upd = gr.update(visible=True) # Viewer is visible
        elif mode == "Chat":
            editor_update = gr.update(visible=False)
            viewer_update = gr.update(visible=True, value=current_text) if current_text else gr.update(visible=True)
            chat_section_upd = gr.update(visible=True)
            status_row_upd = gr.update(visible=True)
        else:  # View mode
            editor_update = gr.update(visible=False)
            viewer_update = gr.update(visible=True, value=current_text) if current_text else gr.update(visible=True)
            status_row_upd = gr.update(visible=True)
        
        if current_log:
            lines = current_log.strip().split("\n")
            if lines:
                last_line = lines[-1]
                if last_msg in last_line or "Adapting" in last_line or "Validation completed" in last_line:
                    return (
                        gr.update(visible=(mode == "Manual")),
                        gr.update(visible=(mode == "Rewrite")),
                        chat_section_upd,
                        gr.update(value=current_log),
                        current_log,
                        editor_update,
                        viewer_update,
                        rewrite_btn_upd,
                        rewrite_action_upd,
                        rewrite_action_upd,
                        rewrite_action_upd,
                        status_row_upd, # Added
                    )

        new_log, status_update = append_status(current_log, last_msg)
        return (
            gr.update(visible=(mode == "Manual")),
            gr.update(visible=(mode == "Rewrite")),
            chat_section_upd,
            status_update,
            new_log,
            editor_update,
            viewer_update,
            rewrite_btn_upd,
            rewrite_action_upd,
            rewrite_action_upd,
            rewrite_action_upd,
            status_row_upd, # Added
        )

    # ====== Dispatchers ======



    def _continue_edit_dispatcher(section, current_log, current_mode, current_md):
        """Dispatch continue_edit to appropriate module based on mode."""
        if current_mode == "Rewrite":
            return Rewrite.continue_edit(section, current_log, current_md)
        elif current_mode == "Chat":
            return Chat.continue_edit(section, current_log)
        else:
            return Manual.continue_edit(section, current_log)

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
        inputs=[section_dropdown, current_drafts],
        outputs=[viewer_md, selected_section, current_md, mode_radio, original_text_before_rewrite, chat_history, initial_text_before_chat, status_row, status_label, btn_checkpoint, btn_draft, btn_diff, current_view_state],
    )

    def _handle_view_switch(view_type, section, drafts):
        if not section:
            return gr.update(), "**Viewing:** <span style='color:red;'>Checkpoint</span>", "Checkpoint"
            
        original_text = H.editor_get_section_content(section) or ""
        draft_text = drafts.get(section, "") if drafts else ""
        
        if view_type == "Checkpoint":
            return original_text, "**Viewing:** <span style='color:red;'>Checkpoint</span>", "Checkpoint"
        elif view_type == "Draft":
            return draft_text, "**Viewing:** <span style='color:red;'>Draft</span>", "Draft"
        elif view_type == "Diff":
            # Reuse diff_handler logic from utils to get HTML
            # diff_handler returns (viewer_update, btn_update)
            # We call it with diff_btn_label="⚖️ Diff" (which matches diff_label) to get the diff HTML
            diff_res, _ = diff_handler(draft_text, original_text, "⚖️ Diff", diff_label="⚖️ Diff")
            # diff_res is a gr.update(value=html)
            return diff_res['value'], "**Viewing:** <span style='color:red;'>Diff</span>", "Diff"
        return original_text, "**Viewing:** <span style='color:red;'>Checkpoint</span>", "Checkpoint"

    btn_checkpoint.click(
        fn=lambda s, d: _handle_view_switch("Checkpoint", s, d),
        inputs=[selected_section, current_drafts],
        outputs=[viewer_md, status_label, current_view_state]
    )
    
    btn_draft.click(
        fn=lambda s, d: _handle_view_switch("Draft", s, d),
        inputs=[selected_section, current_drafts],
        outputs=[viewer_md, status_label, current_view_state]
    )
    
    btn_diff.click(
        fn=lambda s, d: _handle_view_switch("Diff", s, d),
        inputs=[selected_section, current_drafts],
        outputs=[viewer_md, status_label, current_view_state]
    )


    mode_radio.change(
        fn=_toggle_mode,
        inputs=[mode_radio, status_log, current_md],
        outputs=[start_edit_btn, rewrite_section, chat_section, status_strip, status_log, editor_tb, viewer_md, rewrite_btn, rewrite_validate_btn, rewrite_discard_btn, rewrite_force_edit_btn, status_row]
    )
    
    # Chat Input Change Event to toggle Send button - MOVED TO CHAT HANDLERS

    # Call handler creators
    
    # Components dictionary for passing to handlers
    components = {
        "section_dropdown": section_dropdown,
        "mode_radio": mode_radio,
        "start_edit_btn": start_edit_btn,
        "confirm_btn": confirm_btn,
        "discard_btn": discard_btn,
        "force_edit_btn": force_edit_btn,
        "rewrite_section": rewrite_section,
        "rewrite_selected_preview": rewrite_selected_preview,
        "preset_dropdown": preset_dropdown,
        "rewrite_instructions_tb": rewrite_instructions_tb,
        "rewrite_btn": rewrite_btn,
        "rewrite_validate_btn": rewrite_validate_btn,
        "rewrite_discard_btn": rewrite_discard_btn,
        "rewrite_force_edit_btn": rewrite_force_edit_btn,
        "chat_section": chat_section,
        "chatbot": chatbot,
        "chat_input": chat_input,
        "chat_send_btn": chat_send_btn,
        "chat_clear_btn": chat_clear_btn,
        "chat_actions_row_1": chat_actions_row_1,
        "chat_discard_btn": chat_discard_btn,
        "chat_force_edit_btn": chat_force_edit_btn,
        "chat_actions_row_2": chat_actions_row_2,
        "chat_validate_btn": chat_validate_btn,
        "validation_title": validation_title,
        "validation_box": validation_box,
        "apply_updates_btn": apply_updates_btn,
        "stop_updates_btn": stop_updates_btn,
        "regenerate_btn": regenerate_btn,
        "draft_review_panel": draft_review_panel,
        "original_draft_checkbox": original_draft_checkbox,
        "generated_drafts_list": generated_drafts_list,
        "btn_draft_accept_all": btn_draft_accept_all,
        "btn_draft_revert": btn_draft_revert,
        "btn_draft_accept_selected": btn_draft_accept_selected,
        "btn_draft_regenerate": btn_draft_regenerate,
        "continue_btn": continue_btn,
        "discard2_btn": discard2_btn,
        "status_row": status_row,
        "status_label": status_label,
        "btn_checkpoint": btn_checkpoint,
        "btn_draft": btn_draft,
        "btn_diff": btn_diff,
        "viewer_md": viewer_md,
        "editor_tb": editor_tb,
        "status_strip": status_strip,
        "_continue_edit_dispatcher": _continue_edit_dispatcher, # Pass the function
    }
    
    # States dictionary
    states = {
        "selected_section": selected_section,
        "current_md": current_md,
        "pending_plan": pending_plan,
        "status_log": status_log,
        "selected_text": selected_text,
        "selected_indices": selected_indices,
        "original_text_before_rewrite": original_text_before_rewrite,
        "current_drafts": current_drafts,
        "chat_history": chat_history,
        "initial_text_before_chat": initial_text_before_chat,
        "current_view_state": current_view_state,
        "create_sections_epoch": create_sections_epoch,
    }

    Manual.create_manual_handlers(components, states)
    Rewrite.create_rewrite_handlers(components, states)
    Chat.create_chat_handlers(components, states)
    Validate.create_validate_handlers(components, states)

    return section_dropdown
