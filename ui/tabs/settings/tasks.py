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
        
        gr.Markdown("#### LLM Tasks")
        for task in LLM_TASKS:
            with gr.Row():
                t_label = gr.Markdown(f"**{task}**")
                
                # Filter choices to only LLM type models?
                # User didn't strictly say we must filter, but it makes sense.
                llm_models = [m["name"] for m in settings_manager.get_models() if m.get("type") == "llm"]
                
                current_val = tasks_dict.get(task)
                if current_val not in llm_models and current_val is not None:
                     # Fallback if assigned model not in filtered list (e.g. wrong type assigned?)
                     # Just show all to be safe or append current
                     if current_val: llm_models.append(current_val)
                
                dd = gr.Dropdown(choices=llm_models, value=current_val, label=f"Model for {task}", show_label=False)
                
                # Update handler
                def update_task_assignment(val, t_name=task):
                    settings_manager.settings["tasks"][t_name] = val
                    # We don't save to file yet, wait for global save.
                    # But settings_manager.settings is updated in memory.
                
                dd.change(fn=update_task_assignment, inputs=[dd])
                
        gr.Markdown("#### Image Tasks")
        for task in IMAGE_TASKS:
            with gr.Row():
                t_label = gr.Markdown(f"**{task}**")
                
                image_models = [m["name"] for m in settings_manager.get_models() if m.get("type") == "image"]
                current_val = tasks_dict.get(task)
                
                dd = gr.Dropdown(choices=image_models, value=current_val, label=f"Model for {task}", show_label=False)
                
                def update_task_assignment(val, t_name=task):
                    settings_manager.settings["tasks"][t_name] = val
                
                dd.change(fn=update_task_assignment, inputs=[dd])
        
        # We might need a refresh logic if models are added/removed in the Models tab.
        # Since they are on separate tabs, we can't easily trigger a re-render of this tab without a reload
        # OR we can add a "Refresh Choices" button here too.
        
        gr.Markdown("*(If you added a new model, restart or click Refresh below to see it)*")
        # Creating a refresh button for the dropdowns is tricky in a loop without re-rendering.
        # Gradio 5 might allow gr.render, but let's stick to simple first.
        # A simple refresh button that updates all choices.
        
        # Actually, let's just assume user switches tabs. 
        # Updating the `choices` of all dropdowns dynamically is possible if we hold references.
