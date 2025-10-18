# -*- coding: utf-8 -*-
import gradio as gr
from step1_plot_expander import expand_plot
from step2_chapter_generator import generate_chapters
from step3_validator import validate_chapters

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


# ---------- UI ------------
with gr.Blocks(title="BookKing - Live AI Story Planner") as demo:
    gr.Markdown("""
    # 📖 BookKing - Live Story Planner  
    _Generate, validate, and refine a novel outline interactively._
    """)
    
    with gr.Row():
        plot_input = gr.Textbox(label="Short Plot Description", lines=3, placeholder="Ex: A young girl discovers a portal to another world...")
        chapters_input = gr.Number(label="Number of Chapters", value=10, precision=0)
    
    generate_btn = gr.Button("🚀 Generate Outline (Live)")
    
    with gr.Row():
        expanded_output = gr.Textbox(label="📝 Expanded Plot (Step 1)", lines=18)
        chapters_output = gr.Textbox(label="📘 Chapters Overview (Step 2)", lines=18)
    
    status_output = gr.Textbox(label="🧩 Process Log (Step 3 Validation)", lines=12)
    
    generate_btn.click(
        fn=generate_book_outline_stream,
        inputs=[plot_input, chapters_input],
        outputs=[expanded_output, chapters_output, status_output]
    )

demo.launch(server_name="0.0.0.0", server_port=7860)
