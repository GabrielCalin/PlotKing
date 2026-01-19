import gradio as gr
from ui.tabs.settings.models import render_models_tab
from ui.tabs.settings.tasks import render_tasks_tab
from state.settings_manager import settings_manager
from utils.timestamp import ts_prefix

def render_settings_tab():
    with gr.Blocks() as settings_block:
        # Define process_log first so it can be passed to functions. render=False prevents it from showing up here.
        process_log = gr.Textbox(label="Log", lines=20, interactive=False, render=False)

        with gr.Row():
            with gr.Column(scale=2):
                with gr.Tabs():
                    with gr.Tab("🤖 Models"):
                        refresh_models_fn, model_selector_comp, save_evt, del_evt, load_model_details_fn, model_input_components = render_models_tab(process_log)
                    with gr.Tab("📋 Tasks"):
                        refresh_tasks_fn, task_outputs = render_tasks_tab(process_log)
            
            # Wire up auto-refresh for tasks when models change - using .then() on events returned from models.py
            # This ensures they run AFTER the save/delete logic completes
            save_evt.then(fn=refresh_tasks_fn, inputs=[], outputs=task_outputs)
            del_evt.then(fn=refresh_tasks_fn, inputs=[], outputs=task_outputs)
            
            with gr.Column(scale=1):
                gr.Markdown("### Process Log")
                # Render the log where we want it in the layout
                process_log.render()

    # Return refresh utils so interface can bind global load events if needed
    return refresh_tasks_fn, task_outputs, refresh_models_fn, model_selector_comp, load_model_details_fn, model_input_components
