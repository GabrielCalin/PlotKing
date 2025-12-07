# ui/tabs/export_tab.py
import gradio as gr
from handlers.export.export_handlers import fetch_title_handler, export_book_handler, generate_cover_handler, suggest_cover_prompt_handler
from state.checkpoint_manager import get_sections_list

def render_export_tab(editor_sections_epoch, create_sections_epoch):
    """
    Render the Export tab.
    """
    
    # State
    export_log = gr.State("")
    
    # ---- (0) Empty state message (visible by default) ----
    empty_msg = gr.Markdown(
        "📚 **Nothing to export yet!**  \n"
        "Your story world is still blank — go craft one in the *Create* tab! ✨",
        elem_id="export-empty",
        visible=True,
    )

    # ---- (1) Main Layout ----
    with gr.Column(visible=False) as export_main:
        gr.Markdown("## 📤 Export Book")
        
        with gr.Row(elem_id="export-content-row", equal_height=True):
            with gr.Column(scale=2):
                with gr.Column(elem_classes=["plot-wrapper"]):
                    with gr.Row(elem_classes=["plot-header"]):
                        gr.Markdown("Book Title", elem_id="title-label")
                        with gr.Row(elem_classes=["plot-buttons"]):
                            fetch_title_btn = gr.Button("🤖 Fetch", size="sm", elem_id="fetch-btn")
                    title_input = gr.Textbox(
                        label=None,
                        show_label=False,
                        placeholder="Enter book title...",
                        elem_id="export-title",
                        lines=1,
                        max_lines=1
                    )
                
                author_input = gr.Textbox(label="Author Name", placeholder="Enter author name...", elem_id="export-author", lines=1)
                
                with gr.Row():
                    font_family_dropdown = gr.Dropdown(
                        label="Font Family",
                        choices=[
                            ("Georgia (Recommended)", "Georgia, serif"),
                            ("Times New Roman (Classic)", "Times New Roman, Times, serif"),
                            ("Garamond (Elegant)", "Garamond, serif"),
                            ("Palatino (Professional)", "Palatino, serif"),
                            ("Merriweather (Modern Serif)", "Merriweather, serif"),
                            ("Arial (Clean)", "Arial, sans-serif"),
                            ("Verdana (Readable)", "Verdana, sans-serif"),
                            ("Open Sans (Modern)", "Open Sans, sans-serif"),
                        ],
                        value="Georgia, serif",
                        interactive=True
                    )
                    font_size_dropdown = gr.Dropdown(
                        label="Font Size",
                        choices=["10pt", "11pt", "12pt", "13pt", "14pt", "16pt", "18pt"],
                        value="12pt",
                        interactive=True
                    )
                
                gr.Markdown("### Cover Image")
                cover_source = gr.Radio(
                    choices=["Upload", "Generate"],
                    value="Upload",
                    label="Cover Source",
                    interactive=True
                )
                
                with gr.Column(visible=True) as upload_cover_group:
                    cover_image = gr.Image(label="Upload Cover", type="filepath", height=300, elem_id="export-cover")

                with gr.Column(visible=False) as generate_cover_group:
                    with gr.Row():
                        prompt_input = gr.Textbox(
                            label="Image Prompt", 
                            placeholder="Describe the cover image...", 
                            lines=3,
                            scale=4
                        )
                        suggest_btn = gr.Button("✨ Suggest", scale=1)
                    
                    generate_btn = gr.Button("🎨 Generate Cover", variant="primary")
                    generated_cover_image = gr.Image(label="Generated Cover", type="filepath", height=300, interactive=False)
                
            with gr.Column(scale=1):
                export_status = gr.Textbox(label="Process Log", lines=30, interactive=False, elem_id="export-log")
                
        with gr.Row():
            export_btn = gr.Button("📦 Export EPUB", variant="primary", scale=2)
            download_btn = gr.DownloadButton("⬇️ Download EPUB", visible=False, scale=1)

    # ====== Helper functions ======
    def _refresh_export_tab(_):
        """Check if we have content to export."""
        sections = get_sections_list()
        if not sections:
             return gr.update(visible=True), gr.update(visible=False)
        return gr.update(visible=False), gr.update(visible=True)

    # ====== Wiring ======
    
    # Sync visibility with other tabs
    editor_sections_epoch.change(
        fn=_refresh_export_tab,
        inputs=[editor_sections_epoch],
        outputs=[empty_msg, export_main]
    )
    
    create_sections_epoch.change(
        fn=_refresh_export_tab,
        inputs=[create_sections_epoch],
        outputs=[empty_msg, export_main]
    )

    # Fetch Title
    fetch_title_btn.click(
        fn=fetch_title_handler,
        inputs=[export_log],
        outputs=[title_input, export_status]
    ).then(
        fn=lambda log: log, # Update state
        inputs=[export_status],
        outputs=[export_log]
    )

    # Toggle Cover Source
    def _toggle_cover_source(source):
        return gr.update(visible=(source == "Upload")), gr.update(visible=(source == "Generate"))

    cover_source.change(
        fn=_toggle_cover_source,
        inputs=[cover_source],
        outputs=[upload_cover_group, generate_cover_group]
    )

    # Suggest Prompt
    suggest_btn.click(
        fn=suggest_cover_prompt_handler,
        inputs=[export_log],
        outputs=[prompt_input, export_status]
    ).then(
        fn=lambda log: log,
        inputs=[export_status],
        outputs=[export_log]
    )

    # Generate Cover
    generate_btn.click(
        fn=generate_cover_handler,
        inputs=[prompt_input, export_log],
        outputs=[generated_cover_image, export_status]
    ).then(
        fn=lambda log: log,
        inputs=[export_status],
        outputs=[export_log]
    )

    # Export Book
    # Note: We need to handle which image to use. For now, we'll pass the visible one or handle it in the handler.
    # Actually, simpler: The handler takes a path. We can have a wrapper to pick the right one.
    # But wait, 'cover_image' is the upload one. 'generated_cover_image' is the generated one.
    # We should update the export handler call to pass the correct image based on the radio selection.
    
    def _get_active_cover(source, upload_path, gen_path):
        return upload_path if source == "Upload" else gen_path

    export_btn.click(
        fn=_get_active_cover,
        inputs=[cover_source, cover_image, generated_cover_image],
        outputs=[gr.State()]
    ).then(
        fn=export_book_handler,
        inputs=[title_input, author_input, cover_image, generated_cover_image, cover_source, font_family_dropdown, font_size_dropdown, export_log],
        outputs=[download_btn, export_status]
    ).then(
        fn=lambda log: log, # Update state
        inputs=[export_status],
        outputs=[export_log]
    ).then(
        fn=lambda path: gr.update(visible=True, value=path) if path else gr.update(visible=False),
        inputs=[download_btn],
        outputs=[download_btn]
    )
