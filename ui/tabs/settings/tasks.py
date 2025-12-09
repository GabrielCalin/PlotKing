import gradio as gr
from state.settings_manager import settings_manager

def render_tasks_tab():
    with gr.Column():
        gr.Markdown("### Assign Models to Tasks")
        
        # We need a dynamic list of rows, one for each task
        # Gradio doesn't support dynamic creation of components easily after launch without @gr.render
        # But we know the task list is fixed (hardcoded in settings_manager).
        
        tasks_dict = settings_manager.get_tasks()
        
        # Sort tasks: LLM first, then Image
        # We can detect type by checking if it defaults to default_llm or default_image or just by name from manager lists
        
        # Re-import lists to separate them
        from state.settings_manager import LLM_TASKS, IMAGE_TASKS
        
        model_choices = [m["name"] for m in settings_manager.get_models()]
        
        # Use a dictionary to store the dropdown components so we can gather values later if needed
        # But actually, simpler is to have a Save/Sync button that reads all? 
        # Or Just have immediate update? 
        # Requirement: "Va exista si un buton de Save pentru salvarea setarilor, comun tuturor tab-urilor."
        # So we just need to keep `settings_manager` state updated in memory when these change.
        
        # Important: `settings_manager.settings` acts as the in-memory state.
        # But `settings_manager.tasks` is a dict.
        
        # We will create a loop.
        
        llm_dropdowns = []
        image_dropdowns = []
        
        refresh_btn = gr.Button("🔄 Refresh Choices", size="sm")

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
                    
                    def update_task_assignment(val, t_name=task):
                        settings_manager.settings["tasks"][t_name] = val
                    
                    dd.change(fn=update_task_assignment, inputs=[dd])
                
        gr.Markdown("#### Image Tasks")
        with gr.Group():
            for task in IMAGE_TASKS:
                with gr.Row():
                    t_label = gr.Markdown(f"**{task}**")
                    
                    image_models = [m["name"] for m in settings_manager.get_models() if m.get("type") == "image"]
                    current_val = tasks_dict.get(task)
                    
                    dd = gr.Dropdown(choices=image_models, value=current_val, label=f"Model for {task}", show_label=False)
                    image_dropdowns.append((task, dd))
                    
                    def update_task_assignment(val, t_name=task):
                        settings_manager.settings["tasks"][t_name] = val
                    
                    dd.change(fn=update_task_assignment, inputs=[dd])

        # Refresh Logic
        def refresh_choices():
            # Reload settings to ensure fresh state
            # settings_manager.settings = settings_manager.load_settings() # Optional: Force reload from disk?
            # Or just assume memory is updated if Models tab updated it? 
            # Models tab updates `settings_manager` in memory.
            
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


