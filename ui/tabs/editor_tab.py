# -*- coding: utf-8 -*-
# ui/tabs/editor_tab.py

import gradio as gr

def render_editor_tab():
    """Render the Editor tab (manual editing interface)."""
    gr.Markdown("## ✏️ Editor")
    gr.Markdown(
        "Aici va apărea editorul interactiv pentru capitole, "
        "validări manuale, corecturi și alte unelte de revizie."
    )
