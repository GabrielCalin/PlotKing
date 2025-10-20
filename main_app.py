# -*- coding: utf-8 -*-
import gradio as gr
from step1_plot_expander import expand_plot
from step2_chapter_generator import generate_chapters
from step3_validator import validate_chapters
from step4_chapter_writer import generate_chapter_text
from step5_chapter_validator import validate_chapter

MAX_VALIDATION_ATTEMPTS = 3


def generate_book_outline_stream(plot, num_chapters):
    """
    Stable streaming pipeline:
    - Dropdown: sets value="Chapter 1" only for the first chapter.
    - Current Chapter: updates only once (when Chapter 1 is generated).
    """
    if not plot.strip():
        yield "Please enter a plot description.", "", [], "", gr.update(choices=[], value=None), "_No chapters yet_", "⚠️ No input provided."
        return

    status_log = []
    chapters_full = []
    first_chapter_text = ""
    first_display_done = False

    # --- STEP 1 ---
    status_log.append("📝 Step 1: Expanding plot...")
    yield "", "", [], "", gr.update(choices=[], value=None), "_No chapters yet_", "\n".join(status_log)

    expanded_plot = expand_plot(plot)
    status_log.append("✅ Plot expanded.")
    yield expanded_plot, "", [], "", gr.update(choices=[], value=None), "_Ready for chapters..._", "\n".join(status_log)

    # --- STEP 2 ---
    status_log.append("📘 Step 2: Generating chapter overview...")
    yield expanded_plot, "", [], "", gr.update(choices=[], value=None), "_Generating overview..._", "\n".join(status_log)

    chapters_overview = generate_chapters(expanded_plot, num_chapters)
    status_log.append("✅ Chapters overview generated.")
    yield expanded_plot, chapters_overview, [], "", gr.update(choices=[], value=None), "_Overview ready_", "\n".join(status_log)

    # --- STEP 3 (validation) ---
    validation_round = 0
    while validation_round < MAX_VALIDATION_ATTEMPTS:
        validation_round += 1
        result, feedback = validate_chapters(expanded_plot, chapters_overview, iteration=validation_round)
        if result == "OK":
            status_log.append("✅ Validation passed.")
            break
        elif result == "NOT OK":
            status_log.append(f"⚠️ Issues found: {feedback[:200]}...")
            chapters_overview = generate_chapters(expanded_plot, num_chapters, feedback)
            status_log.append("🔄 Regenerated overview.")
        else:
            status_log.append(f"❌ Validation error: {feedback}")
            break

    status_log.append("🚀 Step 4: Writing chapters...")
    yield expanded_plot, chapters_overview, [], "", gr.update(choices=[], value=None), "_Starting..._", "\n".join(status_log)

    # --- STEP 4: generate chapters one by one ---
    for i in range(num_chapters):
        current_index = i + 1
        status_log.append(f"✍️ Generating Chapter {current_index}/{num_chapters}...")

        # always define choices before any yield
        choices = [f"Chapter {j+1}" for j in range(len(chapters_full))]

        # PRE-yield: before generation
        yield (
            expanded_plot,
            chapters_overview,
            chapters_full,
            gr.update(),
            gr.update(choices=choices),
            f"Generating chapter {current_index}...",
            "\n".join(status_log),
        )

        # generate chapter
        chapter_text = generate_chapter_text(expanded_plot, chapters_overview, current_index, chapters_full)
        chapters_full.append(f"Chapter {current_index}: {chapter_text[:10000]}")
        status_log.append(f"✅ Chapter {current_index} generated.")

        # --- Step 5: Validate the generated chapter ---
        status_log.append(f"🧩 Step 5: Validating Chapter {current_index}...")

        # define choices again (now includes the new chapter)
        choices = [f"Chapter {j+1}" for j in range(len(chapters_full))]

        yield (
            expanded_plot,
            chapters_overview,
            chapters_full,
            gr.update(),
            gr.update(choices=choices),
            f"Validating chapter {current_index}...",
            "\n".join(status_log),
        )

        result, feedback = validate_chapter(
            expanded_plot,
            chapters_overview,
            chapters_full[:-1],
            chapter_text,
            current_index
        )

        if result == "OK":
            status_log.append(f"✅ Chapter {current_index} passed validation.")
        elif result == "NOT OK":
            status_log.append(f"⚠️ Chapter {current_index} failed validation — regenerating.")
            yield (
                expanded_plot,
                chapters_overview,
                chapters_full,
                gr.update(),
                gr.update(choices=choices),
                f"Regenerating chapter {current_index}...",
                "\n".join(status_log),
            )
            # regenerate with feedback
            chapter_text = generate_chapter_text(
                expanded_plot,
                chapters_overview,
                current_index,
                chapters_full[:-1],
                feedback=feedback
            )
            chapters_full[-1] = f"Chapter {current_index}: {chapter_text[:10000]}"
            status_log.append(f"✅ Chapter {current_index} regenerated successfully.")
        else:
            status_log.append(f"❌ Validation error or unknown result for Chapter {current_index}.")

        # after validation: update dropdown + display
        choices = [f"Chapter {j+1}" for j in range(len(chapters_full))]

        if current_index == 1 and not first_display_done:
            first_chapter_text = chapters_full[0]
            dropdown_update = gr.update(choices=choices, value="Chapter 1")
            current_text_update = first_chapter_text
            first_display_done = True
        else:
            dropdown_update = gr.update(choices=choices)
            current_text_update = gr.update()

        counter_value = f"📘 {len(chapters_full)} chapter(s) generated so far"
        yield (
            expanded_plot,
            chapters_overview,
            chapters_full,
            current_text_update,
            dropdown_update,
            counter_value,
            "\n".join(status_log),
        )

    # --- FINAL ---
    status_log.append("🎉 All chapters generated successfully!")
    final_choices = [f"Chapter {i+1}" for i in range(len(chapters_full))]
    dropdown_final = gr.update(choices=final_choices)
    counter_final = f"✅ All {len(chapters_full)} chapters generated!"
    yield expanded_plot, chapters_overview, chapters_full, gr.update(), dropdown_final, counter_final, "\n".join(status_log)


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
            chapter_selector = gr.Dropdown(label="📖 Select Chapter", choices=[], value=None, interactive=True)
            chapter_counter = gr.Markdown("_No chapters yet_")
        with gr.Column(scale=3):
            current_chapter_output = gr.Textbox(label="📚 Current Chapter", lines=25)

    status_output = gr.Textbox(label="🧩 Process Log", lines=15)
    chapters_state = gr.State([])

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

    # --- Wiring ---
    generate_btn.click(
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

    # User selection handler
    chapter_selector.change(
        fn=display_selected_chapter,
        inputs=[chapter_selector, chapters_state],
        outputs=[current_chapter_output]
    )

demo.launch(server_name="0.0.0.0", server_port=7860)
