import gradio as gr
from state.settings_manager import settings_manager

def render_models_tab():
    with gr.Column():
        gr.Markdown("### Manage AI Models")
        
        # State to store list of models (names) for dropdowns
        model_names_state = gr.State([m["name"] for m in settings_manager.get_models()])
        
        with gr.Row():
            model_selector = gr.Dropdown(
                label="Select Model to Edit",
                choices=[m["name"] for m in settings_manager.get_models()],
                value=None,
                interactive=True
            )
            refresh_btn = gr.Button("🔄 Refresh List", size="sm")

        # --- Edit / Add Area ---
        with gr.Group():
            with gr.Row():
                name_input = gr.Textbox(label="Friendly Name", placeholder="My Custom Model")
                technical_name_input = gr.Textbox(label="Technical Name / ID", placeholder="gpt-4, phi-3, etc.")
            
            with gr.Row():
                type_selector = gr.Dropdown(
                    label="Type",
                    choices=["llm", "image"],
                    value="llm",
                    interactive=True
                )
                provider_selector = gr.Dropdown(
                    label="Provider",
                    choices=["LM Studio", "OpenAI"], # Initial choices for LLM
                    value="LM Studio",
                    interactive=True
                )
                
            model_url_input = gr.Textbox(label="Endpoint URL", value="http://127.0.0.1:1234")
            model_key_input = gr.Textbox(label="API Key", type="password")
            
            # Helper to update provider choices based on type
            def update_provider_choices(m_type):
                if m_type == "llm":
                    return gr.update(choices=["LM Studio", "OpenAI"], value="LM Studio")
                else:
                    return gr.update(choices=["Automatic1111", "OpenAI"], value="Automatic1111")
            
            type_selector.change(fn=update_provider_choices, inputs=[type_selector], outputs=[provider_selector])

            with gr.Row():
                add_btn = gr.Button("➕ Add New Model", variant="primary")
                save_btn = gr.Button("💾 Update Selected Model")
                delete_btn = gr.Button("🗑️ Delete Selected Model", variant="stop")

        model_status = gr.Markdown("")

        # --- Logic ---

        def load_model_details(model_name):
            if not model_name:
                return gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(visible=True)
            
            models = settings_manager.get_models()
            model = next((m for m in models if m["name"] == model_name), None)
            
            if not model:
                return gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(visible=True)
            
            is_default = model.get("is_default", False)
            delete_interactive = not is_default
            
            
            # Determine correct provider choices based on type
            m_type = model.get("type", "llm")
            provider_choices = ["LM Studio", "OpenAI"] if m_type == "llm" else ["Automatic1111", "OpenAI"]
            
            return (
                model.get("name", ""),
                model.get("technical_name", ""),
                m_type,
                gr.update(value=model.get("provider", "LM Studio"), choices=provider_choices),
                model.get("url", ""),
                model.get("api_key", ""),
                gr.update(interactive=delete_interactive)
            )

        model_selector.change(
            fn=load_model_details,
            inputs=[model_selector],
            outputs=[name_input, technical_name_input, type_selector, provider_selector, model_url_input, model_key_input, delete_btn]
        )

        def add_new_model(name, tech_name, m_type, provider, url, key):
            if not name:
                return "❌ Name is required.", gr.update()
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
                return f"✅ Model '{name}' added.", gr.update(choices=new_choices, value=name)
            except Exception as e:
                return f"❌ Error: {e}", gr.update()

        add_btn.click(
            fn=add_new_model,
            inputs=[name_input, technical_name_input, type_selector, provider_selector, model_url_input, model_key_input],
            outputs=[model_status, model_selector]
        )

        def update_model(original_name, name, tech_name, m_type, provider, url, key):
            if not original_name:
                return "❌ No model selected to update.", gr.update()
            try:
                # Keep is_default if it was default
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
                return f"✅ Model '{name}' updated.", gr.update(choices=new_choices, value=name)
            except Exception as e:
                return f"❌ Error: {e}", gr.update()

        save_btn.click(
            fn=update_model,
            inputs=[model_selector, name_input, technical_name_input, type_selector, provider_selector, model_url_input, model_key_input],
            outputs=[model_status, model_selector]
        )

        def delete_model(name):
            if not name:
                return "❌ No model selected.", gr.update(), gr.update()
            try:
                settings_manager.delete_model(name)
                new_choices = [m["name"] for m in settings_manager.get_models()]
                return f"✅ Model '{name}' deleted.", gr.update(choices=new_choices, value=None), gr.update(value="", placeholder="Deleted")
            except Exception as e:
                return f"❌ Error: {e}", gr.update(), gr.update()

        delete_btn.click(
            fn=delete_model,
            inputs=[model_selector],
            outputs=[model_status, model_selector, name_input]
        )
        
        def refresh_list():
            new_choices = [m["name"] for m in settings_manager.get_models()]
            return gr.update(choices=new_choices)
            
        refresh_btn.click(fn=refresh_list, inputs=None, outputs=[model_selector])
