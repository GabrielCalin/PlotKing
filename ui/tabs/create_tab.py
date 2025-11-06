# -*- coding: utf-8 -*-
# ui/tabs/create_tab.py — conținutul integral al interfeței inițiale, ca tabul "Create"

import gradio as gr
from ui import load_css
from ui.ui_state import display_selected_chapter
import ui.handlers as H
from pipeline.constants import RUN_MODE_CHOICES


def render_create_tab(pipeline_fn, refine_fn, current_project_label):
    header_project = gr.State("")

    # ---- States ----
    plot_state = gr.State("")
    refined_plot_state = gr.State("")
    current_mode = gr.State("original")
    chapters_state = gr.State([])

    # ---- Project Section (nou, collapsed by default) ----
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
    with gr.Row(equal_height=True):
        with gr.Column(scale=3):
            with gr.Column(elem_classes=["plot-wrapper"]):
                with gr.Row(elem_classes=["plot-header"]):
                    gr.Markdown("Plot Description", elem_id="plot-title")
                    with gr.Row(elem_classes=["plot-buttons"]):
                        show_original_btn = gr.Button("O", size="sm")
                        show_refined_btn = gr.Button("R", size="sm")
                        refine_btn = gr.Button("🪄", size="sm")
                plot_input = gr.Textbox(
                    label="Original",
                    lines=3,
                    elem_classes=["plot-textbox"],
                    placeholder="Ex: A young girl discovers a portal to another world...",
                    interactive=True,
                )
            genre_input = gr.Textbox(label="Genre", placeholder="Ex: fantasy, science fiction", lines=2)

        with gr.Column(scale=1):
            with gr.Group(elem_classes=["tight-group"]):
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
                with gr.Row(elem_classes=["plot-buttons"]):
                    regenerate_expanded_btn = gr.Button("🔄", size="sm", visible=False)
            expanded_output = gr.Markdown(elem_id="expanded-output", height=360)

        with gr.Column(elem_classes=["plot-wrapper"]):
            with gr.Row(elem_classes=["plot-header"]):
                gr.Markdown("📘 Chapters Overview")
                with gr.Row(elem_classes=["plot-buttons"]):
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
                with gr.Row(elem_classes=["plot-buttons"]):
                    regenerate_chapter_btn = gr.Button("🔄", size="sm", visible=False)
            current_chapter_output = gr.Markdown(elem_id="current-chapter-output", height=360)

    # ---- Logs / Validation ----
    status_output = gr.Textbox(label="🧠 Process Log", lines=15)
    validation_feedback = gr.Textbox(label="🧩 Validation Feedback", lines=8)

    # ========= Generator WRAPPERS (necesare pt. Gradio) =========
    def _resume_pipeline():
        # generator wrapper peste H.resume_pipeline
        yield from H.resume_pipeline(pipeline_fn)

    def _refresh_expanded():
        yield from H.refresh_expanded(pipeline_fn)

    def _refresh_overview():
        yield from H.refresh_overview(pipeline_fn)

    def _refresh_chapter(selected_name):
        yield from H.refresh_chapter(pipeline_fn, selected_name)

    # ---- Wiring ----

    # Launch pipeline
    generate_btn.click(
        fn=H.choose_plot_for_pipeline,
        inputs=[plot_state, refined_plot_state],
        outputs=[plot_state],
    ).then(
        fn=H.pre_run_reset_and_controls,
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
        fn=pipeline_fn,
        inputs=[plot_state, chapters_input, genre_input, anpc_input, run_mode],
        outputs=[
            expanded_output,
            chapters_output,
            chapters_state,
            current_chapter_output,
            chapter_selector,
            chapter_counter,
            status_output,
            validation_feedback,
        ],
    ).then(
        fn=H.post_pipeline_controls,
        inputs=[],
        outputs=[
            stop_btn,
            resume_btn,
            generate_btn,
            regenerate_expanded_btn,
            regenerate_overview_btn,
            regenerate_chapter_btn,
        ],
    )

    # Stop
    stop_btn.click(
        fn=H.stop_pipeline,
        inputs=[status_output],
        outputs=[status_output, stop_btn, resume_btn],
    )

    # Resume (folosește wrapperul generator)
    resume_btn.click(
        fn=H.show_controls_on_resume_run,
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
        ],
        queue=True,
    ).then(
        fn=H.post_pipeline_controls,
        inputs=[],
        outputs=[
            stop_btn,
            resume_btn,
            generate_btn,
            regenerate_expanded_btn,
            regenerate_overview_btn,
            regenerate_chapter_btn,
        ],
    )

    # Dropdown chapter viewer
    chapter_selector.change(
        fn=display_selected_chapter,
        inputs=[chapter_selector, chapters_state],
        outputs=[current_chapter_output],
    )

    # Regenerate: Expanded
    regenerate_expanded_btn.click(
        fn=H.show_stop_only,
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
        ],
    ).then(
        fn=H.post_pipeline_controls,
        inputs=[],
        outputs=[
            stop_btn,
            resume_btn,
            generate_btn,
            regenerate_expanded_btn,
            regenerate_overview_btn,
            regenerate_chapter_btn,
        ],
    )

    # Regenerate: Overview
    regenerate_overview_btn.click(
        fn=H.show_stop_only,
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
        ],
    ).then(
        fn=H.post_pipeline_controls,
        inputs=[],
        outputs=[
            stop_btn,
            resume_btn,
            generate_btn,
            regenerate_expanded_btn,
            regenerate_overview_btn,
            regenerate_chapter_btn,
        ],
    )

    # Regenerate: Chapter
    regenerate_chapter_btn.click(
        fn=H.show_stop_only,
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
        ],
    ).then(
        fn=H.post_pipeline_controls,
        inputs=[],
        outputs=[
            stop_btn,
            resume_btn,
            generate_btn,
            regenerate_expanded_btn,
            regenerate_overview_btn,
            regenerate_chapter_btn,
        ],
    )

    # Plot toggles
    show_original_btn.click(
        fn=H.show_original, inputs=[plot_state, refined_plot_state], outputs=[plot_input, current_mode, refine_btn]
    )
    show_refined_btn.click(
        fn=H.show_refined, inputs=[plot_state, refined_plot_state], outputs=[plot_input, current_mode, refine_btn]
    )

    # Refine / Clear
    refine_btn.click(
        fn=lambda plot, refined, mode, genre: H.refine_or_clear(plot, refined, mode, genre, refine_fn),
        inputs=[plot_state, refined_plot_state, current_mode, genre_input],
        outputs=[plot_input, refined_plot_state, current_mode, refine_btn],
    )

    # Textbox sync (original vs refined)
    plot_input.change(
        fn=H.sync_textbox, inputs=[plot_input, current_mode], outputs=[plot_state, refined_plot_state]
    )

    # === Project management wiring ===
    save_project_btn.click(
        fn=H.save_project,
        inputs=[
            project_name,
            plot_input,
            genre_input,
            chapters_input,
            anpc_input,
            expanded_output,
            chapters_output,
            chapters_state,
            plot_state,            # <— ORIGINAL (State)
            refined_plot_state,    # <— REFINED (State)
            status_output,         # <— pentru append în log
        ],
        outputs=[status_output, project_dropdown],
    )

    load_project_btn.click(
        fn=H.load_project,
        inputs=[project_dropdown, status_output],
        outputs=[
            plot_input,
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
        ],
    ).then(
        fn=lambda name: f"<div id='bk-project'>{name}</div>" if name else "<div id='bk-project'>(No project loaded)</div>",
        inputs=[project_name],
        outputs=[current_project_label],
    )

    delete_project_btn.click(
        fn=H.delete_project,
        inputs=[project_dropdown, status_output],
        outputs=[status_output, project_dropdown],
    )

    new_project_btn.click(
        fn=H.new_project,
        inputs=[status_output],
        outputs=[
            plot_input,
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
        ],
    )

    return project_dropdown
