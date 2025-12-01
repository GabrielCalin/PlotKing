# ui/export_handlers.py
import os
import gradio as gr
import markdown
from ebooklib import epub
from pipeline.state_manager import get_checkpoint
from pipeline.steps.title_fetcher.llm import fetch_title_llm
from utils.timestamp import ts_prefix

def fetch_title_handler(current_log):
    """
    Handler for the 'Fetch Title' button.
    """
    checkpoint = get_checkpoint()
    if not checkpoint:
        new_log = (current_log or "") + "\n" + ts_prefix("⚠️ No checkpoint found. Cannot fetch title.")
        return "", new_log.strip()

    expanded_plot = checkpoint.get("expanded_plot", "")
    if not expanded_plot:
        new_log = (current_log or "") + "\n" + ts_prefix("⚠️ No expanded plot found. Cannot fetch title.")
        return "", new_log.strip()

    new_log = (current_log or "") + "\n" + ts_prefix("🤖 Fetching title from AI...")
    # Return intermediate log update (though Gradio might not show it if we don't yield, but this is a simple return)
    # For better UX, we could yield, but let's keep it simple for now or use a generator if needed.
    # Since this is a button click, we can just return the final result.
    
    try:
        title = fetch_title_llm(expanded_plot)
        final_log = new_log + "\n" + ts_prefix(f"✅ Title fetched: {title}")
        return title, final_log.strip()
    except Exception as e:
        final_log = new_log + "\n" + ts_prefix(f"❌ Error fetching title: {e}")
        return "", final_log.strip()

def export_book_handler(title, author, cover_image_path, font_family, font_size, current_log):
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

    new_log = (current_log or "") + "\n" + ts_prefix(f"📚 Starting export for '{title}' by {author}...")
    
    try:
        book = epub.EpubBook()

        # Metadata
        book.set_identifier(f"id_{title.lower().replace(' ', '_')}")
        book.set_title(title)
        book.set_language('en')
        book.add_author(author)

        # Cover Image
        cover_page = None
        if cover_image_path and os.path.exists(cover_image_path):
            # EbookLib expects the image content, or we can use set_cover
            # set_cover(file_name, content, create_page=True) -> create_page=True creates a cover page but sometimes it's better to control it.
            # We will use set_cover for metadata and create our own internal page if needed, or rely on create_page=False and do it manually.
            # Let's do it manually to ensure it's in the content flow as requested.
            
            with open(cover_image_path, 'rb') as f:
                cover_content = f.read()
            ext = os.path.splitext(cover_image_path)[1]
            cover_file_name = f"cover{ext}"
            
            # This adds the image file to the manifest and sets it as cover in metadata
            book.set_cover(cover_file_name, cover_content, create_page=False)
            
            # Create internal cover page
            cover_html_content = f'<div style="text-align: center; padding: 0; margin: 0;"><img src="{cover_file_name}" alt="Cover" style="max-width: 100%; height: auto;" /></div>'
            cover_page = epub.EpubHtml(title="Cover", file_name="cover_page.xhtml", lang='en')
            cover_page.content = cover_html_content
            book.add_item(cover_page)
            
            new_log += "\n" + ts_prefix("🖼️ Cover image added.")
        else:
            new_log += "\n" + ts_prefix("ℹ️ No cover image provided or file not found.")

        # Title Page (Manual creation if needed, but EbookLib might handle basic metadata)
        # Let's add a simple title page chapter
        title_page_content = f"<h1>{title}</h1><h2>by {author}</h2>"
        title_page = epub.EpubHtml(title="Title Page", file_name="title.xhtml", lang='en')
        title_page.content = title_page_content
        book.add_item(title_page)

        # Chapters
        chapters_full = checkpoint.get("chapters_full", [])
        epub_chapters = []
        
        # Add items to spine
        book.spine = ['nav']
        if cover_page:
            book.spine.append(cover_page)
        book.spine.append(title_page)

        if not chapters_full:
             new_log += "\n" + ts_prefix("⚠️ No chapters found in checkpoint. Exporting empty book.")

        for i, chapter_content in enumerate(chapters_full):
            # Extract title from markdown (first H2)
            lines = chapter_content.split('\n')
            chapter_title = f"Chapter {i+1}" # Default
            
            # Find first line starting with "## "
            for line in lines:
                if line.strip().startswith("## "):
                    chapter_title = line.strip().replace("## ", "").strip()
                    break
            
            chapter_file_name = f"chapter_{i+1}.xhtml"
            
            # Convert markdown to HTML
            # We use extra extensions for better rendering if needed, but basic is fine for now.
            html_content = markdown.markdown(chapter_content)
            
            c = epub.EpubHtml(title=chapter_title, file_name=chapter_file_name, lang='en')
            # We don't add an extra H1 title here because the content likely already has the title as H2
            # If the user wants the title to be H1 in the epub, we could replace the first H2 with H1 in the HTML,
            # but keeping it as is (H2) is safer to match the source.
            c.content = html_content
            
            # Add CSS link
            c.add_item(epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css"))
            
            book.add_item(c)
            epub_chapters.append(c)
            book.spine.append(c)

        # Table of Contents
        # Flattened structure: Title Page -> Chapters
        book.toc = [epub.Link("title.xhtml", "Title Page", "title")]
        book.toc.extend(epub_chapters)

        # Navigation
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # Define CSS
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

        # Output Directory
        output_dir = "exports"
        os.makedirs(output_dir, exist_ok=True)
        
        # Safe filename
        safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')
        output_filename = f"{safe_title}.epub"
        output_path = os.path.join(output_dir, output_filename)

        epub.write_epub(output_path, book, {})
        
        final_log = new_log + "\n" + ts_prefix(f"✅ Export successful: {output_path}")
        
        # Return the absolute path for the download button
        return os.path.abspath(output_path), final_log.strip()

    except Exception as e:
        final_log = new_log + "\n" + ts_prefix(f"❌ Export failed: {e}")
        return None, final_log.strip()
