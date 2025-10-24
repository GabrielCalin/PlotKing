# -*- coding: utf-8 -*-
import gradio as gr
from datetime import datetime
from pipeline.step1_plot_expander import expand_plot
from pipeline.step2_chapter_generator import generate_chapters
from pipeline.step3_validator import validate_chapters
from pipeline.step4_chapter_writer import generate_chapter_text
from pipeline.step5_chapter_validator import validate_chapter
from ui.interface import create_interface

MAX_VALIDATION_ATTEMPTS = 3


def ts_prefix(message: str) -> str:
    """Return message prefixed with current datetime up to milliseconds."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    return f"[{timestamp}] {message}"


def generate_book_outline_stream(plot, num_chapters, genre, anpc):
    """
    Stable streaming pipeline:
    - Dropdown: sets value="Chapter 1" only for the first chapter.
    - Current Chapter: updates only once (when Chapter 1 is generated).
    - Validation Feedback: displays feedback for both overview & chapters.
    """
    if not plot.strip():
        yield "Please enter a plot description.", "", [], "", gr.update(choices=[], value=None), \
              "_No chapters yet_", "⚠️ No input provided.", ""
        return

    status_log = []
    chapters_full = []
    first_chapter_text = ""
    first_display_done = False
    validation_text = ""

    # --- STEP 1 ---
    status_log.append(ts_prefix("📝 Step 1: Expanding plot..."))
    yield "", "", [], "", gr.update(choices=[], value=None), "_No chapters yet_", "\n".join(status_log), validation_text

    expanded_plot = expand_plot(plot, genre)
    status_log.append(ts_prefix("✅ Plot expanded."))
    yield expanded_plot, "", [], "", gr.update(choices=[], value=None), "_Ready for chapters..._", "\n".join(status_log), validation_text

    # --- STEP 2 ---
    status_log.append(ts_prefix("📘 Step 2: Generating chapter overview..."))
    yield expanded_plot, "", [], "", gr.update(choices=[], value=None), "_Generating overview..._", "\n".join(status_log), validation_text

    chapters_overview = generate_chapters(plot, expanded_plot, num_chapters, genre)
    status_log.append(ts_prefix("✅ Chapters overview generated."))
    yield expanded_plot, chapters_overview, [], "", gr.update(choices=[], value=None), "_Overview ready_", "\n".join(status_log), validation_text

    # --- STEP 3 (validation) ---
    validation_round = 0
    feedback = ""
    while validation_round < MAX_VALIDATION_ATTEMPTS:
        validation_round += 1
        result, feedback = validate_chapters(plot, expanded_plot, chapters_overview, genre)
        if result == "OK":
            status_log.append(ts_prefix("✅ Overview validation passed."))
            validation_text += "✅ Chapters Overview Validation: PASSED"
            break
        elif result == "NOT OK":
            status_log.append(ts_prefix("⚠️ Overview validation issues found."))
            if validation_text:
                validation_text += f"\n\n⚠️ Chapters Overview Validation Feedback (attempt {validation_round}):\n{feedback}"
            else:
                validation_text += f"⚠️ Chapters Overview Validation Feedback (attempt {validation_round}):\n{feedback}"
            chapters_overview = generate_chapters(plot, expanded_plot, num_chapters, genre, feedback)
            status_log.append(ts_prefix("🔄 Regenerated overview with feedback."))
        else:
            status_log.append(ts_prefix(f"❌ Overview validation error: {feedback}"))
            if validation_text:
                validation_text += f"\n\n❌ Validation Error:\n{feedback}"
            else:
                validation_text += f"❌ Validation Error:\n{feedback}"
            break

        yield expanded_plot, chapters_overview, [], "", gr.update(choices=[], value=None), "_Validating overview..._", "\n".join(status_log), validation_text

    status_log.append(ts_prefix("🚀 Step 4: Writing chapters..."))
    yield expanded_plot, chapters_overview, [], "", gr.update(choices=[], value=None), "_Starting chapter generation..._", "\n".join(status_log), validation_text

    # --- STEP 4 + STEP 5 ---
    for i in range(num_chapters):
        current_index = i + 1
        status_log.append(ts_prefix(f"✍️ Generating Chapter {current_index}/{num_chapters}..."))
        choices = [f"Chapter {j+1}" for j in range(len(chapters_full))]

        yield (
            expanded_plot,
            chapters_overview,
            chapters_full,
            gr.update(),
            gr.update(choices=choices),
            f"Generating chapter {current_index}...",
            "\n".join(status_log),
            validation_text,
        )

        # generate chapter
        chapter_text = generate_chapter_text(expanded_plot, chapters_overview, current_index, chapters_full, genre, anpc)
        chapters_full.append(chapter_text)
        status_log.append(ts_prefix(f"✅ Chapter {current_index} generated."))

        validation_attempts = 0
        while validation_attempts < MAX_VALIDATION_ATTEMPTS:
            status_log.append(ts_prefix(f"🧩 Step 5: Validating Chapter {current_index}..."))
            choices = [f"Chapter {j+1}" for j in range(len(chapters_full))]

            yield (
                expanded_plot,
                chapters_overview,
                chapters_full,
                gr.update(),
                gr.update(choices=choices),
                f"Validating chapter {current_index}...",
                "\n".join(status_log),
                validation_text,
            )

            result, feedback = validate_chapter(
                expanded_plot,
                chapters_overview,
                chapters_full[:-1],
                chapter_text,
                current_index,
                genre
            )

            if result == "OK":
                status_log.append(ts_prefix(f"✅ Chapter {current_index} passed validation."))
                validation_text += f"\n\n✅ Chapter {current_index} Validation: PASSED"
                break
            elif result == "NOT OK":
                status_log.append(ts_prefix(f"⚠️ Chapter {current_index} failed validation — regenerating."))
                validation_text += f"\n\n⚠️ Chapter {current_index} Validation Feedback:\n{feedback}"
                yield (
                    expanded_plot,
                    chapters_overview,
                    chapters_full,
                    gr.update(),
                    gr.update(choices=choices),
                    f"Regenerating chapter {current_index}...",
                    "\n".join(status_log),
                    validation_text,
                )
                chapter_text = generate_chapter_text(
                    expanded_plot,
                    chapters_overview,
                    current_index,
                    chapters_full[:-1],
                    genre,
                    anpc,
                    feedback=feedback
                )
                chapters_full[-1] = chapter_text
                status_log.append(ts_prefix(f"✅ Chapter {current_index} regenerated successfully."))
            else:
                status_log.append(ts_prefix(f"❌ Validation error or unknown result for Chapter {current_index}."))
                validation_text += f"\n\n❌ Chapter {current_index} Validation Error:\n{feedback}"
                break

            validation_attempts += 1

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
            validation_text,
        )

    status_log.append(ts_prefix("🎉 All chapters generated successfully!"))
    final_choices = [f"Chapter {i+1}" for i in range(len(chapters_full))]
    dropdown_final = gr.update(choices=final_choices)
    counter_final = f"✅ All {len(chapters_full)} chapters generated!"
    validation_text += "\n\n🎯 All validations passed successfully."
    yield expanded_plot, chapters_overview, chapters_full, gr.update(), dropdown_final, counter_final, "\n".join(status_log), validation_text


# ---------- Launch UI ----------
if __name__ == "__main__":
    from ui.interface import create_interface

    def refine_plot(current_text):
        # momentan doar returnăm textul rafinat dummy
        return current_text + "\n\n[Refined version generated here.]"

    demo = create_interface(generate_book_outline_stream, refine_plot)
    demo.launch(server_name="0.0.0.0", server_port=7860)
