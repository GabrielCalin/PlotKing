# -*- coding: utf-8 -*-
import gradio as gr
from step1_plot_expander import expand_plot
from step2_chapter_generator import generate_chapters
from step3_validator import validate_chapters

MAX_VALIDATION_ATTEMPTS = 3

def generate_book_outline(plot, num_chapters):
    """Main pipeline: step1 → step2 → step3 (feedback loop)"""
    if not plot.strip():
        return "Please enter a plot description.", "", ""
    
    status_log = []
    
    # STEP 1: expand the plot
    status_log.append("📝 Step 1: Expanding plot...")
    expanded_plot = expand_plot(plot)
    
    # STEP 2: generate chapters
    status_log.append("📘 Step 2: Generating chapters...")
    chapters = generate_chapters(expanded_plot, num_chapters)
    
    # STEP 3: validation loop
    validation_round = 0
    while validation_round < MAX_VALIDATION_ATTEMPTS:
        validation_round += 1
        status_log.append(f"🔍 Step 3: Validating chapters (attempt {validation_round})...")
        
        result, feedback = validate_chapters(expanded_plot, chapters, iteration=validation_round)
        
        if result == "OK":
            status_log.append("✅ Validation passed.")
            break
        elif result == "NOT OK":
            status_log.append("⚠️ Validation found issues, regenerating chapters...")
            chapters = generate_chapters(expanded_plot, num_chapters, feedback)
        else:
            status_log.append(f"❌ Validation error: {feedback}")
            break
    
    if validation_round >= MAX_VALIDATION_ATTEMPTS:
        status_log.append("⚠️ Max validation attempts reached. Returning latest chapters.")
    
    return expanded_plot, chapters, "\n".join(status_log)


# ----------- UI -----------
with gr.Blocks(title="BookKing - AI Story Planner") as demo:
    gr.Markdown("# BookKing - AI Story Planner\nAutomatically generate and validate a book structure from a single plot idea.")
    
    with gr.Row():
        plot_input = gr.Textbox(
            label="Short plot description",
            placeholder="Example: A young girl discovers a portal to an underwater world...",
            lines=3
        )
        chapters_input = gr.Number(
            label="Number of chapters",
            value=10,
            precision=0
        )
    
    generate_btn = gr.Button("Generate Outline")
    
    with gr.Row():
        expanded_output = gr.Textbox(label="Expanded Plot (Step 1)", lines=20)
        chapters_output = gr.Textbox(label="Chapters Overview (Step 2)", lines=20)
    
    status_output = gr.Textbox(label="Process Log (Step 3 Validation)", lines=10)
    
    generate_btn.click(
        fn=generate_book_outline,
        inputs=[plot_input, chapters_input],
        outputs=[expanded_output, chapters_output, status_output]
    )

demo.launch(server_name="0.0.0.0", server_port=7860)
