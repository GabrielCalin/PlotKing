# -*- coding: utf-8 -*-
import gradio as gr
from ui import load_css


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

    with gr.Blocks(
        title="BookKing - AI Story Builder",
        css=load_css()
    ) as demo:
        gr.Markdown("""
        # 📖 BookKing - AI Story Builder  
        _Generate, validate, and refine your novels interactively._
        """)

        plot_state = gr.State("")
        refined_plot_state = gr.State("")
        current_mode = gr.State("original")

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
                        interactive=True
                    )

                genre_input = gr.Textbox(
                    label="Genre",
                    placeholder="Ex: fantasy, science fiction",
                    lines=2
                )

            with gr.Column(scale=1):
                with gr.Group(elem_classes=["tight-group"]):
                    chapters_input = gr.Number(label="Number of Chapters", value=5, precision=0)
                    anpc_input = gr.Number(label="Average Number of Pages per Chapter", value=5, precision=0, interactive=True)
                gr.Markdown("")

        generate_btn = gr.Button("🚀 Generate Book")

        with gr.Row():
            expanded_output = gr.Textbox(label="📝 Expanded Plot", lines=15)
            chapters_output = gr.Textbox(label="📘 Chapters Overview", lines=15)

        with gr.Row():
            with gr.Column(scale=1):
                chapter_selector = gr.Dropdown(label="📖 Select Chapter", choices=[], value=None, interactive=True)
                chapter_counter = gr.Markdown("_No chapters yet_")
            with gr.Column(scale=3):
                current_chapter_output = gr.Textbox(label="📚 Current Chapter", lines=20)

        status_output = gr.Textbox(label="🧠 Process Log", lines=15)
        validation_feedback = gr.Textbox(label="🧩 Validation Feedback", lines=8)

        chapters_state = gr.State([])

        # --- main generation button ---
        def choose_plot_for_pipeline(plot, refined):
            return refined if refined.strip() else plot

        generate_btn.click(
            fn=choose_plot_for_pipeline,
            inputs=[plot_state, refined_plot_state],
            outputs=[plot_state]
        ).then(
            fn=pipeline_fn,
            inputs=[plot_state, chapters_input, genre_input, anpc_input],
            outputs=[
                expanded_output, chapters_output, chapters_state,
                current_chapter_output, chapter_selector, chapter_counter,
                status_output, validation_feedback,
            ]
        )

        chapter_selector.change(
            fn=display_selected_chapter,
            inputs=[chapter_selector, chapters_state],
            outputs=[current_chapter_output]
        )

        # --- ORIGINAL view ---
        def show_original(plot, refined):
            return gr.update(
                value=plot,
                label="Original",
                interactive=True,
                placeholder="Ex: A young girl discovers a portal to another world..."
            ), "original", gr.update(value="🪄")

        show_original_btn.click(
            fn=show_original,
            inputs=[plot_state, refined_plot_state],
            outputs=[plot_input, current_mode, refine_btn]
        )

        # --- REFINED view ---
        def show_refined(plot, refined):
            return gr.update(
                value=refined,
                label="Refined",
                interactive=False,
                placeholder="This refined version will be used for generation (if present)."
            ), "refined", gr.update(value="🧹")

        show_refined_btn.click(
            fn=show_refined,
            inputs=[plot_state, refined_plot_state],
            outputs=[plot_input, current_mode, refine_btn]
        )

        def refine_or_clear(plot, refined, mode, genre):
            if mode == "refined":
                # clear refined plot
                return gr.update(value=plot, label="Original", interactive=True), "", "original", gr.update(value="🪄")
            else:
                new_refined = refine_fn(plot, genre)
                return gr.update(
                    value=new_refined,
                    label="Refined",
                    interactive=False,
                    placeholder="This refined version will be used for generation (if present)."
                ), new_refined, "refined", gr.update(value="🧹")

        refine_btn.click(
            fn=refine_or_clear,
            inputs=[plot_state, refined_plot_state, current_mode, genre_input],
            outputs=[plot_input, refined_plot_state, current_mode, refine_btn]
        )

        # --- sync user edits ---
        def sync_textbox(text, mode):
            if mode == "refined":
                return gr.update(), text
            else:
                return text, gr.update()

        plot_input.change(fn=sync_textbox, inputs=[plot_input, current_mode],
                          outputs=[plot_state, refined_plot_state])

    return demo
