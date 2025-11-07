# -*- coding: utf-8 -*-
# ui/interface.py — layout principal (header + tabs)

import gradio as gr
from ui import load_css
from ui.tabs.create_tab import render_create_tab
from ui.tabs.editor_tab import render_editor_tab
import ui.handlers as H  # <-- necesar pentru list_projects() în demo.load()


def create_interface(pipeline_fn, refine_fn):
    with gr.Blocks(title="BookKing - AI Story Builder", css=load_css("style.css", "editor.css")) as demo:
        # === Header aplicație (în afara tab-urilor) ===
        with gr.Row(elem_id="bk-header"):
            gr.HTML("<div id='bk-title'>📖 BookKing – AI Story Builder</div>")
            current_project_label = gr.HTML("<div id='bk-project'>(No project loaded)</div>")

        sections_epoch = gr.State(0)

        # === Tabs ===
        with gr.Tabs():
            with gr.Tab("🪶 Create"):
                # returnăm project_dropdown ca să-l putem popula la load
                project_dropdown = render_create_tab(pipeline_fn, refine_fn, current_project_label, sections_epoch=sections_epoch)

            with gr.Tab("✏️ Editor"):
                render_editor_tab(sections_epoch=sections_epoch)

        # === Populate project list on startup ===
        demo.load(
            fn=lambda: (
                gr.update(
                    choices=H.list_projects(),
                    value=(H.list_projects()[0] if H.list_projects() else None)
                )
            ),
            inputs=None,
            outputs=[project_dropdown],
        )

    return demo
