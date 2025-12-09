import gradio as gr
from state.settings_manager import settings_manager, DEFAULT_LLM_MODEL
from utils.timestamp import ts_prefix

def render_models_tab(process_log):
    with gr.Column():
        gr.Markdown("### Manage AI Models")
        
        models_list = settings_manager.get_models()
        model_names = [m["name"] for m in models_list]
        
        # Use DEFAULT_LLM_MODEL constant for the default if present, otherwise fallback
        default_model_name = DEFAULT_LLM_MODEL["name"]
        default_val = default_model_name if default_model_name in model_names else (model_names[0] if model_names else None)

        # Simplified initialization - default_llm always exists per requirements
        m = next((m for m in models_list if m["name"] == default_val), None)
        # Fallback just in case
        if not m: m = DEFAULT_LLM_MODEL.copy()
        
        initial_name = m.get("name", "")
        initial_tech_name = m.get("technical_name", "")
        initial_type = m.get("type", "llm")
        initial_provider = m.get("provider", "LM Studio")
        initial_url = m.get("url", "")
        initial_key = m.get("api_key", "")
        
        curr_provider_choices = ["LM Studio", "OpenAI"] if initial_type == "llm" else ["Automatic1111", "OpenAI"]

        # Initial Visibility
        caps = settings_manager.get_provider_capabilities(initial_provider)
        initial_url_vis = caps.get("has_url", True)
        initial_key_vis = caps.get("has_api_key", False)

        with gr.Row():
            model_selector = gr.Dropdown(
                label="Select Model to Edit",
                choices=model_names,
                value=default_val,
                interactive=True
            )

        # --- Edit / Add Area ---
        with gr.Group():
            with gr.Row():
                name_input = gr.Textbox(label="Friendly Name", placeholder="My Custom Model", value=initial_name)
                technical_name_input = gr.Textbox(label="Technical Name / ID", placeholder="gpt-4, phi-3, etc.", value=initial_tech_name)
            
            with gr.Row():
                type_selector = gr.Dropdown(
                    label="Type",
                    choices=["llm", "image"],
                    value=initial_type,
                    interactive=True
                )
                provider_selector = gr.Dropdown(
                    label="Provider",
                    choices=curr_provider_choices,
                    value=initial_provider,
                    interactive=True
                )
                
            model_url_input = gr.Textbox(label="Endpoint URL", value=initial_url, visible=initial_url_vis)
            model_key_input = gr.Textbox(label="API Key", type="password", visible=initial_key_vis, value=initial_key)
            
            # Helper to update provider choices based on type
            # Use .input() instead of .change() to avoid triggering when loading details programmatically
            def update_provider_choices(m_type):
                if m_type == "llm":
                    return gr.update(choices=["LM Studio", "OpenAI"], value="LM Studio")
                else:
                    return gr.update(choices=["Automatic1111", "OpenAI"], value="Automatic1111")
            
            type_selector.input(fn=update_provider_choices, inputs=[type_selector], outputs=[provider_selector])

            # Helper for visibility based on provider
            def update_visibility(provider):
                caps = settings_manager.get_provider_capabilities(provider)
                return gr.update(visible=caps.get("has_url", True)), gr.update(visible=caps.get("has_api_key", False))

            provider_selector.change(fn=update_visibility, inputs=[provider_selector], outputs=[model_url_input, model_key_input])

            with gr.Row():
                add_btn = gr.Button("➕ Add New Model", variant="primary")
                save_btn = gr.Button("💾 Update Selected Model")
                delete_btn = gr.Button("🗑️ Delete Selected Model", variant="stop")

        # --- Logic ---

        def load_model_details(model_name):
            if not model_name:
                return (
                    gr.update(), gr.update(), gr.update(), gr.update(), 
                    gr.update(), gr.update(), gr.update(interactive=False)
                )
            
            models = settings_manager.get_models()
            model = next((m for m in models if m["name"] == model_name), None)
            
            if not model:
                return (
                    gr.update(), gr.update(), gr.update(), gr.update(), 
                    gr.update(), gr.update(), gr.update(interactive=False)
                )
            
            is_default = model.get("is_default", False)
            delete_interactive = not is_default
            
            m_type = model.get("type", "llm")
            provider = model.get("provider", "LM Studio")
            provider_choices = ["LM Studio", "OpenAI"] if m_type == "llm" else ["Automatic1111", "OpenAI"]
            
            # Visibility checks
            caps = settings_manager.get_provider_capabilities(provider)
            url_vis = caps.get("has_url", True)
            key_vis = caps.get("has_api_key", False)

            return (
                model.get("name", ""),
                model.get("technical_name", ""),
                m_type,
                gr.update(value=provider, choices=provider_choices),
                gr.update(value=model.get("url", ""), visible=url_vis),
                gr.update(value=model.get("api_key", ""), visible=key_vis),
                gr.update(interactive=delete_interactive)
            )

        model_selector.change(
            fn=load_model_details,
            inputs=[model_selector],
            outputs=[name_input, technical_name_input, type_selector, provider_selector, model_url_input, model_key_input, delete_btn]
        )

        def add_new_model(name, tech_name, m_type, provider, url, key, current_log):
            if not name:
                return (current_log or "") + "\n" + ts_prefix("❌ Name is required."), gr.update()
            try:
                new_model = {
                    "name": name,
                    "technical_name": tech_name,
                    "type": m_type,
                    "provider": provider,
                    "url": url,
                    "api_key": key,
                    "is_default": False
                }
                settings_manager.add_model(new_model)
                new_choices = [m["name"] for m in settings_manager.get_models()]
                log_msg = (current_log or "") + "\n" + ts_prefix(f"✅ Model '{name}' added.")
                return log_msg, gr.update(choices=new_choices, value=name)
            except Exception as e:
                return (current_log or "") + "\n" + ts_prefix(f"❌ Error: {e}"), gr.update()

        add_btn.click(
            fn=add_new_model,
            inputs=[name_input, technical_name_input, type_selector, provider_selector, model_url_input, model_key_input, process_log],
            outputs=[process_log, model_selector]
        )

        def update_model(original_name, name, tech_name, m_type, provider, url, key, current_log):
            if not original_name:
                return (current_log or "") + "\n" + ts_prefix("❌ No model selected to update."), gr.update()
            try:
                models = settings_manager.get_models()
                existing = next((m for m in models if m["name"] == original_name), None)
                is_default = existing.get("is_default", False) if existing else False

                updated_model = {
                    "name": name,
                    "technical_name": tech_name,
                    "type": m_type,
                    "provider": provider,
                    "url": url,
                    "api_key": key,
                    "is_default": is_default
                }
                settings_manager.update_model(original_name, updated_model)
                new_choices = [m["name"] for m in settings_manager.get_models()]
                log_msg = (current_log or "") + "\n" + ts_prefix(f"✅ Model '{name}' updated.")
                return log_msg, gr.update(choices=new_choices, value=name)
            except Exception as e:
                return (current_log or "") + "\n" + ts_prefix(f"❌ Error: {e}"), gr.update()

        save_btn.click(
            fn=update_model,
            inputs=[model_selector, name_input, technical_name_input, type_selector, provider_selector, model_url_input, model_key_input, process_log],
            outputs=[process_log, model_selector]
        )

        def delete_model(name, current_log):
            if not name:
                return (current_log or "") + "\n" + ts_prefix("❌ No model selected."), gr.update(), gr.update()
            try:
                settings_manager.delete_model(name)
                new_choices = [m["name"] for m in settings_manager.get_models()]
                log_msg = (current_log or "") + "\n" + ts_prefix(f"✅ Model '{name}' deleted.")
                return log_msg, gr.update(choices=new_choices, value=None), gr.update(value="", placeholder="Deleted")
            except Exception as e:
                return (current_log or "") + "\n" + ts_prefix(f"❌ Error: {e}"), gr.update(), gr.update()

        delete_btn.click(
            fn=delete_model,
            inputs=[model_selector, process_log],
            outputs=[process_log, model_selector, name_input]
        )

        return add_btn, save_btn, delete_btn
