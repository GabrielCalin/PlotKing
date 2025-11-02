# -*- coding: utf-8 -*-
import gradio as gr
from ui.interface import create_interface
from pipeline.runner import generate_book_outline_stream
from pipeline.steps.refine_plot.step0_refine_plot import refine_plot

if __name__ == "__main__":
    demo = create_interface(generate_book_outline_stream, refine_plot)
    demo.launch(server_name="0.0.0.0", server_port=7860)
