import gradio as gr
from state.settings_manager import settings_manager, LLM_TASKS
from handlers.settings import (
    REASONING_EFFORT_OPTIONS,
    get_task_defaults,
    IMAGE_TASKS
)
from handlers.settings.tasks_handlers import (
    create_model_change_handler,
    create_save_handler,
    create_reset_handler,
    create_image_task_handler
)


def render_tasks_tab(process_log):
    with gr.Column():
        gr.Markdown("### Assign Models to Tasks")
        
        llm_task_components = []
        image_dropdowns = []

        gr.Markdown("#### LLM Tasks")
        with gr.Group():
            for task in LLM_TASKS:
                tech_name = task["technical_name"]
                display_name = task["display_name"]
                
                task_settings = settings_manager.get_task_settings(tech_name)
                current_model = task_settings.get("model", "default_llm") if task_settings else "default_llm"
                defaults = get_task_defaults(tech_name)
                
                with gr.Column(elem_classes=["task-group"]):
                    with gr.Row(elem_classes=["task-row"]):
                        t_label = gr.HTML(
                            f"<p style='display: flex; align-items: center; height: 100%; margin: 0;'>"
                            f"<strong>{display_name}</strong></p>"
                        )
                        
                        llm_models = [m.name for m in settings_manager.get_models() if m.type == "llm"]
                        if current_model not in llm_models:
                            llm_models.append(current_model)
                        
                        model_dd = gr.Dropdown(
                            choices=llm_models,
                            value=current_model,
                            label=f"Model for {display_name}",
                            show_label=False
                        )
                    
                    with gr.Accordion("⚙️ Parameters", open=False):
                        with gr.Row():
                            max_tokens_input = gr.Number(
                                label="Max Tokens",
                                value=task_settings.get("max_tokens", defaults.max_tokens if defaults else 4000),
                                precision=0,
                                minimum=1
                            )
                            temperature_input = gr.Number(
                                label="Temperature",
                                value=task_settings.get("temperature", defaults.temperature if defaults else 0.7),
                                minimum=0.0,
                                maximum=2.0
                            )
                            top_p_input = gr.Number(
                                label="Top-P",
                                value=task_settings.get("top_p", defaults.top_p if defaults else 0.95),
                                minimum=0.0,
                                maximum=1.0
                            )
                        
                        with gr.Row():
                            retries_input = gr.Number(
                                label="Retries",
                                value=task_settings.get("retries", defaults.retries if defaults else 3),
                                precision=0,
                                minimum=0,
                                maximum=10
                            )
                            timeout_input = gr.Number(
                                label="Timeout (seconds)",
                                value=task_settings.get("timeout", defaults.timeout if defaults else 300),
                                precision=0,
                                minimum=1
                            )
                        
                        model_config = settings_manager.get_model_for_task(tech_name)
                        has_reasoning = model_config.reasoning if model_config else False
                        
                        with gr.Column(visible=has_reasoning) as reasoning_section:
                            gr.Markdown("**Reasoning Parameters**")
                            with gr.Row():
                                current_effort = task_settings.get("reasoning_effort")
                                effort_value = current_effort if current_effort in REASONING_EFFORT_OPTIONS else "Not Set"
                                
                                reasoning_effort_dd = gr.Dropdown(
                                    label="Reasoning Effort",
                                    choices=REASONING_EFFORT_OPTIONS,
                                    value=effort_value
                                )
                                
                                current_max_reasoning = task_settings.get("max_reasoning_tokens")
                                max_reasoning_input = gr.Number(
                                    label="Max Reasoning Tokens (empty = Not Set)",
                                    value=current_max_reasoning,
                                    precision=0,
                                    minimum=0
                                )
                        
                        with gr.Row():
                            save_btn = gr.Button("💾 Save Parameters", variant="primary", size="sm")
                            reset_btn = gr.Button("🔄 Reset Defaults", variant="secondary", size="sm")
                
                llm_task_components.append({
                    "tech_name": tech_name,
                    "display_name": display_name,
                    "model_dd": model_dd,
                    "max_tokens": max_tokens_input,
                    "timeout": timeout_input,
                    "temperature": temperature_input,
                    "top_p": top_p_input,
                    "retries": retries_input,
                    "reasoning_section": reasoning_section,
                    "reasoning_effort": reasoning_effort_dd,
                    "max_reasoning_tokens": max_reasoning_input,
                    "save_btn": save_btn,
                    "reset_btn": reset_btn
                })
                
                handler = create_model_change_handler(tech_name, display_name)
                model_dd.change(
                    fn=handler,
                    inputs=[
                        model_dd, max_tokens_input, timeout_input, temperature_input,
                        top_p_input, retries_input, reasoning_effort_dd, max_reasoning_input, process_log
                    ],
                    outputs=[reasoning_section, process_log]
                )
                
                save_handler = create_save_handler(tech_name, display_name)
                save_btn.click(
                    fn=save_handler,
                    inputs=[
                        model_dd, max_tokens_input, timeout_input, temperature_input,
                        top_p_input, retries_input, reasoning_effort_dd, max_reasoning_input, process_log
                    ],
                    outputs=[process_log]
                )
                
                reset_handler = create_reset_handler(tech_name, display_name)
                reset_btn.click(
                    fn=reset_handler,
                    inputs=[process_log],
                    outputs=[
                        max_tokens_input, timeout_input, temperature_input,
                        top_p_input, retries_input, reasoning_effort_dd,
                        max_reasoning_input, reasoning_section, process_log
                    ]
                )

        gr.Markdown("#### Image Tasks")
        with gr.Group():
            for task in IMAGE_TASKS:
                tech_name = task["technical_name"]
                display_name = task["display_name"]
                with gr.Column(elem_classes=["task-group"]):
                    with gr.Row(elem_classes=["task-row", "task-row-simple"]):
                        t_label = gr.HTML(
                            f"<p style='display: flex; align-items: center; height: 100%; margin: 0;'>"
                            f"<strong>{display_name}</strong></p>"
                        )
                        
                        image_models = [m.name for m in settings_manager.get_models() if m.type == "image"]
                        task_data = settings_manager.settings["tasks"].get(tech_name)
                        if isinstance(task_data, dict):
                            current_val = task_data.get("model", "default_image")
                        else:
                            current_val = "default_image"
                        
                        dd = gr.Dropdown(
                            choices=image_models,
                            value=current_val,
                            label=f"Model for {display_name}",
                            show_label=False
                        )
                        image_dropdowns.append((tech_name, dd))
                        
                        dd.change(
                            fn=create_image_task_handler(tech_name, display_name),
                            inputs=[dd, process_log],
                            outputs=[process_log]
                        )

        def refresh_choices():
            new_llm_models = [m.name for m in settings_manager.get_models() if m.type == "llm"]
            new_img_models = [m.name for m in settings_manager.get_models() if m.type == "image"]
            
            updates = []
            current_tasks = settings_manager.get_tasks()
            
            for comp in llm_task_components:
                task_data = current_tasks.get(comp["tech_name"])
                curr_model = task_data.get("model") if isinstance(task_data, dict) else task_data
                updates.append(gr.update(choices=new_llm_models, value=curr_model))
                
                model_config = settings_manager.get_model_for_task(comp["tech_name"])
                has_reasoning = model_config.reasoning if model_config else False
                updates.append(gr.update(visible=has_reasoning))
                
            for task_name, _ in image_dropdowns:
                curr = current_tasks.get(task_name)
                if isinstance(curr, dict):
                    curr_model = curr.get("model", "default_image")
                else:
                    curr_model = curr if curr else "default_image"
                updates.append(gr.update(choices=new_img_models, value=curr_model))
            
            return updates

        all_dropdowns = [comp["model_dd"] for comp in llm_task_components] + [dd for _, dd in image_dropdowns]
        all_reasoning_sections = [comp["reasoning_section"] for comp in llm_task_components]
        all_outputs = []
        
        for comp in llm_task_components:
            all_outputs.append(comp["model_dd"])
            all_outputs.append(comp["reasoning_section"])
        all_outputs.extend([dd for _, dd in image_dropdowns])
        
        return refresh_choices, all_outputs
