# -*- coding: utf-8 -*-
# ui/interface.py — layout principal (header + tabs)

import gradio as gr
from ui import load_css
from ui.tabs.create_tab import render_create_tab
from ui.tabs.editor_tab import render_editor_tab
from ui.tabs.export_tab import render_export_tab
from ui.tabs.settings_tab import render_settings_tab
from handlers.create.create_handlers import list_projects


def create_interface():
    with gr.Blocks(title="PlotKing - AI Story Builder", css=load_css("style.css", "editor.css", "export.css")) as demo:
        # === Header aplicație (în afara tab-urilor) ===
        with gr.Row(elem_id="bk-header"):
            gr.HTML("<div id='bk-title'>📖 PlotKing – AI Story Builder</div>")
            current_project_label = gr.HTML("<div id='bk-project'>(No project loaded)</div>")

        # Două state-uri separate pentru sincronizare bidirecțională:
        # - editor_sections_epoch: Create → Editor (când Create modifică ceva, notifică Editor)
        # - create_sections_epoch: Editor → Create (când Editor modifică ceva, notifică Create)
        editor_sections_epoch = gr.State(0)
        create_sections_epoch = gr.State(0)

        # === Tabs ===
        with gr.Tabs():
            with gr.Tab("🪶 Create"):
                # returnăm project_dropdown ca să-l putem popula la load
                project_dropdown = render_create_tab(
                    current_project_label,
                    editor_sections_epoch=editor_sections_epoch,
                    create_sections_epoch=create_sections_epoch
                )

            with gr.Tab("✏️ Edit"):
                render_editor_tab(
                    editor_sections_epoch=editor_sections_epoch,
                    create_sections_epoch=create_sections_epoch
                )

            with gr.Tab("📤 Export"):
                render_export_tab(
                    editor_sections_epoch=editor_sections_epoch,
                    create_sections_epoch=create_sections_epoch
                )

            with gr.Tab("⚙️ Settings"):
                refresh_tasks_fn, task_dropdowns, refresh_models_fn, model_selector_comp, load_model_details_fn, model_input_components = render_settings_tab()

        # === Populate project list on startup ===
        demo.load(
            fn=lambda: (
                gr.update(
                    choices=list_projects(),
                    value=(list_projects()[0] if list_projects() else None)
                )
            ),
            inputs=None,
            outputs=[project_dropdown],
        )

        # === Refresh Settings Task Dropdowns on startup ===
        # This ensures that even if models were added in previous session, the Tasks tab sees them immediately.
        demo.load(
            fn=refresh_tasks_fn,
            inputs=None,
            outputs=task_dropdowns
        )
        # === Refresh Settings Model Dropdown on startup ===
        demo.load(
            fn=refresh_models_fn,
            inputs=None,
            outputs=[model_selector_comp]
        ).then(
            fn=load_model_details_fn,
            inputs=[model_selector_comp],
            outputs=model_input_components
        )

    return demo
