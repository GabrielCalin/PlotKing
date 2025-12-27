# -*- coding: utf-8 -*-
# ui/tabs/editor_tab.py — Editor tab with full empty-state handling and lockable controls

import gradio as gr
from handlers.editor.rewrite_presets import REWRITE_PRESETS
from state.checkpoint_manager import get_sections_list, get_section_content

# Import helpers and logic from new modules
from handlers.editor.utils import (
    diff_handler,
)
from state.drafts_manager import DraftsManager
import ui.tabs.editor.manual_ui as Manual
import ui.tabs.editor.rewrite_ui as Rewrite
import ui.tabs.editor.validate_ui as Validate
import ui.tabs.editor.chat_ui as Chat
from handlers.editor.constants import Components, States

def render_editor_tab(editor_sections_epoch, create_sections_epoch):
    """Render the Editor tab (manual editing mode only)."""

    # ====== States ======
    selected_section = gr.State(None)
    pending_plan = gr.State(None)
    status_log = gr.State("")  # pentru append la status_strip
    selected_text = gr.State("")  # textul selectat de user
    selected_indices = gr.State(None)  # [start, end] indices pentru selectie

    # Chat States
    from ui.tabs.editor.chat_ui import PLOT_KING_GREETING
    chat_history = gr.State([{"role": "assistant", "content": PLOT_KING_GREETING}])
    current_view_state = gr.State("Checkpoint") # Checkpoint, Draft, Diff
    generated_drafts_choices = gr.State([])

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
            manual_section, start_edit_btn, confirm_btn, discard_btn, force_edit_btn, keep_draft_btn = Manual.create_manual_ui()
            
            # Rewrite Mode UI
            rewrite_section, rewrite_selected_preview, preset_dropdown, rewrite_instructions_tb, rewrite_btn, rewrite_validate_btn, rewrite_discard_btn, rewrite_force_edit_btn, rewrite_keep_draft_btn = Rewrite.create_rewrite_ui()
            
            # Chat Mode UI
            chat_section, chatbot, chat_input, chat_send_btn, chat_clear_btn, chat_actions_row_1, chat_discard_btn, chat_force_edit_btn, chat_actions_row_2, chat_validate_btn, chat_keep_draft_btn = Chat.create_chat_ui()
            
            # Validation & Draft Review UI
            validation_section, validation_title, validation_box, apply_updates_btn, stop_updates_btn, regenerate_btn, draft_review_panel, original_draft_checkbox, generated_drafts_list, drafts_to_keep_list, mark_keep_btn, btn_draft_accept_all, btn_draft_revert, btn_draft_accept_selected, btn_draft_regenerate, continue_btn, discard2_btn, select_all_gen_btn, unselect_all_gen_btn, select_all_keep_btn, unselect_all_keep_btn, move_to_gen_btn, generated_drafts_choices, keep_drafts_choices = Validate.create_validate_ui(generated_drafts_choices)

        # ---- (1b) Right Column: Viewer / Editor ----
        with gr.Column(scale=3):
            # Status Row (New)
            with gr.Row(elem_classes=["editor-status-row"], visible=True) as status_row:
                status_label = gr.Markdown("**Viewing:** Checkpoint")
                with gr.Row(elem_classes=["editor-status-buttons"]):
                    btn_undo = gr.Button("↩️", size="sm", elem_classes=["status-btn"], visible=False)
                    btn_redo = gr.Button("↪️", size="sm", elem_classes=["status-btn"], visible=False)
                    btn_checkpoint = gr.Button("C", size="sm", elem_classes=["status-btn"], interactive=True)
                    btn_draft = gr.Button("D", size="sm", elem_classes=["status-btn"], visible=False)
                    btn_diff = gr.Button("⚖️", size="sm", elem_classes=["status-btn"], visible=False)
            
            # View Actions Row (Visible only in View mode with Draft)
            with gr.Row(visible=False, elem_classes=["view-actions-row"]) as view_actions_row:
                view_validate_btn = gr.Button("✅ Validate Draft", scale=1, min_width=0)
                view_discard_btn = gr.Button("🗑️ Discard Draft", scale=1, min_width=0)
                view_force_edit_btn = gr.Button("⚡ Force Edit", scale=1, min_width=0)

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
        sections = get_sections_list()

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

    def _calculate_undo_redo(section, draft_type, show_ui):
        from state.undo_manager import UndoManager
        from state.drafts_manager import DraftType
        
        undo_visible = False
        redo_visible = False
        undo_icon = "↩️"
        redo_icon = "↪️"
        counts = None
        
        if show_ui and section and draft_type:
            um = UndoManager()
            if draft_type == DraftType.GENERATED.value:
                undo_icon = "⬅️"
                redo_icon = "➡️"
                counts = um.get_counts(section, draft_type)
            
            undo_visible = um.has_undo(section, draft_type)
            redo_visible = um.has_redo(section, draft_type)
            
        return gr.update(visible=undo_visible, value=undo_icon), gr.update(visible=redo_visible, value=redo_icon), counts

    def _load_section_content(name, pending_plan):
        if not name:
            from ui.tabs.editor.chat_ui import PLOT_KING_GREETING
            initial_greeting = [{"role": "assistant", "content": PLOT_KING_GREETING}]
            return "_Empty_", None, gr.update(value="View"), initial_greeting, \
                   gr.update(visible=True), gr.update(value="**Viewing:** <span style='color:red;'>Checkpoint</span>"), \
                   gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), "Checkpoint", gr.update(visible=False), \
                   gr.update(visible=False), gr.update(visible=False)
        
        # Check if we have a draft for this section
        drafts_mgr = DraftsManager()
        has_draft = drafts_mgr.has(name)
        # Check specifically for USER draft to enable view actions
        is_user_draft = False
        draft_type = drafts_mgr.get_type(name)
        from state.drafts_manager import DraftType
        if draft_type == DraftType.USER.value:
            is_user_draft = True
            
        undo_upd = gr.update(visible=False)
        redo_upd = gr.update(visible=False)
        
        if has_draft:
            text = drafts_mgr.get_content(name)
            view_state = "Draft"
            draft_display_name = DraftsManager.get_display_name(draft_type)
            label = f"**Viewing:** <span style='color:red;'>{draft_display_name}</span>"
        
            # Undo/Redo Logic for Draft view
            # Hide if validation is active, EXCEPT for Generated Drafts
            is_generated_draft = draft_type == DraftType.GENERATED.value
            if pending_plan is not None and (pending_plan == {} or isinstance(pending_plan, dict)) and not is_generated_draft:
                # Validation is active, hide undo/redo buttons (except for Generated Drafts)
                undo_upd = gr.update(visible=False)
                redo_upd = gr.update(visible=False)
                counts = None
            else:
                # Normal logic - calculate undo/redo visibility
                # For Generated Drafts, always calculate even if pending_plan exists
                undo_upd, redo_upd, counts = _calculate_undo_redo(name, draft_type, True)
            
            if counts:
                current, total = counts
                label = f"**Viewing:** <span style='color:red;'>Generated Draft {current}/{total}</span>"

            # Buttons: Checkpoint (visible, enabled), Draft (visible), Diff (visible)
            btn_cp_upd = gr.update(visible=True, interactive=True)
            btn_dr_upd = gr.update(visible=True, interactive=True)
            btn_df_upd = gr.update(visible=True, interactive=True)
            
            if pending_plan:
                # If in validation/review session, HIDE manual actions regardless of drafts
                view_actions_upd = gr.update(visible=False)
            else:
                view_actions_upd = gr.update(visible=is_user_draft)
        else:
            text = get_section_content(name) or "_Empty_"
            view_state = "Checkpoint"
            label = "**Viewing:** <span style='color:red;'>Checkpoint</span>"
            # Buttons: Checkpoint (HIDDEN - no point showing only C), Draft (hidden), Diff (hidden)
            btn_cp_upd = gr.update(visible=False)
            btn_dr_upd = gr.update(visible=False)
            btn_df_upd = gr.update(visible=False)
            view_actions_upd = gr.update(visible=False)
            
        # Reset chat history when loading new section
        from ui.tabs.editor.chat_ui import PLOT_KING_GREETING
        initial_greeting = [{"role": "assistant", "content": PLOT_KING_GREETING}]
        
        return text, name, gr.update(value="View"), initial_greeting, \
               gr.update(visible=True), gr.update(value=label), btn_cp_upd, btn_dr_upd, btn_df_upd, view_state, view_actions_upd, undo_upd, redo_upd




    def _toggle_mode(mode, section, view_state, pending_plan):
        from state.drafts_manager import DraftsManager, DraftType
        drafts_mgr = DraftsManager()
        
        # --- Mode-specific UI updates ---
        # Manual Mode
        manual_section_upd = gr.update(visible=(mode == "Manual"))
        manual_btn_visible = (mode == "Manual")
        start_edit_upd = gr.update(visible=manual_btn_visible)
        confirm_upd = gr.update(visible=False)
        discard_upd = gr.update(visible=False)
        force_edit_upd = gr.update(visible=False)
        keep_manual_draft_upd = gr.update(visible=False)
        
        # Rewrite Mode
        rewrite_section_upd = gr.update(visible=(mode == "Rewrite"))
        # Inside rewrite section
        rewrite_btn_upd = gr.update(visible=(mode == "Rewrite"), interactive=False)
        rewrite_action_upd = gr.update(visible=False)
        rewrite_keep_draft_upd = gr.update(visible=False)
        
        # Chat Mode
        chat_section_upd = gr.update(visible=(mode == "Chat"))
        # Hide chat action buttons when entering Chat mode - they'll be shown only after a draft is created
        chat_actions_row_1_upd = gr.update(visible=False)
        chat_actions_row_2_upd = gr.update(visible=False)
        
        # Validation Section (shown when validation is active or when pending_plan exists)
        validation_section_upd = gr.update(visible=(pending_plan is not None))
        
        # --- Common UI updates (Viewer, Status Bar) ---
        status_row_upd = gr.update(visible=(mode != "Rewrite")) # Hide status bar in Rewrite
        view_actions_upd = gr.update(visible=False)
        viewer_update = gr.update()
        status_label_upd = gr.update()
        
        # Determine viewer content and status bar items
        # Default undo/redo to hidden if no section
        undo_upd = gr.update(visible=False)
        redo_upd = gr.update(visible=False)
        
        if section:
            # Re-fetch what should be shown based on preserved view_state (Checkpoint/Draft/Diff)
            # This is CRITICAL for user's report about preserving view selection.
            content, label, state, undo_upd, redo_upd = _handle_view_switch(view_state, section, pending_plan)
            viewer_update = gr.update(visible=(mode != "Rewrite"), value=content)
            status_label_upd = gr.update(value=label)
            
            # Recalculate View Actions (Validate, Discard, etc.) for View mode
            if mode == "View":
                is_user_draft = drafts_mgr.has_type(section, DraftType.USER.value)
                # Hide if in validation (pending_plan active)
                view_actions_upd = gr.update(visible=is_user_draft and not pending_plan)
        else:
            # Fallback if no section
            viewer_update = gr.update(visible=(mode != "Rewrite"))
            status_label_upd = gr.update()

        editor_update = gr.update(visible=False)
        if mode == "Rewrite":
            # For Rewrite mode, editor_tb should prioritize User draft if available, 
            # consistent with Manual mode requirement "neaparat user trebuie".
            if section and drafts_mgr.has_type(section, DraftType.USER.value):
                content = drafts_mgr.get_content(section, DraftType.USER.value)
            else:
                content = get_section_content(section) or ""
            editor_update = gr.update(visible=True, interactive=False, value=content)

        return (
            manual_section_upd, start_edit_upd, confirm_upd, discard_upd, force_edit_upd, keep_manual_draft_upd,
            rewrite_section_upd, chat_section_upd, validation_section_upd,
            editor_update, viewer_update,
            rewrite_btn_upd, rewrite_action_upd, rewrite_action_upd, rewrite_action_upd, rewrite_keep_draft_upd,
            status_row_upd, view_actions_upd, status_label_upd,
            chat_actions_row_1_upd, chat_actions_row_2_upd,
            undo_upd, redo_upd
        )

    # ====== Dispatchers ======



    def _continue_edit_dispatcher(section, current_log, current_mode, viewer_md=None):
        """Dispatch continue_edit to appropriate module based on mode."""
        from handlers.editor.rewrite import continue_edit as rewrite_continue_edit
        from handlers.editor.chat import continue_edit as chat_continue_edit
        from handlers.editor.manual import continue_edit as manual_continue_edit
        from handlers.editor.view import continue_edit as view_continue_edit
        
        if current_mode == "Rewrite":
            return rewrite_continue_edit(section, current_log, viewer_md)
        elif current_mode == "Chat":
            return chat_continue_edit(section, current_log)
        elif current_mode == "View":
            return view_continue_edit(section, current_log)
        else:
            return manual_continue_edit(section, current_log)

    # ====== Wiring ======
    
    # View Mode Actions Handlers
    from handlers.editor.view import discard_draft_handler, force_edit_draft_handler, validate_draft_handler
    
    view_discard_btn.click(
        fn=discard_draft_handler,
        inputs=[selected_section, status_log],
        outputs=[viewer_md, status_label, current_view_state, btn_checkpoint, btn_draft, btn_diff, status_log, status_strip, view_actions_row, btn_undo, btn_redo]
    )
    
    view_force_edit_btn.click(
        fn=force_edit_draft_handler,
        inputs=[selected_section, status_log, create_sections_epoch],
        outputs=[viewer_md, status_label, current_view_state, btn_checkpoint, btn_draft, btn_diff, status_log, status_strip, create_sections_epoch, view_actions_row, btn_undo, btn_redo]
    )

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
        inputs=[section_dropdown, pending_plan],
        outputs=[viewer_md, selected_section, mode_radio, chat_history, status_row, status_label, btn_checkpoint, btn_draft, btn_diff, current_view_state, view_actions_row, btn_undo, btn_redo],
    )

    def _handle_view_switch(view_type, section, pending_plan=None):
        from state.undo_manager import UndoManager
        from state.drafts_manager import DraftsManager, DraftType

        if not section:
            return gr.update(), "**Viewing:** <span style='color:red;'>Checkpoint</span>", "Checkpoint", gr.update(visible=False), gr.update(visible=False)
            
        original_text = get_section_content(section) or ""
        
        drafts_mgr = DraftsManager()
        has_draft = drafts_mgr.has(section)
        draft_type = drafts_mgr.get_type(section) if has_draft else None
        draft_text = drafts_mgr.get_content(section) if has_draft else ""
        
        # Undo/Redo Logic - hide if validation is active, EXCEPT for Generated Drafts
        # pending_plan can be {} (placeholder) during validation or a dict (actual plan) after validation completes
        is_generated_draft = draft_type == DraftType.GENERATED.value
        if pending_plan is not None and (pending_plan == {} or isinstance(pending_plan, dict)) and not is_generated_draft:
            # Validation is active (either running with placeholder {} or completed with plan dict)
            # Hide undo/redo buttons, EXCEPT for Generated Drafts which should show undo/redo
            undo_upd = gr.update(visible=False)
            redo_upd = gr.update(visible=False)
            counts = None
        else:
            # Normal logic - calculate undo/redo visibility
            # For Generated Drafts, always calculate even if pending_plan exists
            show_undo_redo = (view_type == "Draft" or view_type == "Diff") and has_draft
            undo_upd, redo_upd, counts = _calculate_undo_redo(section, draft_type, show_undo_redo)

        if view_type == "Checkpoint":
            return original_text, "**Viewing:** <span style='color:red;'>Checkpoint</span>", "Checkpoint", undo_upd, redo_upd
            
        elif view_type == "Draft":
            draft_display_name = DraftsManager.get_display_name(draft_type)
            
            # Special Label for Generated with counts
            if counts:
                current, total = counts
                draft_display_name = f"Generated Draft {current}/{total}"
                
            return draft_text, f"**Viewing:** <span style='color:red;'>{draft_display_name}</span>", "Draft", undo_upd, redo_upd
            
        elif view_type == "Diff":
            # Reuse diff_handler logic from utils to get HTML
            diff_res, _ = diff_handler(draft_text, original_text, "⚖️ Diff", diff_label="⚖️ Diff")
            return diff_res['value'], "**Viewing:** <span style='color:red;'>Diff</span>", "Diff", undo_upd, redo_upd
            
        return original_text, "**Viewing:** <span style='color:red;'>Checkpoint</span>", "Checkpoint", undo_upd, redo_upd

    btn_checkpoint.click(
        fn=lambda s, p: _handle_view_switch("Checkpoint", s, p),
        inputs=[selected_section, pending_plan],
        outputs=[viewer_md, status_label, current_view_state, btn_undo, btn_redo]
    )
    
    btn_draft.click(
        fn=lambda s, p: _handle_view_switch("Draft", s, p),
        inputs=[selected_section, pending_plan],
        outputs=[viewer_md, status_label, current_view_state, btn_undo, btn_redo]
    )
    
    btn_diff.click(
        fn=lambda s, p: _handle_view_switch("Diff", s, p),
        inputs=[selected_section, pending_plan],
        outputs=[viewer_md, status_label, current_view_state, btn_undo, btn_redo]
    )


    mode_radio.change(
        fn=_toggle_mode,
        inputs=[mode_radio, selected_section, current_view_state, pending_plan],
        outputs=[
            manual_section, start_edit_btn, confirm_btn, discard_btn, force_edit_btn, keep_draft_btn,
            rewrite_section, chat_section, validation_section, editor_tb, viewer_md, 
            rewrite_btn, rewrite_validate_btn, rewrite_discard_btn, rewrite_force_edit_btn, rewrite_keep_draft_btn, 
            status_row, view_actions_row, status_label,
            chat_actions_row_1, chat_actions_row_2,
            btn_undo, btn_redo
        ]
    )
    
    # Chat Input Change Event to toggle Send button - MOVED TO CHAT HANDLERS

    # Call handler creators
    
    # Components dictionary for passing to handlers
    components = {
        Components.SECTION_DROPDOWN: section_dropdown,
        Components.MODE_RADIO: mode_radio,
        Components.MANUAL_SECTION: manual_section,
        Components.START_EDIT_BTN: start_edit_btn,
        Components.CONFIRM_BTN: confirm_btn,
        Components.DISCARD_BTN: discard_btn,
        Components.FORCE_EDIT_BTN: force_edit_btn,
        Components.KEEP_DRAFT_BTN: keep_draft_btn,
        Components.REWRITE_SECTION: rewrite_section,
        Components.REWRITE_SELECTED_PREVIEW: rewrite_selected_preview,
        Components.PRESET_DROPDOWN: preset_dropdown,
        Components.REWRITE_INSTRUCTIONS_TB: rewrite_instructions_tb,
        Components.REWRITE_BTN: rewrite_btn,
        Components.REWRITE_VALIDATE_BTN: rewrite_validate_btn,
        Components.REWRITE_DISCARD_BTN: rewrite_discard_btn,
        Components.REWRITE_FORCE_EDIT_BTN: rewrite_force_edit_btn,
        Components.REWRITE_KEEP_DRAFT_BTN: rewrite_keep_draft_btn,
        Components.CHAT_SECTION: chat_section,
        Components.CHATBOT: chatbot,
        Components.CHAT_INPUT: chat_input,
        Components.CHAT_SEND_BTN: chat_send_btn,
        Components.CHAT_CLEAR_BTN: chat_clear_btn,
        Components.CHAT_ACTIONS_ROW_1: chat_actions_row_1,
        Components.CHAT_DISCARD_BTN: chat_discard_btn,
        Components.CHAT_FORCE_EDIT_BTN: chat_force_edit_btn,
        Components.CHAT_ACTIONS_ROW_2: chat_actions_row_2,
        Components.CHAT_VALIDATE_BTN: chat_validate_btn,
        Components.CHAT_KEEP_DRAFT_BTN: chat_keep_draft_btn,
        Components.VALIDATION_SECTION: validation_section,
        Components.VALIDATION_TITLE: validation_title,
        Components.VALIDATION_BOX: validation_box,
        Components.APPLY_UPDATES_BTN: apply_updates_btn,
        Components.STOP_UPDATES_BTN: stop_updates_btn,
        Components.REGENERATE_BTN: regenerate_btn,
        Components.DRAFT_REVIEW_PANEL: draft_review_panel,
        Components.ORIGINAL_DRAFT_CHECKBOX: original_draft_checkbox,
        Components.GENERATED_DRAFTS_LIST: generated_drafts_list,
        Components.DRAFTS_TO_KEEP_LIST: drafts_to_keep_list,
        Components.MARK_KEEP_BTN: mark_keep_btn,
        Components.BTN_DRAFT_ACCEPT_ALL: btn_draft_accept_all,
        Components.BTN_DRAFT_REVERT: btn_draft_revert,
        Components.BTN_DRAFT_ACCEPT_SELECTED: btn_draft_accept_selected,
        Components.BTN_DRAFT_REGENERATE: btn_draft_regenerate,
        Components.CONTINUE_BTN: continue_btn,
        Components.DISCARD2_BTN: discard2_btn,
        Components.STATUS_ROW: status_row,
        Components.STATUS_LABEL: status_label,
        Components.BTN_CHECKPOINT: btn_checkpoint,
        Components.BTN_DRAFT: btn_draft,
        Components.BTN_DIFF: btn_diff,
        Components.BTN_UNDO: btn_undo,
        Components.BTN_REDO: btn_redo,
        Components.VIEWER_MD: viewer_md,
        Components.EDITOR_TB: editor_tb,
        Components.STATUS_STRIP: status_strip,
        Components.VIEW_VALIDATE_BTN: view_validate_btn,
        Components.VIEW_DISCARD_BTN: view_discard_btn,
        Components.VIEW_FORCE_EDIT_BTN: view_force_edit_btn,
        Components.VIEW_ACTIONS_ROW: view_actions_row,
        Components._CONTINUE_EDIT_DISPATCHER: _continue_edit_dispatcher,
        Components.SELECT_ALL_GEN_BTN: select_all_gen_btn,
        Components.UNSELECT_ALL_GEN_BTN: unselect_all_gen_btn,
        Components.SELECT_ALL_KEEP_BTN: select_all_keep_btn,
        Components.UNSELECT_ALL_KEEP_BTN: unselect_all_keep_btn,
        Components.MOVE_TO_GEN_BTN: move_to_gen_btn,
        Components.MOVE_TO_KEEP_BTN: mark_keep_btn, # Alias mark_keep_btn to standard constant if needed, but ui uses MARK_KEEP_BTN key too
    }
    
    # States dictionary
    states = {
        States.SELECTED_SECTION: selected_section,
        States.PENDING_PLAN: pending_plan,
        States.STATUS_LOG: status_log,
        States.SELECTED_TEXT: selected_text,
        States.SELECTED_INDICES: selected_indices,
        States.CHAT_HISTORY: chat_history,
        States.CURRENT_VIEW_STATE: current_view_state,
        States.CREATE_SECTIONS_EPOCH: create_sections_epoch,
        States.GENERATED_DRAFTS_CHOICES: generated_drafts_choices,
        States.KEEP_DRAFTS_CHOICES: keep_drafts_choices,
    }

    Manual.create_manual_handlers(components, states)
    Rewrite.create_rewrite_handlers(components, states)
    Chat.create_chat_handlers(components, states)
    Validate.create_validate_handlers(components, states)
    
    # Wire Validate Draft here
    view_validate_btn.click(
        fn=validate_draft_handler,
        inputs=[selected_section, status_log],
        # Outputs: UI changes to show Validation Box etc. similar to Manual/Rewrite validate
        outputs=[
             validation_box, pending_plan, validation_title, validation_section, apply_updates_btn, regenerate_btn, continue_btn, discard2_btn,
             viewer_md, editor_tb, mode_radio, section_dropdown, status_strip, status_log, view_actions_row, btn_undo, btn_redo
        ],
        queue=True,
        show_progress=False,
    )

    view_discard_btn.click(
        fn=discard_draft_handler,
        inputs=[selected_section, status_log],
        outputs=[viewer_md, status_label, current_view_state, btn_checkpoint, btn_draft, btn_diff, status_strip, status_log, view_actions_row, btn_undo, btn_redo]
    )
    
    view_force_edit_btn.click(
        fn=force_edit_draft_handler,
        inputs=[selected_section, status_log, create_sections_epoch],
        outputs=[viewer_md, status_label, current_view_state, btn_checkpoint, btn_draft, btn_diff, status_strip, status_log, create_sections_epoch, view_actions_row, btn_undo, btn_redo]
    )

    # Logic: Undo/Redo Handlers
    def _undo_handler(section, view_state):
        from state.undo_manager import UndoManager
        from state.drafts_manager import DraftsManager
        
        dm = DraftsManager()
        if section and dm.has(section):
             dtype = dm.get_type(section)
             if dtype:
                 UndoManager().undo(section, dtype)
        
        # Refresh view
        return _handle_view_switch(view_state, section)

    def _redo_handler(section, view_state):
        from state.undo_manager import UndoManager
        from state.drafts_manager import DraftsManager
        
        dm = DraftsManager()
        if section and dm.has(section):
             dtype = dm.get_type(section)
             if dtype:
                 UndoManager().redo(section, dtype)
        
        # Refresh view
        return _handle_view_switch(view_state, section)

    btn_undo.click(
        fn=_undo_handler,
        inputs=[selected_section, current_view_state],
        outputs=[viewer_md, status_label, current_view_state, btn_undo, btn_redo]
    )

    btn_redo.click(
        fn=_redo_handler,
        inputs=[selected_section, current_view_state],
        outputs=[viewer_md, status_label, current_view_state, btn_undo, btn_redo]
    )

    return section_dropdown
