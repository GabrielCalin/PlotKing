# -*- coding: utf-8 -*-

import gradio as gr
from ui import load_css
from handlers.create.utils import display_selected_chapter
from state.transitions_manager import has_transitions, get_transitions, format_all_transitions
from handlers.create.create_handlers import (
    choose_plot_for_pipeline,
    pre_run_reset_and_controls,
    post_pipeline_controls,
    show_stop_only,
    stop_pipeline,
    show_controls_on_resume_run,
    resume_pipeline,
    refresh_expanded,
    refresh_overview,
    refresh_chapter,
    show_original,
    show_refined,
    show_refined,
    refine_or_clear_dispatcher,
    generate_dispatcher,
    sync_textbox,

    refresh_create_from_checkpoint,
    show_original_wrapper,
    show_refined_wrapper,
    show_chat,

    user_submit_chat_message,
    bot_reply_chat_message,
    bot_reply_chat_message,
    reset_chat_handler,
    
    toggle_transitions_view,
    get_toggle_transitions_visibility,
    pre_refresh_clear_transitions,
)
from handlers.create.project_manager import (
    save_project,
    load_project,
    delete_project,
    new_project,
)
from llm.refine_chat.llm import refine_chat
from pipeline.constants import RUN_MODE_CHOICES
from pipeline.runner_create import generate_book_outline_stream
from llm.refine_plot.llm import refine_plot


def render_create_tab(current_project_label, header_save_btn, editor_sections_epoch, create_sections_epoch):
    header_project = gr.State("")

    # ---- States ----
    plot_state = gr.State("")
    refined_plot_state = gr.State("")
    current_mode = gr.State("original")
    chapters_state = gr.State([])
    chat_history = gr.State([])
    overview_view_mode = gr.State("overview")  # "overview" or "transitions"
    chapters_overview_original = gr.State("")  # Store original overview when viewing transitions

    # ---- helper: bump epoch (pt. sincronizare Create → Editor) ----
    def _bump_editor_epoch(epoch):
        return (epoch or 0) + 1


    # ---- Project Section ----
    with gr.Accordion("📂 Project", open=False):
        with gr.Row(equal_height=True):
            with gr.Column(scale=3):
                project_name = gr.Textbox(
                    label="Project Name",
                    placeholder="Enter project name...",
                    interactive=True,
                    lines=1,
                    max_lines=1,
                )
                project_dropdown = gr.Dropdown(
                    label="Saved Projects",
                    choices=[],
                    value=None,
                    interactive=True,
                )
            with gr.Column(scale=1, elem_classes=["project-buttons"], min_width=120):
                new_project_btn = gr.Button("🆕 New", size="sm")
                save_project_btn = gr.Button("💾 Save", size="sm")
                load_project_btn = gr.Button("📂 Load", size="sm")
                delete_project_btn = gr.Button("❌ Delete", size="sm")

    # ---- Inputs (plot + genre + params) ----
    with gr.Row():
        with gr.Column(scale=3):
            with gr.Column(elem_classes=["plot-wrapper"]):
                with gr.Row(elem_classes=["plot-header"]):
                    gr.Markdown("Plot Description", elem_id="plot-title")
                    with gr.Row(elem_classes=["plot-buttons"]):
                        show_original_btn = gr.Button("O", size="sm")
                        show_chat_btn = gr.Button("C", size="sm")
                        show_refined_btn = gr.Button("R", size="sm")
                        refine_btn = gr.Button("🪄", size="sm")
                plot_input_textbox = gr.Textbox(
                    label="Original",
                    lines=3,
                    elem_classes=["plot-textbox"],
                    placeholder="Ex: A young girl discovers a portal to another world...",
                    interactive=True,
                    visible=True,
                )
                with gr.Column(visible=False, elem_classes=["plot-refined-wrapper"]) as plot_refined_column:
                    gr.Markdown("Refined", elem_classes=["plot-refined-label"])
                    plot_input_markdown = gr.Markdown(
                        value="_This refined version will be used for generation (if present)._",
                        elem_id="plot-refined-markdown",
                        elem_classes=["plot-refined-content"],
                        min_height=80,
                        max_height=300
                    )
                with gr.Column(visible=False, elem_classes=["chat-wrapper"]) as chat_wrapper:
                    chatbot = gr.Chatbot(label="Plot King", height=300, type="messages", elem_id="create-chatbot", elem_classes=["small-text-chatbot"], avatar_images=("images/user_avatar.png", "images/plotking_avatar.png"))
                    with gr.Row(elem_classes=["chat-input-row"]):
                        chat_msg = gr.Textbox(scale=20, show_label=False, placeholder="Discuss with Plot King...", container=False, lines=1, max_lines=10, elem_id="chat-input-create")
                        send_btn = gr.Button("Send", scale=1, min_width=80)
                        gr.Column(scale=0, min_width=10, elem_classes=["spacer-right"]) # Spacer
            genre_input = gr.Textbox(label="Genre", placeholder="Ex: fantasy, science fiction", lines=2)

        with gr.Column(scale=1, elem_classes=["tight-group"]):
            chapters_input = gr.Number(label="Number of Chapters", value=5, precision=0)
            anpc_input = gr.Number(
                label="Average Number of Pages per Chapter",
                value=5,
                precision=0,
                interactive=True,
            )
            run_mode = gr.Dropdown(
                label="Run Mode",
                choices=list(RUN_MODE_CHOICES.values()),
                value=RUN_MODE_CHOICES["FULL"],
                interactive=True,
            )

    # ---- Top controls ----
    with gr.Row():
        generate_btn = gr.Button("🚀 Generate Book")
        stop_btn = gr.Button("🛑 Stop", variant="stop", visible=False)
        resume_btn = gr.Button("▶️ Resume", variant="primary", visible=False)

    # ---- Expanded Plot / Overview ----
    with gr.Row(equal_height=True):
        with gr.Column(elem_classes=["plot-wrapper"]):
            with gr.Row(elem_classes=["plot-header"]):
                gr.Markdown("📝 Expanded Plot")
                with gr.Row(elem_classes=["plot-buttons", "plot-buttons-compact"]):
                    regenerate_expanded_btn = gr.Button("🔄", size="sm", visible=False)
            expanded_output = gr.Markdown(elem_id="expanded-output", height=360)

        with gr.Column(elem_classes=["plot-wrapper"]):
            with gr.Row(elem_classes=["plot-header"]):
                gr.Markdown("📘 Chapters Overview")
                with gr.Row(elem_classes=["plot-buttons", "plot-buttons-compact"]):
                    toggle_transitions_btn = gr.Button("🔗", size="sm", visible=False, elem_id="toggle-transitions-btn")
                    regenerate_overview_btn = gr.Button("🔄", size="sm", visible=False)
            chapters_output = gr.Markdown(elem_id="chapters-output", height=360)

    # ---- Current chapter viewer ----
    with gr.Row():
        with gr.Column(scale=1):
            chapter_selector = gr.Dropdown(label="📖 Select Chapter", choices=[], value=None, interactive=True)
            chapter_counter = gr.Markdown("_No chapters yet_")
        with gr.Column(scale=3, elem_classes=["plot-wrapper"]):
            with gr.Row(elem_classes=["plot-header"]):
                gr.Markdown("📚 Current Chapter")
                with gr.Row(elem_classes=["plot-buttons", "plot-buttons-compact"]):
                    regenerate_chapter_btn = gr.Button("🔄", size="sm", visible=False)
            current_chapter_output = gr.Markdown(elem_id="current-chapter-output", height=360)

    # ---- Logs / Validation ----
    status_output = gr.Textbox(label="🧠 Process Log", lines=15, interactive=False)
    validation_feedback = gr.Textbox(label="🧩 Validation Feedback", lines=8)

    # ========= Generator WRAPPERS =========
    def _resume_pipeline():
        yield from resume_pipeline(generate_book_outline_stream)

    def _refresh_expanded():
        yield from refresh_expanded(generate_book_outline_stream)

    def _refresh_overview():
        yield from refresh_overview(generate_book_outline_stream)

    def _refresh_chapter(selected_name):
        yield from refresh_chapter(generate_book_outline_stream, selected_name)

    # ---- Chat Handlers are now in create_handlers.py ----

    # ---- Wiring ----

    # Launch pipeline
    generate_btn.click(
        fn=choose_plot_for_pipeline,
        inputs=[plot_state, refined_plot_state],
        outputs=[plot_state],
    ).then(
        fn=pre_run_reset_and_controls,
        inputs=[],
        outputs=[
            stop_btn,
            resume_btn,
            generate_btn,
            regenerate_expanded_btn,
            regenerate_overview_btn,
            regenerate_chapter_btn,
        ],
    ).then(
        fn=generate_dispatcher,
        inputs=[run_mode, plot_state, chapters_input, genre_input, anpc_input, run_mode],
        outputs=[
            expanded_output,
            chapters_output,
            chapters_state,
            current_chapter_output,
            chapter_selector,
            chapter_counter,
            status_output,
            validation_feedback,
            toggle_transitions_btn,
        ],
    ).then(
        fn=post_pipeline_controls,
        inputs=[],
        outputs=[
            stop_btn,
            resume_btn,
            generate_btn,
            regenerate_expanded_btn,
            regenerate_overview_btn,
            regenerate_chapter_btn,
        ],
    ).then(
        fn=_bump_editor_epoch,
        inputs=[editor_sections_epoch],
        outputs=[editor_sections_epoch],
    )

    # ---- Check Start Empty Button State ----
    def _update_btn_label(mode_val):
        # We need to check against the display value or key. Gradio returns the value.
        # RUN_MODE_CHOICES values are: "Full Pipeline", "Up to Chapters Overview", "Start Empty"
        if mode_val == "Start Empty":
             return gr.update(value="✨ Start Empty", interactive=True)
        return gr.update(value="🚀 Generate Book", interactive=True)

    
    # Run Mode Change -> Update Button Label
    run_mode.change(
        fn=_update_btn_label,
        inputs=[run_mode],
        outputs=[generate_btn]
    )

    # Stop
    stop_btn.click(
        fn=stop_pipeline,
        inputs=[status_output],
        outputs=[status_output, stop_btn, resume_btn],
    )

    # Resume
    resume_btn.click(
        fn=show_controls_on_resume_run,
        inputs=[],
        outputs=[
            stop_btn,
            resume_btn,
            generate_btn,
            regenerate_expanded_btn,
            regenerate_overview_btn,
            regenerate_chapter_btn,
        ],
    ).then(
        fn=_resume_pipeline,
        inputs=[],
        outputs=[
            expanded_output,
            chapters_output,
            chapters_state,
            current_chapter_output,
            chapter_selector,
            chapter_counter,
            status_output,
            validation_feedback,
            toggle_transitions_btn,
        ],
        queue=True,
    ).then(
        fn=post_pipeline_controls,
        inputs=[],
        outputs=[
            stop_btn,
            resume_btn,
            generate_btn,
            regenerate_expanded_btn,
            regenerate_overview_btn,
            regenerate_chapter_btn,
        ],
    ).then(
        fn=_bump_editor_epoch,
        inputs=[editor_sections_epoch],
        outputs=[editor_sections_epoch],
    )

    # Dropdown chapter viewer
    chapter_selector.change(
        fn=display_selected_chapter,
        inputs=[chapter_selector, chapters_state],
        outputs=[current_chapter_output],
    )

    # Regenerate: Expanded
    regenerate_expanded_btn.click(
        fn=show_stop_only,
        inputs=[],
        outputs=[
            stop_btn,
            resume_btn,
            generate_btn,
            regenerate_expanded_btn,
            regenerate_overview_btn,
            regenerate_chapter_btn,
        ],
    ).then(
        fn=pre_refresh_clear_transitions,
        inputs=[],
        outputs=[toggle_transitions_btn, overview_view_mode],
    ).then(
        fn=_refresh_expanded,
        inputs=[],
        outputs=[
            expanded_output,
            chapters_output,
            chapters_state,
            current_chapter_output,
            chapter_selector,
            chapter_counter,
            status_output,
            validation_feedback,
            toggle_transitions_btn,
        ],
    ).then(
        fn=post_pipeline_controls,
        inputs=[],
        outputs=[
            stop_btn,
            resume_btn,
            generate_btn,
            regenerate_expanded_btn,
            regenerate_overview_btn,
            regenerate_chapter_btn,
        ],
    ).then(
        fn=_bump_editor_epoch,
        inputs=[editor_sections_epoch],
        outputs=[editor_sections_epoch],
    )

    # Regenerate: Overview
    regenerate_overview_btn.click(
        fn=show_stop_only,
        inputs=[],
        outputs=[
            stop_btn,
            resume_btn,
            generate_btn,
            regenerate_expanded_btn,
            regenerate_overview_btn,
            regenerate_chapter_btn,
        ],
    ).then(
        fn=pre_refresh_clear_transitions,
        inputs=[],
        outputs=[toggle_transitions_btn, overview_view_mode],
    ).then(
        fn=_refresh_overview,
        inputs=[],
        outputs=[
            expanded_output,
            chapters_output,
            chapters_state,
            current_chapter_output,
            chapter_selector,
            chapter_counter,
            status_output,
            validation_feedback,
            toggle_transitions_btn,
        ],
    ).then(
        fn=post_pipeline_controls,
        inputs=[],
        outputs=[
            stop_btn,
            resume_btn,
            generate_btn,
            regenerate_expanded_btn,
            regenerate_overview_btn,
            regenerate_chapter_btn,
        ],
    ).then(
        fn=_bump_editor_epoch,
        inputs=[editor_sections_epoch],
        outputs=[editor_sections_epoch],
    )

    # Regenerate: Chapter
    regenerate_chapter_btn.click(
        fn=show_stop_only,
        inputs=[],
        outputs=[
            stop_btn,
            resume_btn,
            generate_btn,
            regenerate_expanded_btn,
            regenerate_overview_btn,
            regenerate_chapter_btn,
        ],
    ).then(
        fn=_refresh_chapter,
        inputs=[chapter_selector],
        outputs=[
            expanded_output,
            chapters_output,
            chapters_state,
            current_chapter_output,
            chapter_selector,
            chapter_counter,
            status_output,
            validation_feedback,
            toggle_transitions_btn,
        ],
    ).then(
        fn=post_pipeline_controls,
        inputs=[],
        outputs=[
            stop_btn,
            resume_btn,
            generate_btn,
            regenerate_expanded_btn,
            regenerate_overview_btn,
            regenerate_chapter_btn,
        ],
    ).then(
        fn=_bump_editor_epoch,
        inputs=[editor_sections_epoch],
        outputs=[editor_sections_epoch],
    )

    # Toggle Transitions View
    toggle_transitions_btn.click(
        fn=toggle_transitions_view,
        inputs=[overview_view_mode, chapters_overview_original, chapters_output],
        outputs=[chapters_output, overview_view_mode, chapters_overview_original, toggle_transitions_btn],
    )

    # Plot toggles
    show_original_btn.click(
        fn=show_original_wrapper, 
        inputs=[plot_state, refined_plot_state], 
        outputs=[plot_input_textbox, plot_refined_column, plot_input_markdown, current_mode, refine_btn, chat_wrapper]
    )
    show_refined_btn.click(
        fn=show_refined_wrapper, 
        inputs=[plot_state, refined_plot_state], 
        outputs=[plot_input_textbox, plot_refined_column, plot_input_markdown, current_mode, refine_btn, chat_wrapper]
    )
    show_chat_btn.click(
        fn=show_chat,
        inputs=[chat_history, plot_state, genre_input, status_output],
        outputs=[plot_input_textbox, plot_refined_column, plot_input_markdown, current_mode, refine_btn, chat_wrapper, chatbot, chat_history, status_output]
    )

    # Chat interactions
    # Chat interactions: 
    # 1. User submits -> update UI immediately, disable controls
    # 2. Bot replies -> call LLM, update UI, enable controls
    
    def _chat_submit_chain(start_fn, trigger):
        trigger(
            fn=user_submit_chat_message,
            inputs=[chat_msg, chat_history],
            outputs=[chat_msg, chatbot, chat_history, send_btn, chat_msg]
        ).then(
            fn=bot_reply_chat_message,
            inputs=[chat_history, plot_state, genre_input, status_output],
            outputs=[chatbot, chat_history, status_output, send_btn, chat_msg]
        )

    _chat_submit_chain(user_submit_chat_message, chat_msg.submit)
    _chat_submit_chain(user_submit_chat_message, send_btn.click)

    # Chatbot clear event
    chatbot.clear(
        fn=reset_chat_handler,
        inputs=[plot_state, genre_input, status_output],
        outputs=[chatbot, chat_history, status_output]
    )
    
    # Refine / Clear
    refine_btn.click(
        fn=refine_or_clear_dispatcher,
        inputs=[plot_state, refined_plot_state, current_mode, genre_input, chat_history, status_output],
        outputs=[plot_input_textbox, plot_refined_column, plot_input_markdown, refined_plot_state, current_mode, refine_btn, chat_wrapper, status_output, chat_msg, send_btn]
    )

    # Textbox sync
    plot_input_textbox.change(
        fn=sync_textbox, inputs=[plot_input_textbox, current_mode], outputs=[plot_state, refined_plot_state]
    )

    # === Project management wiring ===
    save_project_btn.click(
        fn=save_project,
        inputs=[
            project_name,
            genre_input,
            chapters_input,
            anpc_input,
            plot_state,
            refined_plot_state,
            status_output,
        ],
        outputs=[status_output, project_dropdown, current_project_label, header_save_btn],
    )
    
    # Header save button wiring
    header_save_btn.click(
        fn=save_project,
        inputs=[
            project_name,
            genre_input,
            chapters_input,
            anpc_input,
            plot_state,
            refined_plot_state,
            status_output,
        ],
        outputs=[status_output, project_dropdown, current_project_label, header_save_btn],
    )

    load_project_btn.click(
        fn=load_project,
        inputs=[project_dropdown, status_output],
        outputs=[
            plot_input_textbox,
            plot_refined_column,
            plot_input_markdown,
            genre_input,
            chapters_input,
            anpc_input,
            expanded_output,
            chapters_output,
            chapters_state,
            project_name,
            chapter_selector,
            current_chapter_output,
            chapter_counter,
            plot_state,
            refined_plot_state,
            current_mode,
            refine_btn,
            status_output,
            stop_btn,
            resume_btn,
            generate_btn,
            regenerate_expanded_btn,
            regenerate_overview_btn,
            regenerate_chapter_btn,
            current_project_label,
            header_save_btn,
        ],
    ).then(
        fn=_bump_editor_epoch,
        inputs=[editor_sections_epoch],
        outputs=[editor_sections_epoch],
    )

    delete_project_btn.click(
        fn=delete_project,
        inputs=[project_dropdown, status_output],
        outputs=[status_output, project_dropdown, current_project_label, header_save_btn],
    ).then(
        fn=_bump_editor_epoch,
        inputs=[editor_sections_epoch],
        outputs=[editor_sections_epoch],
    )

    new_project_btn.click(
        fn=new_project,
        inputs=[status_output],
        outputs=[
            plot_input_textbox,
            plot_refined_column,
            plot_input_markdown,
            genre_input,
            chapters_input,
            anpc_input,
            expanded_output,
            chapters_output,
            chapters_state,
            project_name,
            chapter_selector,
            current_chapter_output,
            chapter_counter,
            plot_state,
            refined_plot_state,
            refine_btn,
            status_output,
            regenerate_expanded_btn,
            regenerate_overview_btn,
            regenerate_chapter_btn,
            stop_btn,
            resume_btn,
            generate_btn,
            current_project_label,
            header_save_btn,
        ],
    ).then(
        fn=_bump_editor_epoch,
        inputs=[editor_sections_epoch],
        outputs=[editor_sections_epoch],
    )

    # ---- Sincronizare Editor -> Create: refresh Create tab când Editor modifică checkpoint ----
    create_sections_epoch.change(
        fn=refresh_create_from_checkpoint,
        inputs=[create_sections_epoch, chapters_state, chapter_selector],
        outputs=[
            expanded_output,
            chapters_output,
            chapters_state,
            current_chapter_output,
            chapter_selector,
            chapter_counter,
        ],
    )

    return project_dropdown
