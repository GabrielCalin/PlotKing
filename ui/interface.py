# -*- coding: utf-8 -*-
import gradio as gr


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


def create_interface(pipeline_fn):
    with gr.Blocks(
        title="BookKing - AI Story Builder",
        css="""
        .tight-group > *:not(:last-child) {
            margin-bottom: 4px !important;
        }
        """
    ) as demo:
        gr.Markdown("""
        # 📖 BookKing - AI Story Builder  
        _Generate, validate, and refine your novels interactively._
        """)

        with gr.Row(equal_height=True):
            with gr.Column(scale=3):
                plot_input = gr.Textbox(
                    label="Plot Description",
                    lines=3,
                    placeholder="Ex: A young girl discovers a portal to another world..."
                )
                genre_input = gr.Textbox(
                    label="Genre",
                    placeholder="Ex: fantasy, science fiction",
                    lines=2
                )
            with gr.Column(scale=1):
                with gr.Group(elem_classes=["tight-group"]):
                    chapters_input = gr.Number(
                        label="Number of Chapters",
                        value=5,
                        precision=0
                    )
                    anpc_input = gr.Number(
                        label="Average Number of Pages per Chapter",
                        value=5,
                        precision=0,
                        interactive=True
                    )
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

        generate_btn.click(
            fn=pipeline_fn,
            inputs=[plot_input, chapters_input, genre_input, anpc_input],
            outputs=[
                expanded_output,
                chapters_output,
                chapters_state,
                current_chapter_output,
                chapter_selector,
                chapter_counter,
                status_output,
                validation_feedback,
            ]
        )

        chapter_selector.change(
            fn=display_selected_chapter,
            inputs=[chapter_selector, chapters_state],
            outputs=[current_chapter_output]
        )

    return demo
