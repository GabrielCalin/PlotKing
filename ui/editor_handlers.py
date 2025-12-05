from typing import List, Tuple, Dict, Any
from ui.tabs.editor.utils import format_validation_markdown

def editor_validate(section, draft):
    """Validează modificările comparând versiunea originală cu versiunea editată."""
    from pipeline.checkpoint_manager import get_checkpoint, get_section_content
    from pipeline.steps.version_diff import call_llm_version_diff
    from pipeline.steps.impact_analyzer import call_llm_impact_analysis

    checkpoint = get_checkpoint()
    if not checkpoint:
        return "Error: No checkpoint found.", None

    # Obține versiunea originală din checkpoint (fără să o modificăm)
    original_version = get_section_content(section) or ""

    # Apelează call_llm_version_diff
    result, diff_data = call_llm_version_diff(
        section_type=section,
        original_version=original_version,
        modified_version=draft or "",
        genre=checkpoint.genre or "",
    )

    # Formatează rezultatul pentru Validation Output
    if result == "ERROR":
        msg = format_validation_markdown(result, diff_data)
        plan = None
    elif result == "UNKNOWN":
        msg = format_validation_markdown(result, diff_data)
        plan = None
    elif result == "NO_CHANGES":
        msg = format_validation_markdown(result, diff_data)
        plan = None
    elif result == "CHANGES_DETECTED":
        candidates = _build_candidate_sections(section, checkpoint)
        if diff_data.get("changes"):
            diff_summary_text = "\n".join(f"- {item}" for item in diff_data.get("changes", []) if item)
        else:
            diff_summary_text = diff_data.get("message", "")

        impact_result, impact_data, impacted = call_llm_impact_analysis(
            section_name=section,
            edited_section_content=draft or "",
            diff_summary=diff_summary_text,
            candidate_sections=candidates,
        )
        msg = format_validation_markdown(result, diff_data, impact_result, impact_data, impacted)
        # Păstrăm datele pentru runner_edit
        plan = {
            "edited_section": section,
            "diff_data": diff_data,
            "impact_data": impact_data,
            "impacted_sections": impacted,
        } if impact_result == "IMPACT_DETECTED" and impacted else None
    else:
        msg = format_validation_markdown(result, diff_data)
        plan = None

    return msg, plan

def editor_apply(section, draft, plan):
    """
    Aplică modificarea și rulează pipeline-ul de editare dacă există secțiuni impactate.
    Returnează drafts (dict) și rulează pipeline-ul de editare.
    """
    from pipeline.checkpoint_manager import get_checkpoint
    
    checkpoint = get_checkpoint()
    if not checkpoint:
        return {section: draft}
    
    # Initialize drafts with the user's manual edit
    from ui.tabs.editor.drafts_manager import DraftsManager
    drafts = DraftsManager()
    drafts.add_original(section, draft)
    
    # Dacă există plan cu secțiuni impactate, rulează pipeline-ul de editare
    if plan and isinstance(plan, dict):
        edited_section = plan.get("edited_section", section)
        diff_data = plan.get("diff_data", {})
        impact_data = plan.get("impact_data", {})
        impacted = plan.get("impacted_sections", [])
        
        if impacted:
            from pipeline.runner_edit import run_edit_pipeline_stream
            
            # No need to yield drafts here - DraftsManager is a Singleton accessible everywhere
            
            for result in run_edit_pipeline_stream(
                edited_section=edited_section,
                diff_data=diff_data,
                impact_data=impact_data,
                impacted_sections=impacted,
            ):
                # result is a tuple, the last element is the drafts dict (now DraftsManager)
                if isinstance(result, tuple) and len(result) >= 9:
                    pipeline_drafts = result[8]
                    # Update our drafts with what the pipeline produced
                    drafts.update(pipeline_drafts)
                    
                    # Yield the full result from pipeline (caller expects this structure)
                    # We pass drafts as part of the result or handle it in the caller
                    # The caller (validate.py) expects specific tuple unpacking
                    yield result
                else:
                    # Fallback or error state
                    yield result
            return
    
    # Dacă nu există plan sau nu sunt secțiuni impactate, doar returnează draft-ul inițial
    return drafts


def editor_rewrite(section, selected_text, instructions):
    """
    Rewrite selected text based on instructions using LLM.
    Returns a dict with success status and result/message.
    """
    from pipeline.steps.rewrite_editor.llm import call_llm_rewrite_editor
    
    if not selected_text:
        return {"success": False, "message": "No text selected."}
    
    # Get full section content for context
    from pipeline.checkpoint_manager import get_section_content
    full_content = get_section_content(section)
    
    # Calculate context padding
    context_before = ""
    context_after = ""
    
    if len(selected_text) < 50:
        try:
            # Find the selection in the full content
            # Note: This is a simple find. If the text appears multiple times, 
            # it might pick the wrong one, but for now we assume uniqueness or first match is close enough.
            # A more robust solution would require passing indices from the frontend.
            idx = full_content.find(selected_text)
            if idx != -1:
                start = max(0, idx - 25)
                end = min(len(full_content), idx + len(selected_text) + 25)
                
                context_before = full_content[start:idx]
                context_after = full_content[idx + len(selected_text):end]
        except Exception:
            pass

    # Call LLM
    result = call_llm_rewrite_editor(
        section_content=full_content,
        selected_text=selected_text,
        instructions=instructions,
        context_before=context_before,
        context_after=context_after,
    )
    
    return result

def _build_candidate_sections(section: str, checkpoint) -> List[Tuple[str, str]]:
    candidates: List[Tuple[str, str]] = []

    if not section:
        return candidates

    def add(name: str):
        if not name or name == section:
            return
        from pipeline.checkpoint_manager import get_section_content
        content = get_section_content(name) or ""
        candidates.append((name, content))

    total_chapters = len(checkpoint.chapters_full or [])

    if section in {"Expanded Plot", "Chapters Overview"}:
        add("Expanded Plot")
        add("Chapters Overview")
        for idx in range(1, total_chapters + 1):
            add(f"Chapter {idx}")
    elif section.startswith("Chapter "):
        add("Expanded Plot")
        add("Chapters Overview")
        try:
            chapter_num = int(section.split(" ")[1])
        except (ValueError, IndexError):
            chapter_num = None
        if chapter_num:
            for idx in range(chapter_num + 1, total_chapters + 1):
                add(f"Chapter {idx}")
    else:
        add("Expanded Plot")
        add("Chapters Overview")

    unique: List[Tuple[str, str]] = []
    seen = set()
    for name, content in candidates:
        if name in seen:
            continue
        seen.add(name)
        unique.append((name, content))
    return unique
