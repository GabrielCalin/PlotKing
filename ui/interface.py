# -*- coding: utf-8 -*-
import gradio as gr
from ui import load_css
from pipeline.constants import RUN_MODE_CHOICES
from pipeline.state_manager import request_stop, get_checkpoint, clear_stop, clear_checkpoint
from datetime import datetime

def ts_prefix(message: str) -> str:
    return f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] {message}"

def display_selected_chapter(chapter_name, chapters):
    if not chapters or not chapter_name:
        return ""
    try:
        idx = int(chapter_name.split(" ")[1]) - 1
    except Exception:
        return ""
    if 0 <= idx < len(chapters):
        return chapters[idx]
    return ""

def create_interface(pipeline_fn, refine_fn):
    def toggle_plot_label(is_refined):
        return gr.update(label="Refined" if is_refined else "Original")

    with gr.Blocks(title="BookKing - AI Story Builder", css=load_css()) as demo:
        gr.Markdown("""
        # 📖 BookKing - AI Story Builder  
        _Generate, validate, and refine your novels interactively._
        """)

        plot_state = gr.State("")
        refined_plot_state = gr.State("")
        current_mode = gr.State("original")
        chapters_state = gr.State([])

        with gr.Row(equal_height=True):
            with gr.Column(scale=3):
                with gr.Column(elem_classes=["plot-wrapper"]):
                    with gr.Row(elem_classes=["plot-header"]):
                        gr.Markdown("Plot Description", elem_id="plot-title")
                        with gr.Row(elem_classes=["plot-buttons"]):
                            show_original_btn = gr.Button("O", size="sm")
                            show_refined_btn = gr.Button("R", size="sm")
                            refine_btn = gr.Button("🪄", size="sm")
                    plot_input = gr.Textbox(label="Original", lines=3, elem_classes=["plot-textbox"],
                                            placeholder="Ex: A young girl discovers a portal to another world...",
                                            interactive=True)
                genre_input = gr.Textbox(label="Genre", placeholder="Ex: fantasy, science fiction", lines=2)
            with gr.Column(scale=1):
                with gr.Group(elem_classes=["tight-group"]):
                    chapters_input = gr.Number(label="Number of Chapters", value=5, precision=0)
                    anpc_input = gr.Number(label="Average Number of Pages per Chapter", value=5, precision=0, interactive=True)
                    run_mode = gr.Dropdown(label="Run Mode", choices=list(RUN_MODE_CHOICES.values()),
                                           value=RUN_MODE_CHOICES["FULL"], interactive=True)

        with gr.Row():
            generate_btn = gr.Button("🚀 Generate Book")
            stop_btn = gr.Button("🛑 Stop", variant="stop", visible=False)
            resume_btn = gr.Button("▶️ Resume", variant="primary", visible=False)

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

        status_output = gr.Textbox(label="🧠 Process Log", lines=15)
        validation_feedback = gr.Textbox(label="🧩 Validation Feedback", lines=8)

        def choose_plot_for_pipeline(plot, refined):
            return refined if refined.strip() else plot

        def pre_run_reset_and_controls():
            clear_stop()
            clear_checkpoint()
            return (
                gr.update(visible=True, interactive=True, value="🛑 Stop"),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
            )

        def post_pipeline_controls():
            checkpoint = get_checkpoint()
            if not checkpoint:
                return (
                    gr.update(interactive=True, visible=False),
                    gr.update(visible=False),
                    gr.update(visible=True),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                )

            expanded_visible = bool(checkpoint.get("expanded_plot"))
            overview_visible = bool(checkpoint.get("chapters_overview"))
            chapters_count = len(checkpoint.get("chapters_full", []))

            try:
                total_chapters = int(checkpoint.get("num_chapters") or chapters_count)
            except Exception:
                total_chapters = chapters_count

            has_resume_markers = bool(checkpoint.get("pending_validation_index")) or bool(checkpoint.get("next_chapter_index"))

            is_full_complete = expanded_visible and overview_visible and (chapters_count >= max(1, total_chapters)) and not has_resume_markers
            stopped_at_overview = expanded_visible and overview_visible and (chapters_count == 0) and not has_resume_markers

            chapters_visible = chapters_count > 0

            if is_full_complete:
                return (
                    gr.update(interactive=True, visible=False),
                    gr.update(visible=False),
                    gr.update(visible=True),
                    gr.update(visible=expanded_visible),
                    gr.update(visible=overview_visible),
                    gr.update(visible=chapters_visible),
                )
            elif stopped_at_overview:
                return (
                    gr.update(interactive=True, visible=False),
                    gr.update(visible=True),
                    gr.update(visible=True),
                    gr.update(visible=expanded_visible),
                    gr.update(visible=overview_visible),
                    gr.update(visible=False),
                )
            else:
                return (
                    gr.update(interactive=True, visible=False),
                    gr.update(visible=True),
                    gr.update(visible=True),
                    gr.update(visible=expanded_visible),
                    gr.update(visible=overview_visible),
                    gr.update(visible=chapters_visible),
                )

        def show_stop_only():
            return (
                gr.update(visible=True, interactive=True, value="🛑 Stop"),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
            )

        generate_btn.click(
            fn=choose_plot_for_pipeline,
            inputs=[plot_state, refined_plot_state],
            outputs=[plot_state]
        ).then(
            fn=pre_run_reset_and_controls,
            inputs=[],
            outputs=[stop_btn, resume_btn, generate_btn,
                     regenerate_expanded_btn, regenerate_overview_btn, regenerate_chapter_btn]
        ).then(
            fn=pipeline_fn,
            inputs=[plot_state, chapters_input, genre_input, anpc_input, run_mode],
            outputs=[
                expanded_output, chapters_output, chapters_state,
                current_chapter_output, chapter_selector, chapter_counter,
                status_output, validation_feedback,
            ]
        ).then(
            fn=post_pipeline_controls,
            inputs=[],
            outputs=[stop_btn, resume_btn, generate_btn,
                     regenerate_expanded_btn, regenerate_overview_btn, regenerate_chapter_btn]
        )

        def stop_pipeline(cur_status):
            request_stop()
            new_status = (cur_status + "\n" + ts_prefix("🛑 Stop requested")).strip() if cur_status else ts_prefix("🛑 Stop requested")
            return new_status, gr.update(interactive=False, value="Stopping…"), gr.update(visible=False)

        stop_btn.click(
            fn=stop_pipeline,
            inputs=[status_output],
            outputs=[status_output, stop_btn, resume_btn]
        )

        def show_controls_on_resume_run():
            return (
                gr.update(visible=True, interactive=True, value="🛑 Stop"),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
            )

        def resume_pipeline():
            checkpoint = get_checkpoint()
            if not checkpoint:
                yield "", "", [], "", gr.update(choices=[]), "_No checkpoint_", "⚠️ No checkpoint found to resume from.", ""
                return
            plot = checkpoint.get("plot", "")
            num_chapters = checkpoint.get("num_chapters", 0)
            genre = checkpoint.get("genre", "")
            anpc = checkpoint.get("anpc", 0)
            rm = checkpoint.get("run_mode", RUN_MODE_CHOICES["FULL"])

            expanded_visible = bool(checkpoint.get("expanded_plot"))
            overview_visible = bool(checkpoint.get("chapters_overview"))
            chapters_count = len(checkpoint.get("chapters_full", []))
            has_resume_markers = bool(checkpoint.get("pending_validation_index")) or bool(checkpoint.get("next_chapter_index"))
            stopped_at_overview = expanded_visible and overview_visible and (chapters_count == 0) and not has_resume_markers and (rm == RUN_MODE_CHOICES.get("OVERVIEW"))

            resume_run_mode = RUN_MODE_CHOICES["FULL"] if stopped_at_overview else rm

            clear_stop()
            clear_checkpoint()
            yield from pipeline_fn(plot, num_chapters, genre, anpc, resume_run_mode, checkpoint=checkpoint)

        resume_btn.click(
            fn=show_controls_on_resume_run,
            inputs=[],
            outputs=[stop_btn, resume_btn, generate_btn,
                     regenerate_expanded_btn, regenerate_overview_btn, regenerate_chapter_btn]
        ).then(
            fn=resume_pipeline,
            inputs=[],
            outputs=[
                expanded_output, chapters_output, chapters_state,
                current_chapter_output, chapter_selector, chapter_counter,
                status_output, validation_feedback,
            ]
        ).then(
            fn=post_pipeline_controls,
            inputs=[],
            outputs=[stop_btn, resume_btn, generate_btn,
                     regenerate_expanded_btn, regenerate_overview_btn, regenerate_chapter_btn]
        )

        chapter_selector.change(
            fn=display_selected_chapter,
            inputs=[chapter_selector, chapters_state],
            outputs=[current_chapter_output]
        )

        def refresh_expanded():
            checkpoint = get_checkpoint()
            if not checkpoint:
                yield "", "", [], "", gr.update(), "_No checkpoint_", "⚠️ Cannot refresh without checkpoint.", ""
                return
            clear_stop()
            yield from pipeline_fn(
                checkpoint["plot"],
                checkpoint["num_chapters"],
                checkpoint["genre"],
                checkpoint["anpc"],
                checkpoint["run_mode"],
                checkpoint=checkpoint,
                refresh_from="expanded"
            )

        def refresh_overview():
            checkpoint = get_checkpoint()
            if not checkpoint:
                yield "", "", [], "", gr.update(), "_No checkpoint_", "⚠️ Cannot refresh without checkpoint.", ""
                return
            clear_stop()
            yield from pipeline_fn(
                checkpoint["plot"],
                checkpoint["num_chapters"],
                checkpoint["genre"],
                checkpoint["anpc"],
                checkpoint["run_mode"],
                checkpoint=checkpoint,
                refresh_from="overview"
            )

        def refresh_chapter(selected_name):
            checkpoint = get_checkpoint()
            if not checkpoint:
                yield "", "", [], "", gr.update(), "_No checkpoint_", "⚠️ Cannot refresh without checkpoint.", ""
                return
            if not selected_name:
                yield "", "", [], "", gr.update(), "_No chapter selected_", "⚠️ Please select a chapter.", ""
                return
            try:
                idx = int(selected_name.split(" ")[1])
            except Exception:
                idx = None
            clear_stop()
            if idx == 1:
                current_text_update = ""
                dropdown_update = gr.update(value=None)
            else:
                current_text_update = checkpoint.get("chapters_full", [])[0] if checkpoint.get("chapters_full") else ""
                dropdown_update = gr.update(value="Chapter 1")
            yield (
                gr.update(value=checkpoint.get("expanded_plot", "")),
                gr.update(value=checkpoint.get("chapters_overview", "")),
                checkpoint.get("chapters_full", []),
                current_text_update,
                dropdown_update,
                f"Refreshing from chapter {idx}...",
                ts_prefix(f"🔁 Refresh from chapter {idx} initiated."),
                checkpoint.get("validation_text", ""),
            )
            yield from pipeline_fn(
                checkpoint["plot"],
                checkpoint["num_chapters"],
                checkpoint["genre"],
                checkpoint["anpc"],
                checkpoint["run_mode"],
                checkpoint=checkpoint,
                refresh_from=idx
            )

        regenerate_expanded_btn.click(
            fn=show_stop_only,
            inputs=[],
            outputs=[stop_btn, resume_btn, generate_btn,
                     regenerate_expanded_btn, regenerate_overview_btn, regenerate_chapter_btn]
        ).then(
            fn=refresh_expanded,
            inputs=[],
            outputs=[
                expanded_output, chapters_output, chapters_state,
                current_chapter_output, chapter_selector, chapter_counter,
                status_output, validation_feedback
            ]
        ).then(
            fn=post_pipeline_controls,
            inputs=[],
            outputs=[stop_btn, resume_btn, generate_btn,
                     regenerate_expanded_btn, regenerate_overview_btn, regenerate_chapter_btn]
        )

        regenerate_overview_btn.click(
            fn=show_stop_only,
            inputs=[],
            outputs=[stop_btn, resume_btn, generate_btn,
                     regenerate_expanded_btn, regenerate_overview_btn, regenerate_chapter_btn]
        ).then(
            fn=refresh_overview,
            inputs=[],
            outputs=[
                expanded_output, chapters_output, chapters_state,
                current_chapter_output, chapter_selector, chapter_counter,
                status_output, validation_feedback
            ]
        ).then(
            fn=post_pipeline_controls,
            inputs=[],
            outputs=[stop_btn, resume_btn, generate_btn,
                     regenerate_expanded_btn, regenerate_overview_btn, regenerate_chapter_btn]
        )

        regenerate_chapter_btn.click(
            fn=show_stop_only,
            inputs=[],
            outputs=[stop_btn, resume_btn, generate_btn,
                     regenerate_expanded_btn, regenerate_overview_btn, regenerate_chapter_btn]
        ).then(
            fn=refresh_chapter,
            inputs=[chapter_selector],
            outputs=[
                expanded_output, chapters_output, chapters_state,
                current_chapter_output, chapter_selector, chapter_counter,
                status_output, validation_feedback
            ]
        ).then(
            fn=post_pipeline_controls,
            inputs=[],
            outputs=[stop_btn, resume_btn, generate_btn,
                     regenerate_expanded_btn, regenerate_overview_btn, regenerate_chapter_btn]
        )

        def show_original(plot, refined):
            return gr.update(value=plot, label="Original", interactive=True,
                             placeholder="Ex: A young girl discovers a portal to another world..."), \
                   "original", gr.update(value="🪄")

        show_original_btn.click(
            fn=show_original,
            inputs=[plot_state, refined_plot_state],
            outputs=[plot_input, current_mode, refine_btn]
        )

        def show_refined(plot, refined):
            return gr.update(value=refined, label="Refined", interactive=False,
                             placeholder="This refined version will be used for generation (if present)."), \
                   "refined", gr.update(value="🧹")

        show_refined_btn.click(
            fn=show_refined,
            inputs=[plot_state, refined_plot_state],
            outputs=[plot_input, current_mode, refine_btn]
        )

        def refine_or_clear(plot, refined, mode, genre):
            if mode == "refined":
                return gr.update(value=plot, label="Original", interactive=True), "", "original", gr.update(value="🪄")
            else:
                new_refined = refine_fn(plot, genre)
                return gr.update(value=new_refined, label="Refined", interactive=False,
                                 placeholder="This refined version will be used for generation (if present)."), \
                       new_refined, "refined", gr.update(value="🧹")

        refine_btn.click(
            fn=refine_or_clear,
            inputs=[plot_state, refined_plot_state, current_mode, genre_input],
            outputs=[plot_input, refined_plot_state, current_mode, refine_btn]
        )

        def sync_textbox(text, mode):
            if mode == "refined":
                return gr.update(), text
            else:
                return text, gr.update()

        plot_input.change(fn=sync_textbox, inputs=[plot_input, current_mode],
                          outputs=[plot_state, refined_plot_state])

    return demo
