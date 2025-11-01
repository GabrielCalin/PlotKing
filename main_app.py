# -*- coding: utf-8 -*-
import gradio as gr
from datetime import datetime
from pipeline.step0_refine_plot import refine_plot
from pipeline.step1_plot_expander import expand_plot
from pipeline.step2_chapter_generator import generate_chapters
from pipeline.step3_validator import validate_chapters
from pipeline.step4_chapter_writer import generate_chapter_text
from pipeline.step5_chapter_validator import validate_chapter
from ui.interface import create_interface
from pipeline.constants import RUN_MODE_CHOICES
from pipeline.state_manager import is_stop_requested, save_checkpoint, clear_stop
from pipeline.pipeline_state import PipelineState

MAX_VALIDATION_ATTEMPTS = 3


def ts_prefix(message: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    return f"[{timestamp}] {message}"


def vtext_add(section: str, validation_text: str) -> str:
    if not validation_text:
        return section
    validation_text = validation_text.rstrip("\n")
    return validation_text + "\n\n" + section


def maybe_pause_pipeline(step_label: str, state: PipelineState):
    if not is_stop_requested():
        return False
    save_checkpoint(state.to_dict())
    state.status_log.append(ts_prefix(f"🛑 Stop requested — pipeline paused after {step_label}."))
    yield (
        state.expanded_plot,
        state.chapters_overview,
        state.chapters_full,
        gr.update(),
        gr.update(choices=state.choices) if state.choices is not None else gr.update(),
        "_Paused_",
        "\n".join(state.status_log),
        state.validation_text,
    )
    return True


def apply_refresh_point(state: PipelineState, refresh_from):
    state.pending_validation_index = None
    state.next_chapter_index = None

    if refresh_from == "expanded":
        state.expanded_plot = None
        state.chapters_overview = None
        state.chapters_full = []
        state.overview_validated = False

    elif refresh_from == "overview":
        state.chapters_overview = None
        state.chapters_full = []
        state.overview_validated = False

    elif isinstance(refresh_from, int):
        keep_until = min(refresh_from - 1, len(state.chapters_full))
        state.chapters_full = state.chapters_full[:keep_until]
        state.next_chapter_index = refresh_from
        state.pending_validation_index = None

    return state


def generate_book_outline_stream(plot, num_chapters, genre, anpc, run_mode, checkpoint=None, refresh_from=None):
    clear_stop()

    if checkpoint:
        state = PipelineState.from_checkpoint(checkpoint)
        state.run_mode = run_mode
        if refresh_from:
            state.status_log.append(ts_prefix("🔁 Regeneration requested..."))
            state = apply_refresh_point(state, refresh_from)
    else:
        state = PipelineState(
            expanded_plot=None,
            chapters_overview=None,
            chapters_full=[],
            validation_text="",
            status_log=[],
            genre=genre,
            anpc=anpc,
            plot=plot,
            num_chapters=num_chapters,
            run_mode=run_mode,
        )

    if not checkpoint and not state.plot.strip():
        yield "Please enter a plot description.", "", [], "", gr.update(choices=[], value=None), \
              "_No chapters yet_", "⚠️ No input provided.", ""
        return

    if state.expanded_plot is None:
        state.status_log.append(ts_prefix("📝 Step 1: Expanding plot..."))
        yield "", "", [], "", gr.update(choices=[], value=None), "_No chapters yet_", "\n".join(state.status_log), state.validation_text

        state.expanded_plot = expand_plot(state.plot, state.genre)
        state.status_log.append(ts_prefix("✅ Plot expanded."))
        yield state.expanded_plot, "", [], "", gr.update(choices=[], value=None), "_Ready for chapters..._", "\n".join(state.status_log), state.validation_text

        if (yield from maybe_pause_pipeline("plot expansion", state)):
            return

    if state.chapters_overview is None:
        state.status_log.append(ts_prefix("📘 Step 2: Generating chapter overview..."))
        yield state.expanded_plot, "", [], "", gr.update(choices=[], value=None), "_Generating overview..._", "\n".join(state.status_log), state.validation_text

        state.chapters_overview = generate_chapters(state.plot, state.expanded_plot, state.num_chapters, state.genre)
        state.status_log.append(ts_prefix("✅ Chapters overview generated."))
        yield state.expanded_plot, state.chapters_overview, [], "", gr.update(choices=[], value=None), "_Overview ready_", "\n".join(state.status_log), state.validation_text

        if (yield from maybe_pause_pipeline("chapter overview generation", state)):
            return

    if not state.overview_validated:
        validation_round = 0
        feedback = ""
        while validation_round < MAX_VALIDATION_ATTEMPTS:
            validation_round += 1
            result, feedback = validate_chapters(state.plot, state.expanded_plot, state.chapters_overview, state.genre)
            if result == "OK":
                state.status_log.append(ts_prefix("✅ Overview validation passed."))
                state.validation_text = vtext_add("✅ Chapters Overview Validation: PASSED", state.validation_text)
                state.overview_validated = True
                break
            elif result == "NOT OK":
                state.status_log.append(ts_prefix("⚠️ Overview validation issues found."))
                state.validation_text = vtext_add(f"⚠️ Chapters Overview Validation Feedback (attempt {validation_round}):\n{feedback}", state.validation_text)
                state.chapters_overview = generate_chapters(state.plot, state.expanded_plot, state.num_chapters, state.genre, feedback=feedback,previous_output=state.chapters_overview)
                state.status_log.append(ts_prefix("🔄 Revised overview with feedback."))
            else:
                state.status_log.append(ts_prefix(f"❌ Overview validation error: {feedback}"))
                state.validation_text = vtext_add(f"❌ Validation Error:\n{feedback}", state.validation_text)
                break

            yield state.expanded_plot, state.chapters_overview, [], "", gr.update(choices=[], value=None), "_Validating overview..._", "\n".join(state.status_log), state.validation_text

        if not state.overview_validated:
            state.overview_validated = True

        if (yield from maybe_pause_pipeline("overview validation", state)):
            return

    if state.run_mode == RUN_MODE_CHOICES["OVERVIEW"]:
        save_checkpoint(state.to_dict())
        state.status_log.append(ts_prefix("⏹️ Stopped after chapters overview as requested."))
        yield state.expanded_plot, state.chapters_overview, [], "", gr.update(choices=[], value=None), "_Stopped after overview_", "\n".join(state.status_log), state.validation_text
        return

    state.status_log.append(ts_prefix("🚀 Step 4: Writing chapters..."))
    preloop_choices = [f"Chapter {j+1}" for j in range(len(state.chapters_full))]
    yield (
        state.expanded_plot,
        state.chapters_overview,
        state.chapters_full,
        gr.update(),
        gr.update(choices=preloop_choices),
        "_Starting chapter generation..._",
        "\n".join(state.status_log),
        state.validation_text,
    )

    if state.pending_validation_index:
        start_index = int(state.pending_validation_index)
    elif state.next_chapter_index:
        start_index = min(int(state.next_chapter_index), len(state.chapters_full) + 1)
    else:
        start_index = len(state.chapters_full) + 1

    first_chapter_text = ""
    first_display_done = len(state.chapters_full) > 0

    for i in range(start_index - 1, state.num_chapters):
        current_index = i + 1
        state.choices = [f"Chapter {j+1}" for j in range(len(state.chapters_full))]
        is_pending_validation = (state.pending_validation_index == current_index)

        if not is_pending_validation:
            state.status_log.append(ts_prefix(f"✍️ Generating Chapter {current_index}/{state.num_chapters}..."))
            yield (
                state.expanded_plot,
                state.chapters_overview,
                state.chapters_full,
                gr.update(),
                gr.update(choices=state.choices),
                f"Generating chapter {current_index}...",
                "\n".join(state.status_log),
                state.validation_text,
            )

            chapter_text = generate_chapter_text(state.expanded_plot, state.chapters_overview, current_index, state.chapters_full, state.genre, state.anpc)
            state.chapters_full.append(chapter_text)
            state.status_log.append(ts_prefix(f"✅ Chapter {current_index} generated."))

            state.choices = [f"Chapter {j+1}" for j in range(len(state.chapters_full))]
            if current_index == 1 and not first_chapter_text:
                first_chapter_text = state.chapters_full[0]
            if current_index == 1 and not first_display_done:
                dropdown_update = gr.update(choices=state.choices, value="Chapter 1")
                current_text_update = first_chapter_text
                first_display_done = True
            else:
                dropdown_update = gr.update(choices=state.choices)
                current_text_update = gr.update()

            counter_value = f"📘 {len(state.chapters_full)} chapter(s) generated so far"
            yield (
                state.expanded_plot,
                state.chapters_overview,
                state.chapters_full,
                current_text_update,
                dropdown_update,
                counter_value,
                "\n".join(state.status_log),
                state.validation_text,
            )

            state.next_chapter_index = current_index
            state.pending_validation_index = current_index
            if (yield from maybe_pause_pipeline(f"chapter {current_index} generation", state)):
                return

        else:
            state.status_log.append(ts_prefix(f"▶️ Resuming with validation for Chapter {current_index}..."))
            chapter_text = state.chapters_full[current_index - 1]
            yield (
                state.expanded_plot,
                state.chapters_overview,
                state.chapters_full,
                gr.update(),
                gr.update(choices=state.choices),
                f"Validating chapter {current_index}...",
                "\n".join(state.status_log),
                state.validation_text,
            )

        validation_attempts = 0
        while validation_attempts < MAX_VALIDATION_ATTEMPTS:
            state.status_log.append(ts_prefix(f"🧩 Step 5: Validating Chapter {current_index}..."))
            yield (
                state.expanded_plot,
                state.chapters_overview,
                state.chapters_full,
                gr.update(),
                gr.update(choices=state.choices),
                f"Validating chapter {current_index}...",
                "\n".join(state.status_log),
                state.validation_text,
            )

            result, feedback = validate_chapter(
                state.expanded_plot,
                state.chapters_overview,
                state.chapters_full[:-1],
                chapter_text,
                current_index,
                state.genre
            )

            if result == "OK":
                state.validation_text = vtext_add(f"✅ Chapter {current_index} Validation: PASSED", state.validation_text)
                state.status_log.append(ts_prefix(f"✅ Chapter {current_index} passed validation."))
                break
            elif result == "NOT OK":
                state.validation_text = vtext_add(f"⚠️ Chapter {current_index} Validation Feedback:\n{feedback}", state.validation_text)
                state.status_log.append(ts_prefix(f"⚠️ Chapter {current_index} failed validation — regenerating."))
                yield (
                    state.expanded_plot,
                    state.chapters_overview,
                    state.chapters_full,
                    gr.update(),
                    gr.update(choices=state.choices),
                    f"Regenerating chapter {current_index}...",
                    "\n".join(state.status_log),
                    state.validation_text,
                )
                chapter_text = generate_chapter_text(
                    state.expanded_plot,
                    state.chapters_overview,
                    current_index,
                    state.chapters_full[:-1],
                    state.genre,
                    state.anpc,
                    feedback=feedback
                )
                state.chapters_full[-1] = chapter_text
                state.status_log.append(ts_prefix(f"✅ Chapter {current_index} regenerated successfully."))
            else:
                state.validation_text = vtext_add(f"❌ Chapter {current_index} Validation Error:\n{feedback}", state.validation_text)
                state.status_log.append(ts_prefix(f"❌ Validation error or unknown result for Chapter {current_index}."))
                break

            validation_attempts += 1

        state.next_chapter_index = current_index + 1
        state.pending_validation_index = None
        if (yield from maybe_pause_pipeline(f"chapter {current_index} complete", state)):
            return

        state.choices = [f"Chapter {j+1}" for j in range(len(state.chapters_full))]
        if current_index == 1 and first_chapter_text and not first_display_done:
            dropdown_update = gr.update(choices=state.choices, value="Chapter 1")
            current_text_update = first_chapter_text
            first_display_done = True
        else:
            dropdown_update = gr.update(choices=state.choices)
            current_text_update = gr.update()

        counter_value = f"📘 {len(state.chapters_full)} chapter(s) generated so far"
        yield (
            state.expanded_plot,
            state.chapters_overview,
            state.chapters_full,
            current_text_update,
            dropdown_update,
            counter_value,
            "\n".join(state.status_log),
            state.validation_text,
        )

    state.status_log.append(ts_prefix("🎉 All chapters generated successfully!"))
    final_choices = [f"Chapter {i+1}" for i in range(len(state.chapters_full))]
    dropdown_final = gr.update(choices=final_choices)
    counter_final = f"✅ All {len(state.chapters_full)} chapters generated!"
    state.validation_text = vtext_add("🎯 All validations passed successfully.", state.validation_text)
    
    state.next_chapter_index = None
    state.pending_validation_index = None
    save_checkpoint(state.to_dict())
    
    yield state.expanded_plot, state.chapters_overview, state.chapters_full, gr.update(), dropdown_final, counter_final, "\n".join(state.status_log), state.validation_text


def generate_book_outline_stream_resume(checkpoint):
    plot = checkpoint.get("plot", "")
    num_chapters = checkpoint.get("num_chapters", 0)
    genre = checkpoint.get("genre", "")
    anpc = checkpoint.get("anpc", 0)
    run_mode = checkpoint.get("run_mode", RUN_MODE_CHOICES["FULL"])
    return generate_book_outline_stream(plot, num_chapters, genre, anpc, run_mode, checkpoint=checkpoint)


if __name__ == "__main__":
    demo = create_interface(generate_book_outline_stream, refine_plot)
    demo.launch(server_name="0.0.0.0", server_port=7860)
