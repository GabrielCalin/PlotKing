# -*- coding: utf-8 -*-
import gradio as gr
from step1_plot_expander import expand_plot
from step2_chapter_generator import generate_chapters
from step3_validator import validate_chapters
from step4_chapter_writer import generate_chapter_text

MAX_VALIDATION_ATTEMPTS = 3


def generate_book_outline_stream(plot, num_chapters):
    """Pipeline streaming: yields updates after each stage."""
    if not plot.strip():
        yield "Please enter a plot description.", "", [], "", "", "", "⚠️ No input provided."
        return

    status_log = []
    chapters_full = []
    first_chapter_shown = False

    def chapter_ui(chapters, lock_selection=False):
        """Return dropdown + counter updated live."""
        if not chapters:
            return gr.Dropdown(choices=[], value=None), gr.Markdown("_No chapters yet_")
        choices = [f"Chapter {i+1}" for i in range(len(chapters))]
        # dacă e blocat, nu schimbăm value (evităm declanșarea .change)
        if lock_selection:
            return gr.Dropdown(choices=choices, value=gr.update()), gr.Markdown(
                f"📘 {len(chapters)} chapter(s) generated so far"
            )
        return gr.Dropdown(choices=choices, value=choices[-1]), gr.Markdown(
            f"📘 {len(chapters)} chapter(s) generated so far"
        )

    # STEP 1
    status_log.append("📝 Step 1: Expanding plot...")
    yield "", "", [], "", "", "", "\n".join(status_log)
    expanded_plot = expand_plot(plot)
    status_log.append("✅ Plot expanded.")
    dropdown, counter = chapter_ui(chapters_full)
    yield expanded_plot, "", chapters_full, "", dropdown, counter, "\n".join(status_log)

    # STEP 2
    status_log.append("📘 Step 2: Generating chapter overview...")
    yield expanded_plot, "", chapters_full, "", dropdown, counter, "\n".join(status_log)
    chapters_overview = generate_chapters(expanded_plot, num_chapters)
    status_log.append("✅ Chapters overview generated.")
    dropdown, counter = chapter_ui(chapters_full)
    yield expanded_plot, chapters_overview, chapters_full, "", dropdown, counter, "\n".join(status_log)

    # STEP 3 - validation
    validation_round = 0
    while validation_round < MAX_VALIDATION_ATTEMPTS:
        validation_round += 1
        status_log.append(f"🔍 Step 3: Validating chapters (attempt {validation_round})...")
        yield expanded_plot, chapters_overview, chapters_full, "", dropdown, counter, "\n".join(status_log)

        result, feedback = validate_chapters(expanded_plot, chapters_overview, iteration=validation_round)

        if result == "OK":
            status_log.append("✅ Validation passed.")
            break
        elif result == "NOT OK":
            status_log.append(f"⚠️ Issues found: {feedback[:200]}...")
            status_log.append("♻️ Regenerating overview with feedback...")
            yield expanded_plot, chapters_overview, chapters_full, "", dropdown, counter, "\n".join(status_log)
            chapters_overview = generate_chapters(expanded_plot, num_chapters, feedback)
            status_log.append("🔄 New version of chapter overview generated.")
        else:
            status_log.append(f"❌ Validation error: {feedback}")
            break

    # STEP 4 - generare capitole
    status_log.append("🚀 Step 4: Writing full chapters iteratively...")
    yield expanded_plot, chapters_overview, chapters_full, "", dropdown, counter, "\n".join(status_log)

    for i in range(num_chapters):
        current_index = i + 1
        status_log.append(f"✍️ Generating Chapter {current_index}/{num_chapters}...")
        yield expanded_plot, chapters_overview, chapters_full, "", dropdown, counter, "\n".join(status_log)

        chapter_text = generate_chapter_text(expanded_plot, chapters_overview, current_index, chapters_full)
        chapters_full.append(f"Chapter {current_index}: {chapter_text[:10000]}")

        status_log.append(f"✅ Chapter {current_index} generated.")

        # 🔧 generăm lista de capitole actualizată
        choices = [f"Chapter {j+1}" for j in range(len(chapters_full))]
        counter = gr.Markdown(f"📘 {len(chapters_full)} chapter(s) generated so far")

        if not first_chapter_shown:
            first_chapter_shown = True
            dropdown = gr.update(choices=choices, value="Chapter 1")  # primul selectat
            current_output = chapters_full[0]  # afișăm primul capitol
        else:
            dropdown = gr.update(choices=choices, value=None)  # doar actualizăm lista
            current_output = gr.update()  # nu modificăm conținutul

        yield (
            expanded_plot,
            chapters_overview,
            chapters_full,
            current_output,
            dropdown,
            counter,
            "\n".join(status_log),
        )

    # la final
    status_log.append("🎉 All chapters generated successfully!")
    final_choices = [f"Chapter {i+1}" for i in range(len(chapters_full))]
    dropdown = gr.update(choices=final_choices, value="Chapter 1")  # rămâne pe primul
    counter = gr.Markdown(f"✅ All {len(chapters_full)} chapters generated!")
    yield expanded_plot, chapters_overview, chapters_full, gr.update(), dropdown, counter, "\n".join(status_log)


# ---------- UI ------------
with gr.Blocks(title="BookKing - Live AI Story Planner") as demo:
    gr.Markdown("""
    # 📖 BookKing - Live Story Planner  
    _Generate, validate, and refine your novel outline interactively._
    """)

    with gr.Row():
        plot_input = gr.Textbox(
            label="Short Plot Description",
            lines=3,
            placeholder="Ex: A young girl discovers a portal to another world..."
        )
        chapters_input = gr.Number(label="Number of Chapters", value=5, precision=0)

    generate_btn = gr.Button("🚀 Generate Book (Live)")

    with gr.Row():
        expanded_output = gr.Textbox(label="📝 Expanded Plot (Step 1)", lines=15)
        chapters_output = gr.Textbox(label="📘 Chapters Overview (Step 2)", lines=15)

    with gr.Row():
        with gr.Column(scale=1):
            chapter_selector = gr.Dropdown(label="📖 Select Chapter", choices=[], interactive=True)
            chapter_counter = gr.Markdown("_No chapters yet_")
        with gr.Column(scale=3):
            current_chapter_output = gr.Textbox(label="📚 Current Chapter", lines=25)

    status_output = gr.Textbox(label="🧩 Process Log", lines=15)

    chapters_state = gr.State([])

    def display_selected_chapter(chapter_name, chapters):
        if not chapters or not chapter_name:
            return ""
        idx = int(chapter_name.split(" ")[1]) - 1
        if 0 <= idx < len(chapters):
            return chapters[idx]
        return ""

    # --- Wiring ---
    book_generator = generate_btn.click(
        fn=generate_book_outline_stream,
        inputs=[plot_input, chapters_input],
        outputs=[
            expanded_output,
            chapters_output,
            chapters_state,
            current_chapter_output,
            chapter_selector,
            chapter_counter,
            status_output,
        ]
    )

    chapter_selector.change(
        fn=display_selected_chapter,
        inputs=[chapter_selector, chapters_state],
        outputs=[current_chapter_output]
    )

demo.launch(server_name="0.0.0.0", server_port=7860)
