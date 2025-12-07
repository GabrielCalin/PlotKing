# ui/tabs/export/export_handlers.py
import os
import gradio as gr
import markdown
import requests
import base64
from ebooklib import epub
from state.checkpoint_manager import get_checkpoint
from llm.title_fetcher.llm import fetch_title_llm
from llm.cover_prompter.llm import generate_prompt
from utils.timestamp import ts_prefix

def fetch_title_handler(current_log):
    """
    Handler for the 'Fetch Title' button.
    """
    checkpoint = get_checkpoint()
    if not checkpoint:
        new_log = (current_log or "") + "\n" + ts_prefix("⚠️ No checkpoint found. Cannot fetch title.")
        return "", new_log.strip()

    expanded_plot = checkpoint.expanded_plot or ""
    if not expanded_plot:
        new_log = (current_log or "") + "\n" + ts_prefix("⚠️ No expanded plot found. Cannot fetch title.")
        return "", new_log.strip()

    new_log = (current_log or "") + "\n" + ts_prefix("🤖 Fetching title from AI...")
    
    try:
        title = fetch_title_llm(expanded_plot)
        final_log = new_log + "\n" + ts_prefix(f"✅ Title fetched: {title}")
        return title, final_log.strip()
    except Exception as e:
        final_log = new_log + "\n" + ts_prefix(f"❌ Error fetching title: {e}")
        return "", final_log.strip()

def suggest_cover_prompt_handler(current_log):
    """
    Handler for the 'Suggest' button.
    """
    checkpoint = get_checkpoint()
    if not checkpoint:
        return "", (current_log or "") + "\n" + ts_prefix("⚠️ No checkpoint found. Cannot suggest prompt.")
    
    expanded_plot = checkpoint.expanded_plot or ""
    if not expanded_plot:
        return "", (current_log or "") + "\n" + ts_prefix("⚠️ No expanded plot found. Cannot suggest prompt.")

    new_log = (current_log or "") + "\n" + ts_prefix("✨ Suggesting cover prompt...")
    
    try:
        prompt = generate_prompt(expanded_plot)
        final_log = new_log + "\n" + ts_prefix("✅ Prompt suggested.")
        return prompt, final_log.strip()
    except Exception as e:
        final_log = new_log + "\n" + ts_prefix(f"❌ Error suggesting prompt: {e}")
        return "", final_log.strip()

def generate_cover_handler(prompt, current_log):
    """
    Handler for the 'Generate Cover' button.
    """
    if not prompt or not prompt.strip():
        return None, (current_log or "") + "\n" + ts_prefix("⚠️ Prompt is required.")

    new_log = (current_log or "") + "\n" + ts_prefix(f"🎨 Generating cover for prompt: '{prompt}'...")
    
    try:
        payload = {
            "prompt": prompt,
            "steps": 20, # Increased steps for better quality
            "width": 512,
            "height": 768, # Portrait aspect ratio for book covers
            "cfg_scale": 7
        }
        
        response = requests.post("http://127.0.0.1:6969/sdapi/v1/txt2img", json=payload)
        
        if response.status_code == 200:
            r = response.json()
            image_b64 = r['images'][0]
            
            # Create tmp directory if it doesn't exist
            tmp_dir = "tmp"
            os.makedirs(tmp_dir, exist_ok=True)
            
            output_path = os.path.join(tmp_dir, "cover.png")
            
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(image_b64))
                
            final_log = new_log + "\n" + ts_prefix(f"✅ Cover generated: {output_path}")
            return os.path.abspath(output_path), final_log.strip()
        else:
            final_log = new_log + "\n" + ts_prefix(f"❌ Generation failed with status code: {response.status_code}")
            return None, final_log.strip()
            
    except Exception as e:
        final_log = new_log + "\n" + ts_prefix(f"❌ Error generating cover: {e}")
        return None, final_log.strip()

def export_book_handler(title, author, upload_path, gen_path, source, font_family, font_size, current_log):
    """
    Handler for the 'Export' button.
    Generates an EPUB file.
    """
    checkpoint = get_checkpoint()
    if not checkpoint:
        return None, (current_log or "") + "\n" + ts_prefix("⚠️ No checkpoint found. Cannot export.")

    if not title or not title.strip():
        return None, (current_log or "") + "\n" + ts_prefix("⚠️ Title is required.")
    
    if not author or not author.strip():
        return None, (current_log or "") + "\n" + ts_prefix("⚠️ Author is required.")

    # Determine cover image path
    cover_image_path = upload_path if source == "Upload" else gen_path

    new_log = (current_log or "") + "\n" + ts_prefix(f"📚 Starting export for '{title}' by {author}...")
    
    try:
        book = epub.EpubBook()

        book.set_identifier(f"id_{title.lower().replace(' ', '_')}")
        book.set_title(title)
        book.set_language('en')
        book.add_author(author)

        cover_page = None
        if cover_image_path and os.path.exists(cover_image_path):
            with open(cover_image_path, 'rb') as f:
                cover_content = f.read()
            ext = os.path.splitext(cover_image_path)[1]
            if not ext:
                ext = ".png" # Default to png if no extension
            cover_file_name = f"cover{ext}"
            
            book.set_cover(cover_file_name, cover_content, create_page=False)
            
            cover_html_content = f'<div style="text-align: center; padding: 0; margin: 0;"><img src="{cover_file_name}" alt="Cover" style="max-width: 100%; height: auto;" /></div>'
            cover_page = epub.EpubHtml(title="Cover", file_name="cover_page.xhtml", lang='en')
            cover_page.content = cover_html_content
            book.add_item(cover_page)
            
            new_log += "\n" + ts_prefix(f"🖼️ Cover image added from {source}.")
        else:
            new_log += "\n" + ts_prefix("ℹ️ No cover image provided or file not found.")

        title_page_content = f"""
        <div style="text-align: center; margin-top: 20%;">
            <h1 style="font-size: 2.5em; margin-bottom: 0.5em;">{title}</h1>
            <h2 style="font-size: 1.2em; font-weight: normal; margin-left: 10%; color: #444;">by {author}</h2>
        </div>
        """
        title_page = epub.EpubHtml(title="Title Page", file_name="title.xhtml", lang='en')
        title_page.content = title_page_content
        book.add_item(title_page)

        chapters_full = checkpoint.chapters_full or []
        epub_chapters = []
        
        book.spine = ['nav']
        if cover_page:
            book.spine.append(cover_page)
        book.spine.append(title_page)

        if not chapters_full:
             new_log += "\n" + ts_prefix("⚠️ No chapters found in checkpoint. Exporting empty book.")

        for i, chapter_content in enumerate(chapters_full):
            lines = chapter_content.split('\n')
            chapter_title = f"Chapter {i+1}"
            
            for line in lines:
                if line.strip().startswith("## "):
                    chapter_title = line.strip().replace("## ", "").strip()
                    break
            
            chapter_file_name = f"chapter_{i+1}.xhtml"
            
            html_content = markdown.markdown(chapter_content)
            
            c = epub.EpubHtml(title=chapter_title, file_name=chapter_file_name, lang='en')
            c.content = html_content
            
            c.add_item(epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css"))
            
            book.add_item(c)
            epub_chapters.append(c)
            book.spine.append(c)

        book.toc = [epub.Link("title.xhtml", "Title Page", "title")]
        book.toc.extend(epub_chapters)

        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        style = f'''
        body {{ 
            font-family: {font_family}; 
            font-size: {font_size};
            line-height: 1.6;
            margin: 0;
            padding: 0;
        }} 
        h1 {{ text-align: center; }}
        p {{ margin-bottom: 1em; }}
        '''
        nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
        book.add_item(nav_css)

        output_dir = "exports"
        os.makedirs(output_dir, exist_ok=True)
        
        safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')
        output_filename = f"{safe_title}.epub"
        output_path = os.path.join(output_dir, output_filename)

        epub.write_epub(output_path, book, {})
        
        final_log = new_log + "\n" + ts_prefix(f"✅ Export successful: {output_path}")
        
        return os.path.abspath(output_path), final_log.strip()

    except Exception as e:
        final_log = new_log + "\n" + ts_prefix(f"❌ Export failed: {e}")
        return None, final_log.strip()

