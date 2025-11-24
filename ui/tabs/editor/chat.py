# ui/tabs/editor/chat.py
import gradio as gr
import difflib
import ui.editor_handlers as H
from ui.tabs.editor.utils import append_status
from pipeline.steps.chat_editor.llm import call_llm_chat

def chat_handler(section, message, history, current_text, initial_text, current_log):
    """
    Handles the chat interaction with the Plot King.
    Uses OpenAI-style messages format: [{'role': 'user', 'content': '...'}, ...]
    """
    if not message:
        return (
            gr.update(value=""), # clear input
            history,
            history, # chatbot update
            gr.update(), # viewer_md
            gr.update(), # validate_btn
            gr.update(), # discard_btn
            gr.update(), # force_edit_btn
            gr.update(), # diff_btn
            current_log,
            gr.update(), # status_strip
            current_text, # current_md
            gr.update(), # chat_input (no change)
            gr.update(), # chat_clear_btn (no change)
        )

    # Append user message to history
    new_history = history + [{"role": "user", "content": message}]
    
    new_log, status_update = append_status(current_log, f"💬 ({section}) Asking Plot King...")
    
    # Yield loading state
    yield (
        gr.update(value="", interactive=False), # clear input and disable
        new_history,
        new_history, # chatbot update
        gr.update(), # viewer_md
        gr.update(), # validate_btn
        gr.update(), # discard_btn
        gr.update(), # force_edit_btn
        gr.update(), # diff_btn
        new_log,
        status_update,
        current_text,
        gr.update(interactive=False), # chat_input disable
        gr.update(interactive=False), # chat_clear_btn disable
    )

    # Call LLM
    try:
        # Pass the full history (including the new message) to the LLM
        # The LLM step expects a list of dicts, which matches our new format
        result = call_llm_chat(
            section_name=section,
            initial_content=initial_text,
            current_content=current_text,
            conversation_history=new_history, # Pass full history including current msg
            user_message=message # Still pass this if the LLM step treats it specially, but usually history is enough
        )
        
        response_text = result.get("response", "I'm speechless!")
        new_content = result.get("new_content")
        
        # Append bot response to history
        new_history.append({"role": "assistant", "content": response_text})
        
        if new_content:
            # Edits were made
            final_log, final_status = append_status(new_log, f"✅ ({section}) Plot King made edits.")
            yield (
                gr.update(value="", interactive=True),
                new_history,
                new_history, # chatbot update
                gr.update(value=new_content), # viewer_md updated with new content
                gr.update(visible=True), # validate_btn
                gr.update(visible=True), # discard_btn
                gr.update(visible=True), # force_edit_btn
                gr.update(visible=True, value="⚖️ Diff"), # diff_btn
                final_log,
                final_status,
                new_content, # update current_md
                gr.update(interactive=True), # chat_input enable
                gr.update(interactive=True), # chat_clear_btn enable
            )
        else:
            # No edits, just chat
            final_log, final_status = append_status(new_log, f"✅ ({section}) Plot King replied.")
            yield (
                gr.update(value="", interactive=True),
                new_history,
                new_history, # chatbot update
                gr.update(), # viewer_md unchanged
                gr.update(), # validate_btn unchanged
                gr.update(), # discard_btn unchanged
                gr.update(), # force_edit_btn unchanged
                gr.update(), # diff_btn unchanged
                final_log,
                final_status,
                current_text, # current_md unchanged
                gr.update(interactive=True), # chat_input enable
                gr.update(interactive=True), # chat_clear_btn enable
            )
            
    except Exception as e:
        error_msg = f"Error talking to Plot King: {str(e)}"
        new_history.append({"role": "assistant", "content": error_msg})
        final_log, final_status = append_status(new_log, f"❌ ({section}) Chat error: {str(e)}")
        yield (
            gr.update(value="", interactive=True),
            new_history,
            new_history, # chatbot update
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            final_log,
            final_status,
            current_text,
            gr.update(interactive=True), # chat_input enable
            gr.update(interactive=True), # chat_clear_btn enable
        )


PLOT_KING_GREETING = "Hello! I'm Plot King, your friendly creative sidekick. How can I help you today?"

def clear_chat(section, current_log):
    """Resets the chat history to the initial greeting."""
    initial_greeting = [{"role": "assistant", "content": PLOT_KING_GREETING}]
    new_log, status_update = append_status(current_log, f"🧹 ({section}) Chat cleared.")
    return initial_greeting, new_log, status_update, initial_greeting

def diff_handler(current_text, initial_text, diff_btn_label):
    """
    Toggles between Draft view and Diff view.
    Uses paragraph-level diffing with inline word-level diffs for modifications.
    """
    if diff_btn_label == "⚖️ Diff":
        import re
        
        # 1. Tokenize by paragraphs (splitting by double newlines)
        def tokenize_paragraphs(text):
            return re.split(r'(\n\n+)', text)

        # 2. Tokenize by words (keeping whitespace)
        def tokenize_words(text):
            return re.split(r'(\s+)', text)

        initial_paras = tokenize_paragraphs(initial_text)
        current_paras = tokenize_paragraphs(current_text)
        
        matcher = difflib.SequenceMatcher(None, initial_paras, current_paras)
        
        html_parts = []
        
        # CSS classes are defined in editor.css
        # .diff-view, .diff-del, .diff-ins, .diff-del-word, .diff-ins-word
        
        for opcode, a0, a1, b0, b1 in matcher.get_opcodes():
            if opcode == 'equal':
                # Unchanged paragraphs
                for i in range(a0, a1):
                    html_parts.append(initial_paras[i])
            
            elif opcode == 'delete':
                # Deleted paragraphs
                for i in range(a0, a1):
                    # Wrap entire paragraph in delete style
                    html_parts.append(f'<div class="diff-del">{initial_paras[i]}</div>')
            
            elif opcode == 'insert':
                # Inserted paragraphs
                for i in range(b0, b1):
                    # Wrap entire paragraph in insert style
                    html_parts.append(f'<div class="diff-ins">{current_paras[i]}</div>')
            
            elif opcode == 'replace':
                # Replaced paragraphs
                # If it's a 1-to-1 replacement, try word-level diff
                if (a1 - a0) == 1 and (b1 - b0) == 1:
                    p_old = initial_paras[a0]
                    p_new = current_paras[b0]
                    
                    # Check if it's just a newline change (which happens with the split)
                    if not p_old.strip() and not p_new.strip():
                         html_parts.append(p_new)
                         continue

                    w_matcher = difflib.SequenceMatcher(None, tokenize_words(p_old), tokenize_words(p_new))
                    
                    para_html = []
                    for w_opcode, wa0, wa1, wb0, wb1 in w_matcher.get_opcodes():
                        if w_opcode == 'equal':
                            para_html.append("".join(tokenize_words(p_old)[wa0:wa1]))
                        elif w_opcode == 'delete':
                            del_text = "".join(tokenize_words(p_old)[wa0:wa1])
                            para_html.append(f'<span class="diff-del-word">{del_text}</span>')
                        elif w_opcode == 'insert':
                            ins_text = "".join(tokenize_words(p_new)[wb0:wb1])
                            para_html.append(f'<span class="diff-ins-word">{ins_text}</span>')
                        elif w_opcode == 'replace':
                            del_text = "".join(tokenize_words(p_old)[wa0:wa1])
                            ins_text = "".join(tokenize_words(p_new)[wb0:wb1])
                            para_html.append(f'<span class="diff-del-word">{del_text}</span>')
                            para_html.append(f'<span class="diff-ins-word">{ins_text}</span>')
                    
                    html_parts.append("".join(para_html))
                else:
                    # Block replacement (too different or multi-paragraph)
                    # Show old block as deleted, new block as inserted
                    for i in range(a0, a1):
                        html_parts.append(f'<div class="diff-del">{initial_paras[i]}</div>')
                    for i in range(b0, b1):
                        html_parts.append(f'<div class="diff-ins">{current_paras[i]}</div>')
        
        final_html = "".join(html_parts)
        
        # Wrap in container with class
        final_html = f'<div class="diff-view">{final_html}</div>'
        
        return (
            gr.update(value=final_html), # viewer_md shows diff
            gr.update(value="📝 Show Draft"), # Toggle button label
        )
    else:
        # Revert to Draft view
        return (
            gr.update(value=current_text), # viewer_md shows draft
            gr.update(value="⚖️ Diff"), # Toggle button label
        )

def validate_handler(section, current_text, current_log):
    """
    Starts validation for the chat edits. Hides Chat UI.
    """
    new_log, status_update = append_status(current_log, f"🔍 ({section}) Validation started (from Chat).")
    
    # Hide Chat UI, Show Validation UI
    yield (
        gr.update(visible=False), # chat_group
        gr.update(visible=True), # validation_title
        gr.update(value="🔄 Validating...", visible=True), # validation_box
        gr.update(visible=False), # apply_updates_btn
        gr.update(visible=False), # regenerate_btn
        gr.update(visible=False), # continue_btn
        gr.update(visible=False), # discard2_btn
        gr.update(visible=True, value=current_text), # viewer_md
        new_log,
        status_update,
        None, # pending_plan placeholder
        gr.update(value="⚖️ Diff") # chat_diff_btn reset
    )
    
    msg, plan = H.editor_validate(section, current_text)
    final_log, final_status = append_status(new_log, f"✅ ({section}) Validation completed.")
    
    yield (
        gr.update(visible=False), # chat_group
        gr.update(visible=True), # validation_title
        gr.update(value=msg, visible=True), # validation_box
        gr.update(visible=True), # apply_updates_btn
        gr.update(visible=True), # regenerate_btn
        gr.update(visible=True), # continue_btn
        gr.update(visible=True), # discard2_btn
        gr.update(visible=True, value=current_text), # viewer_md
        final_log,
        final_status,
        plan, # pending_plan
        gr.update(value="⚖️ Diff") # chat_diff_btn reset
    )

def discard_handler(section, current_log):
    """
    Discards chat edits and reverts to checkpoint.
    """
    clean_text = H.editor_get_section_content(section) or "_Empty_"
    new_log, status_update = append_status(current_log, f"🗑️ ({section}) Chat edits discarded.")
    
    return (
        gr.update(value=clean_text), # viewer_md
        gr.update(visible=False), # validate_btn
        gr.update(visible=False), # discard_btn
        gr.update(visible=False), # force_edit_btn
        gr.update(visible=False, value="⚖️ Diff"), # diff_btn (reset label too)
        clean_text, # current_md
        new_log,
        status_update
    )

def force_edit_handler(section, current_text, current_log, create_epoch):
    """
    Force saves the chat edits to checkpoint.
    """
    updated_text = H.force_edit(section, current_text)
    new_log, status_update = append_status(current_log, f"⚡ ({section}) Synced (forced from Chat).")
    new_create_epoch = (create_epoch or 0) + 1
    
    return (
        gr.update(value=updated_text), # viewer_md
        gr.update(visible=False), # validate_btn
        gr.update(visible=False), # discard_btn
        gr.update(visible=False), # force_edit_btn
        gr.update(visible=False, value="⚖️ Diff"), # diff_btn
        updated_text, # current_md
        new_log,
        status_update,
        new_create_epoch
    )

def continue_edit(section, current_log, current_md):
    """Return to editing mode. If Chat mode, return to Chat Section."""
    new_log, status_update = append_status(current_log, f"🔁 ({section}) Continue chatting.")
    return (
        gr.update(visible=False),   # hide Validation Title
        gr.update(visible=False),   # hide Validation Box
        gr.update(visible=False),   # hide Apply Updates
        gr.update(visible=False),   # hide Regenerate
        gr.update(visible=False),   # hide Continue Editing
        gr.update(visible=False),   # hide Discard2
        gr.update(visible=False),   # hide Validate (Manual)
        gr.update(visible=False),   # hide Discard (Manual)
        gr.update(visible=False),   # hide Force Edit (Manual)
        gr.update(visible=False),   # hide Rewrite Section
        gr.update(visible=True, value=current_md),  # show viewer_md
        gr.update(visible=False),   # hide editor_tb
        gr.update(value="Chat", interactive=True), # unlock Mode
        gr.update(interactive=True), # unlock Section
        status_update,
        new_log,
        gr.update(visible=True),    # SHOW Chat Section
    )
