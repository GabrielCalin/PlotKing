import gradio as gr
from ui.tabs.settings.models import render_models_tab
from ui.tabs.settings.tasks import render_tasks_tab
from state.settings_manager import settings_manager
from utils.timestamp import ts_prefix

def render_settings_tab():
    with gr.Blocks() as settings_block:
        with gr.Row():
            with gr.Column(scale=2):
                with gr.Tabs():
                    with gr.Tab("🤖 Models"):
                        render_models_tab()
                    with gr.Tab("📋 Tasks"):
                        refresh_tasks_fn, task_dropdowns = render_tasks_tab()
            
            with gr.Column(scale=1):
                gr.Markdown("### Process Log")
                process_log = gr.Textbox(label="Log", lines=20, interactive=False)
        
        with gr.Row():
            save_all_btn = gr.Button("💾 Save All Settings", variant="primary", scale=1)
            status_msg = gr.Markdown("")

        def save_all_settings():
            try:
                settings_manager.save_settings()
                return "\n" + ts_prefix("✅ Settings saved successfully to disk.")
            except Exception as e:
                return "\n" + ts_prefix(f"❌ Error saving settings: {e}")

        # Note: We need to append to log, but for now we just show the message. 
        # Real process log usually accumulates. 
        # Let's make it accumulate.
        
        def save_and_log(current_log):
            msg = save_all_settings()
            return (current_log or "") + msg

        save_all_btn.click(
            fn=save_and_log,
            inputs=[process_log],
            outputs=[process_log]
        )

    # Return refresh utils so interface can bind global load events if needed
    return refresh_tasks_fn, task_dropdowns

