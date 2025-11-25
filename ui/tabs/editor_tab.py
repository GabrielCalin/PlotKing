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
    selected_indices = gr.State(None)  # [start, end] indices pentru selectie
    selected_indices = gr.State(None)  # [start, end] indices pentru selectie
    original_text_before_rewrite = gr.State("")  # textul original inainte de rewrite
    current_drafts = gr.State({})  # {section_name: draft_content}
    
    # Chat States
    chat_history = gr.State([{"role": "assistant", "content": Chat.PLOT_KING_GREETING}])
    initial_text_before_chat = gr.State("")

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
            
            # Chat Section
            with gr.Column(visible=False) as chat_section:
                chatbot = gr.Chatbot(
                    label="Plot King",
                    value=[{"role": "assistant", "content": Chat.PLOT_KING_GREETING}],
                    height=350,
                    elem_id="editor-chatbot",
                    avatar_images=(None, "https://api.dicebear.com/7.x/bottts/svg?seed=PlotKing"),
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
                    chat_validate_btn = gr.Button("✅ Validate", scale=1, min_width=0)
                    chat_discard_btn = gr.Button("🗑️ Discard", scale=1, min_width=0)
                
                with gr.Row(visible=False) as chat_actions_row_2:
                    chat_force_edit_btn = gr.Button("⚡ Force Edit", scale=1, min_width=0)
                    chat_diff_btn = gr.Button("⚖️ Diff", scale=1, min_width=0)

            # Manual Mode Section
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
                stop_updates_btn = gr.Button("🛑 Stop", variant="stop", scale=1, min_width=0, visible=False)
                regenerate_btn = gr.Button("🔄 Regenerate", scale=1, min_width=0, visible=False)
            
            # Draft Review Panel
            with gr.Column(visible=False) as draft_review_panel:
                gr.Markdown("### 📝 Draft Review")
                draft_section_list = gr.CheckboxGroup(
                    label="Drafts to Apply",
                    choices=[],
                    value=[],
                    interactive=True
                )
                with gr.Row():
                    btn_draft_accept_all = gr.Button("✅ Accept All", variant="primary", scale=1)
                    btn_draft_revert = gr.Button("❌ Revert All", variant="stop", scale=1)
                with gr.Row():
                    btn_draft_accept_selected = gr.Button("✔️ Accept Selected", scale=1)
                    btn_draft_regenerate = gr.Button("🔄 Regenerate Selected", scale=1)

            with gr.Row(elem_classes=["validation-row"]):
                continue_btn = gr.Button("🔁 Back", scale=1, min_width=0, visible=False)
                discard2_btn = gr.Button("🗑️ Discard", scale=1, min_width=0, visible=False)

        # ---- (1b) Right Column: Viewer / Editor ----
        with gr.Column(scale=3):
            viewer_md = gr.Markdown(
                value="_Nothing selected_",
                elem_id="editor-viewer",
                height=850,
            )
            with gr.Row(visible=True) as viewer_controls:
                view_diff_btn = gr.Button("⚖️ Toggle Diff View", size="sm")
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
            return "_Empty_", None, "", gr.update(value="View"), "", [], ""
        
        # Check if we have a draft for this section
        if drafts and name in drafts:
            text = drafts[name]
        else:
            text = H.editor_get_section_content(name) or "_Empty_"
            
        # Reset chat history when loading new section
        initial_greeting = [{"role": "assistant", "content": Chat.PLOT_KING_GREETING}]
        return text, name, text, gr.update(value="View"), text, initial_greeting, text

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
            # Reset buttons when entering Rewrite mode
            rewrite_btn_upd = gr.update(visible=True, interactive=False) # Disabled until selection
            rewrite_action_upd = gr.update(visible=False)
        elif mode == "Manual":
            editor_update = gr.update(visible=False)
            viewer_update = gr.update(visible=True, value=current_text) if current_text else gr.update(visible=True)
        elif mode == "Chat":
            editor_update = gr.update(visible=False)
            viewer_update = gr.update(visible=True, value=current_text) if current_text else gr.update(visible=True)
            chat_section_upd = gr.update(visible=True)
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
                        chat_section_upd,
                        gr.update(value=current_log),
                        current_log,
                        editor_update,
                        viewer_update,
                        rewrite_btn_upd,
                        rewrite_action_upd,
                        rewrite_action_upd,
                        rewrite_action_upd,
                    )
                if "Adapting" in last_line or "Validation completed" in last_line:
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
        )

    # ====== Dispatchers ======

    def _regenerate_dispatcher(section, editor_text, current_log, mode, current_md):
        """
        Handles 'Regenerate' button click.
        Re-runs validation logic based on the current mode and updates ONLY the Validation UI.
        """
        # 1. Common "Loading" State
        new_log, status_update = append_status(current_log, f"🔄 ({section}) Regenerating validation...")
        
        yield (
            gr.update(value="🔄 Validating..."), # validation_box
            None, # pending_plan
            gr.update(visible=True), # validation_title
            gr.update(visible=False), # apply_updates_btn
            gr.update(visible=False), # regenerate_btn
            gr.update(visible=False), # continue_btn
            gr.update(visible=False), # discard2_btn
            status_update, # status_strip
            new_log # status_log
        )
        
        # 2. Determine text to validate
        text_to_validate = ""
        if mode == "Manual":
            text_to_validate = editor_text
        else:
            # Chat and Rewrite modes use current_md state
            text_to_validate = current_md
            
        # 3. Run Validation Logic
        msg, plan = H.editor_validate(section, text_to_validate)
        final_log, final_status = append_status(new_log, f"✅ ({section}) Validation completed.")
        
        # 4. Common "Done" State
        yield (
            gr.update(value=msg), # validation_box
            plan, # pending_plan
            gr.update(visible=True), # validation_title
            gr.update(visible=True), # apply_updates_btn
            gr.update(visible=True), # regenerate_btn
            gr.update(visible=True), # continue_btn
            gr.update(visible=True), # discard2_btn
            final_status, # status_strip
            final_log # status_log
        )

    def _continue_edit_dispatcher(section, current_log, current_mode, current_md):
        """Dispatch continue_edit to appropriate module based on mode."""
        if current_mode == "Rewrite":
            return Rewrite.continue_edit(section, current_log, current_md)
        elif current_mode == "Chat":
            return Chat.continue_edit(section, current_log, current_md)
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
        outputs=[viewer_md, selected_section, current_md, mode_radio, original_text_before_rewrite, chat_history, initial_text_before_chat],
    )

    editor_tb.select(
        fn=Rewrite.handle_text_selection,
        inputs=None,
        outputs=[selected_text, selected_indices, rewrite_selected_preview, rewrite_btn],
    )

    preset_dropdown.change(
        fn=update_instructions_from_preset,
        inputs=[preset_dropdown],
        outputs=[rewrite_instructions_tb]
    )

    mode_radio.change(
        fn=_toggle_mode,
        inputs=[mode_radio, status_log, current_md],
        outputs=[start_edit_btn, rewrite_section, chat_section, status_strip, status_log, editor_tb, viewer_md, rewrite_btn, rewrite_validate_btn, rewrite_discard_btn, rewrite_force_edit_btn]
    )
    
    # Chat Input Change Event to toggle Send button
    chat_input.change(
        fn=lambda x: gr.update(interactive=bool(x.strip())),
        inputs=[chat_input],
        outputs=[chat_send_btn]
    )

    start_edit_btn.click(
        fn=Manual.start_edit,
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
        fn=Manual.confirm_edit,
        inputs=[selected_section, editor_tb, status_log],
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

    def draft_diff_handler(section, drafts, btn_label):
        """Toggle between Draft and Diff view for the current section."""
        if not section or not drafts or section not in drafts:
            return gr.update(), btn_label
            
        draft_content = drafts[section]
        original_content = H.editor_get_section_content(section) or ""
        
        if "Diff" in btn_label:
            # Show Diff
            from ui.tabs.editor.utils import diff_handler
            # diff_handler expects (current, original, btn)
            # We want to show what changed in draft vs original
            # So draft is "current", original is "original"
            # But diff_handler logic might be inverted depending on usage.
            # Usually diff(new, old) -> shows changes in new relative to old.
            
            # Let's check utils.py diff_handler signature
            # It takes (current_text, original_text, btn)
            # And returns (viewer_update, btn_update)
            
            return diff_handler(draft_content, original_content, btn_label)
        else:
            # Show Draft (Clean)
            return gr.update(value=draft_content), "⚖️ Toggle Diff View"

    view_diff_btn.click(
        fn=draft_diff_handler,
        inputs=[selected_section, current_drafts, view_diff_btn],
        outputs=[viewer_md, view_diff_btn]
    )

    apply_updates_btn.click(
        fn=Validate.apply_updates,
        inputs=[section_dropdown, editor_tb, pending_plan, status_log, create_sections_epoch, mode_radio, current_md],
        outputs=[
            viewer_md, status_strip,
            editor_tb,
            validation_title, validation_box,
            apply_updates_btn, stop_updates_btn, regenerate_btn, continue_btn, discard2_btn,
            start_edit_btn,
            rewrite_section,
            mode_radio, section_dropdown,
            current_md,  # update current_md state
            status_log,
            create_sections_epoch,  # bump create_sections_epoch to notify Create tab
            draft_review_panel, # Added
            draft_section_list, # Added
            current_drafts, # Added
        ],
        queue=True,
    )

    stop_updates_btn.click(
        fn=Validate.request_stop,
        inputs=None,
        outputs=[stop_updates_btn],
        queue=False
    )
    
    continue_btn.click(
        fn=_continue_edit_dispatcher,
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
            chat_section, # Added output
        ],
    )

    discard_btn.click(
        fn=Manual.discard_from_manual,
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
        fn=Validate.discard_from_validate,
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
            draft_review_panel, # Added
            draft_section_list, # Added
            current_drafts, # Added
        ],
    )

    force_edit_btn.click(
        fn=Manual.force_edit,
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
        fn=_regenerate_dispatcher,
        inputs=[selected_section, editor_tb, status_log, mode_radio, current_md],
        outputs=[
            validation_box,
            pending_plan,
            validation_title,
            apply_updates_btn,
            regenerate_btn,
            continue_btn,
            discard2_btn,
            status_strip,
            status_log,
        ],
        queue=True,
        show_progress=False,
    )

    rewrite_btn.click(
        fn=Rewrite.rewrite_handler,
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
        fn=Rewrite.rewrite_discard,
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
        fn=Rewrite.rewrite_force_edit,
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
        fn=Rewrite.rewrite_validate,
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
    
    # Draft Review Handlers
    btn_draft_accept_all.click(
        fn=Validate.draft_accept_all,
        inputs=[current_drafts, status_log, create_sections_epoch],
        outputs=[draft_review_panel, status_strip, status_log, create_sections_epoch, current_drafts]
    )
    
    btn_draft_revert.click(
        fn=Validate.draft_revert_all,
        inputs=[status_log],
        outputs=[draft_review_panel, status_strip, status_log, current_drafts]
    )
    
    btn_draft_accept_selected.click(
        fn=Validate.draft_accept_selected,
        inputs=[draft_section_list, current_drafts, status_log, create_sections_epoch],
        outputs=[draft_review_panel, draft_section_list, status_strip, status_log, create_sections_epoch, current_drafts]
    )
    
    btn_draft_regenerate.click(
        fn=Validate.draft_regenerate_selected,
        inputs=[draft_section_list, current_drafts, pending_plan, selected_section, status_log, create_sections_epoch],
        outputs=[draft_review_panel, status_strip, status_log, create_sections_epoch, current_drafts],
        queue=True
    )
    
    # Chat Event Handlers
    
    chat_send_btn.click(
        fn=Chat.chat_handler,
        inputs=[selected_section, chat_input, chat_history, current_md, initial_text_before_chat, status_log],
        outputs=[
            chat_input,
            chat_history,
            chatbot, # Update chatbot component
            viewer_md,
            chat_actions_row_1, # validate/discard row
            chat_discard_btn, # redundant but for safety if handled individually
            chat_actions_row_2, # force/diff row
            chat_diff_btn,
            status_log,
            status_strip,
            current_md,
            chat_input, # Added output
            chat_clear_btn, # Added output
        ],
        queue=True
    )
    
    # Also trigger send on Enter in chat_input
    chat_input.submit(
        fn=Chat.chat_handler,
        inputs=[selected_section, chat_input, chat_history, current_md, initial_text_before_chat, status_log],
        outputs=[
            chat_input,
            chat_history,
            chatbot, # Update chatbot component
            viewer_md,
            chat_actions_row_1,
            chat_discard_btn,
            chat_actions_row_2,
            chat_diff_btn,
            status_log,
            status_strip,
            current_md,
            chat_input, # Added output
            chat_clear_btn, # Added output
        ],
        queue=True
    )
    
    chat_clear_btn.click(
        fn=Chat.clear_chat,
        inputs=[selected_section, status_log],
        outputs=[chat_history, status_log, status_strip, chatbot]
    )

    chatbot.clear(
        fn=Chat.clear_chat,
        inputs=[selected_section, status_log],
        outputs=[chat_history, status_log, status_strip, chatbot]
    )

    
    chat_diff_btn.click(
        fn=diff_handler,
        inputs=[current_md, initial_text_before_chat, chat_diff_btn],
        outputs=[viewer_md, chat_diff_btn]
    )
    
    chat_validate_btn.click(
        fn=Chat.validate_handler,
        inputs=[selected_section, current_md, status_log],
        outputs=[
            chat_section,
            validation_title,
            validation_box,
            apply_updates_btn,
            regenerate_btn,
            continue_btn,
            discard2_btn,
            viewer_md,
            status_log,
            status_strip,
            pending_plan, # Added output
            chat_diff_btn, # Reset diff button label
        ]
    )
    
    chat_discard_btn.click(
        fn=Chat.discard_handler,
        inputs=[selected_section, status_log],
        outputs=[
            viewer_md,
            chat_actions_row_1,
            chat_discard_btn,
            chat_actions_row_2,
            chat_diff_btn,
            current_md,
            status_log,
            status_strip
        ]
    )
    
    chat_force_edit_btn.click(
        fn=Chat.force_edit_handler,
        inputs=[selected_section, current_md, status_log, create_sections_epoch],
        outputs=[
            viewer_md,
            chat_actions_row_1,
            chat_discard_btn,
            chat_actions_row_2,
            chat_diff_btn,
            current_md,
            status_log,
            status_strip,
            create_sections_epoch
        ]
    )

    return section_dropdown
