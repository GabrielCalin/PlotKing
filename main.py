# -*- coding: utf-8 -*-
import gradio as gr
from ui.interface import create_interface

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(server_name="0.0.0.0", server_port=7860)
