# -*- coding: utf-8 -*-
import gradio as gr
from step1_plot_expander import expand_plot
from step2_chapter_generator import generate_chapters
from step3_validator import validate_chapters
from step4_chapter_writer import generate_chapter_text

MAX_VALIDATION_ATTEMPTS = 3

def generate_full_book_stream(plot, num_chapters):
    """Full pipeline with live streaming for all 4 steps."""
    if not plot.strip():
        yield "Please enter a plot description.", "", "", "⚠️ No input provided."
        return

    status_log = []
    expanded_plot, chapters, full_chapter_texts = "", "", {}

    # STEP 1 - Expand Plot
    status_log.append("📝 Step 1: Expanding plot...")
    yield "", "", "", "\n".join(status_log)
    expanded_plot = expand_plot(plot)
    status_log.append("✅ Plot expanded.")
    yield expanded_plot, "", "", "\n".join(status_log)

    # STEP 2 - Generate Chapters
    status_log.append("📘 Step 2: Generating chapter list...")
    yield expanded_plot, "", "", "\n".join(status_log)
    chapters = generate_chapters(expanded_plot, num_chapters)
    status_log.append("✅ Chapters overview generated.")
    yield expanded_plot, chapters, "", "\n".join(status_log)

    # STEP 3 - Validate Chapters
    validation_round = 0
    while validation_round < MAX_VALIDATION_ATTEMPTS:
        validation_round += 1
        status_log.append(f"🔍 Step 3: Validating chapters (attempt {validation_round})...")
        yield expanded_plot, chapters, "", "\n".join(status_log)

        result, feedback = validate_chapters(expanded_plot, chapters, iteration=validation_round)

        if result == "OK":
            status_log.append("✅ Validation passed.")
            yield expanded_plot, chapters, "", "\n".join(status_log)
            break
        elif result == "NOT OK":
            status_log.append(f"⚠️ Validation found issues: {feedback[:200]}...")
            status_log.append("♻️ Regenerating chapters with feedback...")
            yield expanded_plot, chapters, "", "\n".join(status_log)
            chapters = generate_chapters(expanded_plot, num_chapters, feedback)
            status_log.append("🔄 New version of chapters generated.")
            yield expanded_plot, chapters, "", "\n".join(status_log)
        else:
            status_log.append(f"❌ Validation error: {feedback}")
            yield expanded_plot, chapters, "", "\n".join(status_log)
            break

    if validation_round >= MAX_VALIDATION_ATTEMPTS:
        status_log.append("⚠️ Max validation attempts reached, using latest chapters.")
        yield expanded_plot, chapters, "", "\n".join(status_log)

    # STEP 4 - Generate Chapters Iteratively
    status_log.append("📖 Step 4: Generating full chapter texts...")
    yield expanded_plot, chapters, "", "\n".join(status_log)

    for i in range(1, int(num_chapters) + 1):
        chapter_title = f"Chapter {i}"
        status_log.append(f"🪶 Writing {chapter_title}...")
        yield expanded_plot, chapters, "\n".join(
            [f"{k}\n{v}\n" for k, v in full_chapter_texts.items()]
        ), "\n".join(status_log)

        # generate one chapter
        chapter_text = generate_chapter_text(expanded_plot, chapters, i)
        full_chapter_texts[chapter_title] = chapter_text

        status_log.append(f"✅ {chapter_title} completed.")
        yield expanded_plot, chapters, "\n".join(
            [f"{k}\n{v}\n" for k, v in full_chapter_texts.items()]
        ), "\n".join(status_log)

    status_log.append("🎉 All chapters generated successfully!")
    yield expanded_plot, chapters, "\n".join(
        [f"{k}\n{v}\n" for k, v in full_chapter_texts.items()]
    ), "\n".join(status_log)


# ---------- UI ------------
with gr.Blocks(title="BookKing - AI Story Creator") as demo:
    gr.Markdown("""
    # 📚 BookKing - Live AI Story Creator  
    _Automatically generate, validate, and expand your novel in real time._
    """)

    with gr.Row():
        plot_input = gr.Textbox(
            label="Short Plot Description",
            lines=3,
            placeholder="Ex: A young girl discovers a portal to another world..."
        )
        chapters_input = gr.Number(
            label="Number of Chapters",
            value=10,
            precision=0
        )

    generate_btn = gr.Button("🚀 Generate Full Book (Live)")

    with gr.Row():
        expanded_output = gr.Textbox(label="📝 Expanded Plot (Step 1)", lines=12)
        chapters_output = gr.Textbox(label="📘 Chapters Overview (Step 2-3)", lines=12)

    with gr.Row():
        full_book_output = gr.Textbox(label="📖 Generated Chapters (Step 4)", lines=20)
        status_output = gr.Textbox(label="🧩 Process Log", lines=20)

    generate_btn.click(
        fn=generate_full_book_stream,
        inputs=[plot_input, chapters_input],
        outputs=[expanded_output, chapters_output, full_book_output, status_output]
    )

demo.launch(server_name="0.0.0.0", server_port=7860)
