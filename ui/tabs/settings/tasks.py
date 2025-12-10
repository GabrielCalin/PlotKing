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
                with gr.Row():
                    t_label = gr.Markdown(f"**{task}**")
                    
                    llm_models = [m["name"] for m in settings_manager.get_models() if m.get("type") == "llm"]
                    
                    current_val = tasks_dict.get(task)
                    if current_val not in llm_models and current_val is not None:
                         if current_val: llm_models.append(current_val)
                    
                    dd = gr.Dropdown(choices=llm_models, value=current_val, label=f"Model for {task}", show_label=False)
                    llm_dropdowns.append((task, dd))
                    
                    def update_task_assignment(val, current_log, t_name=task):
                        settings_manager.settings["tasks"][t_name] = val
                        settings_manager.save_settings()
                        return append_log_string(current_log, ts_prefix(f"✅ Task '{t_name}' assigned to '{val}'."))
                    
                    dd.change(fn=update_task_assignment, inputs=[dd, process_log], outputs=[process_log])
                
        gr.Markdown("#### Image Tasks")
        with gr.Group():
            for task in IMAGE_TASKS:
                with gr.Row():
                    t_label = gr.Markdown(f"**{task}**")
                    
                    image_models = [m["name"] for m in settings_manager.get_models() if m.get("type") == "image"]
                    current_val = tasks_dict.get(task)
                    
                    dd = gr.Dropdown(choices=image_models, value=current_val, label=f"Model for {task}", show_label=False)
                    image_dropdowns.append((task, dd))
                    
                    def update_task_assignment(val, current_log, t_name=task):
                        settings_manager.settings["tasks"][t_name] = val
                        settings_manager.save_settings()
                        return append_log_string(current_log, ts_prefix(f"✅ Task '{t_name}' assigned to '{val}'."))
                    
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
