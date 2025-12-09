import gradio as gr
from state.settings_manager import settings_manager, DEFAULT_LLM_MODEL, LLM_PROVIDERS, IMAGE_PROVIDERS
from utils.timestamp import ts_prefix

def render_models_tab(process_log):
    with gr.Column():
        gr.Markdown("### Manage AI Models")
        
        models_list = settings_manager.get_models()
        model_names = [m["name"] for m in models_list]
        
        default_model_name = DEFAULT_LLM_MODEL["name"]
        default_val = default_model_name if default_model_name in model_names else (model_names[0] if model_names else None)

        def get_model_data(model_name):
            if not model_name:
                # Return empty defaults
                return "", "", "llm", LLM_PROVIDERS[0], "", "", True, False, False, LLM_PROVIDERS
                
            model = next((m for m in settings_manager.get_models() if m["name"] == model_name), None)
            if not model:
                 # Fallback to default structure if not found (shouldn't happen for valid names)
                 model = DEFAULT_LLM_MODEL.copy()
            
            name = model.get("name", "")
            tech_name = model.get("technical_name", "")
            m_type = model.get("type", "llm")
            provider = model.get("provider", LLM_PROVIDERS[0])
            url = model.get("url", "")
            key = model.get("api_key", "")
            
            is_default = model.get("is_default", False)
            delete_interactive = not is_default
            
            provider_choices = LLM_PROVIDERS if m_type == "llm" else IMAGE_PROVIDERS
            
            caps = settings_manager.get_provider_capabilities(provider)
            url_vis = caps.get("has_url", True)
            key_vis = caps.get("has_api_key", False)
            
            return name, tech_name, m_type, provider, url, key, url_vis, key_vis, delete_interactive, provider_choices

        # Initialization using the helper
        (
            initial_name, initial_tech_name, initial_type, initial_provider, 
            initial_url, initial_key, initial_url_vis, initial_key_vis, 
            _, curr_provider_choices
        ) = get_model_data(default_val)

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
                    return gr.update(choices=LLM_PROVIDERS, value=LLM_PROVIDERS[0])
                else:
                    return gr.update(choices=IMAGE_PROVIDERS, value=IMAGE_PROVIDERS[0])
            
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
            (
                name, tech, mtype, prov, url, key, url_v, key_v, del_int, p_choices
            ) = get_model_data(model_name)
            
            return (
                name,
                tech,
                mtype,
                gr.update(value=prov, choices=p_choices),
                gr.update(value=url, visible=url_v),
                gr.update(value=key, visible=key_v),
                gr.update(interactive=del_int)
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

        add_evt = add_btn.click(
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

        save_evt = save_btn.click(
            fn=update_model,
            inputs=[model_selector, name_input, technical_name_input, type_selector, provider_selector, model_url_input, model_key_input, process_log],
            outputs=[process_log, model_selector]
        )

        def delete_model(name, current_log):
            if not name:
                return (
                    (current_log or "") + "\n" + ts_prefix("❌ No model selected."), 
                    gr.update(), gr.update(), gr.update(), gr.update(), 
                    gr.update(), gr.update(), gr.update(), gr.update()
                )
            try:
                settings_manager.delete_model(name)
                
                # Switch to default
                fallback_name = DEFAULT_LLM_MODEL["name"]
                new_choices = [m["name"] for m in settings_manager.get_models()]
                
                log_msg = (current_log or "") + "\n" + ts_prefix(f"✅ Model '{name}' deleted.")
                
                # Get details for fallback model to repopulate the form
                (
                    f_name, f_tech, f_type, f_provider, f_url, f_key, f_url_vis, f_key_vis, f_del_int, f_choices
                ) = get_model_data(fallback_name)
                
                return (
                    log_msg, 
                    gr.update(choices=new_choices, value=fallback_name), 
                    f_name, 
                    f_tech, 
                    f_type, 
                    gr.update(value=f_provider, choices=f_choices),
                    gr.update(value=f_url, visible=f_url_vis),
                    gr.update(value=f_key, visible=f_key_vis), 
                    gr.update(interactive=f_del_int)
                )

            except Exception as e:
                return (
                    (current_log or "") + "\n" + ts_prefix(f"❌ Error: {e}"), 
                    gr.update(), gr.update(), gr.update(), gr.update(), 
                    gr.update(), gr.update(), gr.update(), gr.update()
                )

        del_evt = delete_btn.click(
            fn=delete_model,
            inputs=[model_selector, process_log],
            outputs=[process_log, model_selector, name_input, technical_name_input, type_selector, provider_selector, model_url_input, model_key_input, delete_btn]
        )

        def refresh_models_list():
            models = settings_manager.get_models()
            names = [m["name"] for m in models]
            # Keep current value if valid, else default
            return gr.update(choices=names)

        return refresh_models_list, model_selector, add_evt, save_evt, del_evt
