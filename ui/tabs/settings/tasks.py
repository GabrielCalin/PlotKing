import gradio as gr
from state.settings_manager import settings_manager
from utils.timestamp import ts_prefix
from utils.logger import append_log_string

def render_tasks_tab(process_log):
    with gr.Column():
        gr.Markdown("### Assign Models to Tasks")
        
        # We need a dynamic list of rows, one for each task
        tasks_dict = settings_manager.get_tasks()
        
        from state.settings_manager import LLM_TASKS, IMAGE_TASKS
        
        # We will create a loop.
        llm_dropdowns = []
        image_dropdowns = []

        gr.Markdown("#### LLM Tasks")
        with gr.Group():
            for task in LLM_TASKS:
                tech_name = task["technical_name"]
                display_name = task["display_name"]
                with gr.Row(elem_classes=["task-row"]):
                    t_label = gr.HTML(f"<p style='display: flex; align-items: center; height: 100%; margin: 0;'><strong>{display_name}</strong></p>")
                    
                    llm_models = [m["name"] for m in settings_manager.get_models() if m.get("type") == "llm"]
                    
                    current_val = tasks_dict.get(tech_name)
                    if current_val not in llm_models and current_val is not None:
                         if current_val: llm_models.append(current_val)
                    
                    dd = gr.Dropdown(choices=llm_models, value=current_val, label=f"Model for {display_name}", show_label=False)
                    llm_dropdowns.append((tech_name, dd))
                    
                    def update_task_assignment(val, current_log, t_name=tech_name, d_name=display_name):
                        settings_manager.settings["tasks"][t_name] = val
                        settings_manager.save_settings()
                        return append_log_string(current_log, ts_prefix(f"✅ Task '{d_name}' assigned to '{val}'."))
                    
                    dd.change(fn=update_task_assignment, inputs=[dd, process_log], outputs=[process_log])
                
        gr.Markdown("#### Image Tasks")
        with gr.Group():
            for task in IMAGE_TASKS:
                tech_name = task["technical_name"]
                display_name = task["display_name"]
                with gr.Row(elem_classes=["task-row"]):
                    t_label = gr.HTML(f"<p style='display: flex; align-items: center; height: 100%; margin: 0;'><strong>{display_name}</strong></p>")
                    
                    image_models = [m["name"] for m in settings_manager.get_models() if m.get("type") == "image"]
                    current_val = tasks_dict.get(tech_name)
                    
                    dd = gr.Dropdown(choices=image_models, value=current_val, label=f"Model for {display_name}", show_label=False)
                    image_dropdowns.append((tech_name, dd))
                    
                    def update_task_assignment(val, current_log, t_name=tech_name, d_name=display_name):
                        settings_manager.settings["tasks"][t_name] = val
                        settings_manager.save_settings()
                        return append_log_string(current_log, ts_prefix(f"✅ Task '{d_name}' assigned to '{val}'."))
                    
                    dd.change(fn=update_task_assignment, inputs=[dd, process_log], outputs=[process_log])

        # Refresh Logic
        def refresh_choices():
            new_llm_models = [m["name"] for m in settings_manager.get_models() if m.get("type") == "llm"]
            new_img_models = [m["name"] for m in settings_manager.get_models() if m.get("type") == "image"]
            
            updates = []
            
            # For LLM tasks
            current_tasks = settings_manager.get_tasks()
            
            for task, _ in llm_dropdowns:
                curr = current_tasks.get(task)
                updates.append(gr.update(choices=new_llm_models, value=curr))
                
            for task, _ in image_dropdowns:
                curr = current_tasks.get(task)
                updates.append(gr.update(choices=new_img_models, value=curr))
                
            return updates

        # Expose components for external refresh
        all_dropdowns = [dd for _, dd in llm_dropdowns] + [dd for _, dd in image_dropdowns]
        
        return refresh_choices, all_dropdowns
