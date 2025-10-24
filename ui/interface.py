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


def create_interface(pipeline_fn, refine_fn=None):
    def toggle_plot_label(is_refined):
        return gr.update(label="Refined" if is_refined else "Original")

    with gr.Blocks(
        title="BookKing - AI Story Builder",
        css="""
        .tight-group > *:not(:last-child) { margin-bottom: 4px !important; }
        .plot-wrapper { border: 1px solid var(--block-border-color); border-radius: var(--block-radius); overflow: hidden; }
        .plot-header { display: flex; justify-content: space-between; align-items: center; background-color: var(--block-label-background-fill);
                       padding: 4px 8px; font-weight: 600; font-size: 0.9rem; border-bottom: 1px solid var(--block-border-color); }
        .plot-buttons { display: flex; gap: 3px; }
        .plot-buttons button { background: none !important; border: none !important; box-shadow: none !important; padding: 0 4px !important;
                               min-width: auto !important; height: auto !important; font-size: 0.9rem !important; opacity: 0.65; transition: opacity 0.15s; }
        .plot-buttons button:hover { opacity: 1; }
        .plot-textbox textarea { border: none !important; border-radius: 0 !important; box-shadow: none !important; resize: vertical !important; }
        """
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
                        placeholder="Ex: A young girl discovers a portal to another world..."
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

        # --- PIPELINE main button ---
        generate_btn.click(
            fn=pipeline_fn,
            inputs=[plot_input, chapters_input, genre_input, anpc_input],
            outputs=[
                expanded_output, chapters_output, chapters_state, current_chapter_output,
                chapter_selector, chapter_counter, status_output, validation_feedback,
            ]
        )

        # --- Display selected chapter ---
        chapter_selector.change(
            fn=display_selected_chapter,
            inputs=[chapter_selector, chapters_state],
            outputs=[current_chapter_output]
        )

        # --- BUTTONS: Original / Refined ---
        def show_original(plot, refined_plot):
            return gr.update(value=plot, label="Original"), "original"

        def show_refined(plot, refined_plot):
            return gr.update(value=refined_plot, label="Refined"), "refined"

        show_original_btn.click(fn=show_original, inputs=[plot_state, refined_plot_state],
                                outputs=[plot_input, current_mode])
        show_refined_btn.click(fn=show_refined, inputs=[plot_state, refined_plot_state],
                               outputs=[plot_input, current_mode])

        # --- REFINE button (generate refined plot) ---
        def refine_action(plot, refined_plot):
            if refine_fn:
                new_refined = refine_fn(plot)
            else:
                new_refined = plot + "\n\n[Refined plot generated here.]"
            return gr.update(value=new_refined, label="Refined"), new_refined, "refined"

        refine_btn.click(fn=refine_action, inputs=[plot_state, refined_plot_state],
                         outputs=[plot_input, refined_plot_state, current_mode])

        # --- When user edits the textbox ---
        def sync_textbox(text, mode):
            if mode == "refined":
                return gr.update(), text
            else:
                return text, gr.update()

        plot_input.change(fn=sync_textbox, inputs=[plot_input, current_mode],
                          outputs=[plot_state, refined_plot_state])

    return demo
