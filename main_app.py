# -*- coding: utf-8 -*-
import gradio as gr
from step1_plot_expander import expand_plot
from step2_chapter_generator import generate_chapters
from step3_validator import validate_chapters
from step4_chapter_writer import generate_chapter

MAX_VALIDATION_ATTEMPTS = 3


def generate_book_outline_stream(plot, num_chapters):
    """Pipeline streaming: yields updates after each stage."""
    if not plot.strip():
        yield "Please enter a plot description.", "", "⚠️ No input provided."
        return

    status_log = []

    # STEP 1
    status_log.append("📝 Step 1: Expanding plot...")
    yield "", "", "\n".join(status_log)
    expanded_plot = expand_plot(plot)
    status_log.append("✅ Plot expanded.")
    yield expanded_plot, "", "\n".join(status_log)

    # STEP 2
    status_log.append("📘 Step 2: Generating chapters...")
    yield expanded_plot, "", "\n".join(status_log)
    chapters = generate_chapters(expanded_plot, num_chapters)
    status_log.append("✅ Chapters generated.")
    yield expanded_plot, chapters, "\n".join(status_log)

    # STEP 3 - feedback loop
    validation_round = 0
    while validation_round < MAX_VALIDATION_ATTEMPTS:
        validation_round += 1
        status_log.append(f"🔍 Step 3: Validating chapters (attempt {validation_round})...")
        yield expanded_plot, chapters, "\n".join(status_log)

        result, feedback = validate_chapters(expanded_plot, chapters, iteration=validation_round)

        if result == "OK":
            status_log.append("✅ Validation passed.")
            yield expanded_plot, chapters, "\n".join(status_log)
            break
        elif result == "NOT OK":
            status_log.append(f"⚠️ Validation found issues: {feedback[:200]}...")
            status_log.append("♻️ Regenerating chapters with feedback...")
            yield expanded_plot, chapters, "\n".join(status_log)
            chapters = generate_chapters(expanded_plot, num_chapters, feedback)
            status_log.append("🔄 New version of chapters generated.")
            yield expanded_plot, chapters, "\n".join(status_log)
        else:
            status_log.append(f"❌ Validation error: {feedback}")
            yield expanded_plot, chapters, "\n".join(status_log)
            break

    if validation_round >= MAX_VALIDATION_ATTEMPTS:
        status_log.append("⚠️ Max validation attempts reached. Returning latest chapters.")
        yield expanded_plot, chapters, "\n".join(status_log)


# ---------------- STEP 4 ---------------- #

def generate_next_chapter(expanded_plot, chapters_overview, chapters_state, current_index):
    """Step 4 streaming generator for long chapters."""
    if not expanded_plot or not chapters_overview:
        yield "Missing previous steps output.", chapters_state, "⚠️ Missing data."
        return

    logs = [f"🖋 Generating Chapter {current_index + 1}..."]
    yield "", chapters_state, "\n".join(logs)

    previous_texts = [c["text"] for c in chapters_state]
    new_text = generate_chapter(expanded_plot, chapters_overview, previous_texts, current_index)

    new_entry = {
        "title": f"Chapter {current_index + 1}",
        "text": new_text,
    }
    chapters_state.append(new_entry)
    logs.append(f"✅ Chapter {current_index + 1} generated successfully.")

    yield new_text, chapters_state, "\n".join(logs)


def update_chapter_display(selected_title, chapters_state):
    """When user selects a chapter in dropdown."""
    if not chapters_state:
        return "No chapters generated yet."
    for ch in chapters_state:
        if ch["title"] == selected_title:
            return ch["text"]
    return "Chapter not found."


# ------------------- UI ------------------- #

with gr.Blocks(title="BookKing - Full AI Book Builder") as demo:
    gr.Markdown("""
    # 📚 BookKing — AI Book Generator  
    _From plot → outline → validation → full chapter generation (live)._
    """)

    # Inputs for Step 1–3
    with gr.Row():
        plot_input = gr.Textbox(
            label="Short Plot Description",
            lines=3,
            placeholder="Ex: A young girl discovers a portal to another world..."
        )
        chapters_input = gr.Number(label="Number of Chapters", value=10, precision=0)

    generate_outline_btn = gr.Button("🚀 Generate Outline (Steps 1–3 Live)")

    with gr.Row():
        expanded_output = gr.Textbox(label="📝 Expanded Plot", lines=15)
        chapters_output = gr.Textbox(label="📘 Chapters Overview", lines=15)

    status_output = gr.Textbox(label="🧩 Process Log", lines=10)

    # --- Step 4: Chapter Generation ---
    gr.Markdown("## ✏️ Step 4 — Generate Full Chapters")

    chapters_state = gr.State([])

    with gr.Row():
        next_index = gr.Number(label="Generate Chapter #", value=1, precision=0)
        gen_chapter_btn = gr.Button("✏️ Generate This Chapter")

    with gr.Row():
        chapter_selector = gr.Dropdown(label="Select Chapter to View", choices=[], interactive=True)
        chapter_view = gr.Textbox(label="📖 Chapter Text", lines=25)

    # Connect outline generation
    generate_outline_btn.click(
        fn=generate_book_outline_stream,
        inputs=[plot_input, chapters_input],
        outputs=[expanded_output, chapters_output, status_output]
    )

    # Generate chapter (Step 4)
    gen_chapter_btn.click(
        fn=generate_next_chapter,
        inputs=[expanded_output, chapters_output, chapters_state, next_index],
        outputs=[chapter_view, chapters_state, status_output]
    ).then(
        fn=lambda chapters: [ch["title"] for ch in chapters],
        inputs=chapters_state,
        outputs=chapter_selector
    )

    # Update chapter display when selecting
    chapter_selector.change(
        fn=update_chapter_display,
        inputs=[chapter_selector, chapters_state],
        outputs=chapter_view
    )

demo.launch(server_name="0.0.0.0", server_port=7860)
