from typing import List, Tuple, Dict, Any
from handlers.editor.utils import format_validation_markdown

def editor_validate(section, draft):
    """Validează modificările comparând versiunea originală cu versiunea editată."""
    from state.checkpoint_manager import get_checkpoint, get_section_content
    from llm.version_diff import call_llm_version_diff
    from llm.impact_analyzer import call_llm_impact_analysis

    checkpoint = get_checkpoint()
    if not checkpoint:
        return "Error: No checkpoint found.", None

    original_version = get_section_content(section) or ""

    result, diff_data = call_llm_version_diff(
        section_type=section,
        original_version=original_version,
        modified_version=draft or "",
        genre=checkpoint.genre or "",
    )

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
        plan = {
            "edited_section": section,
            "diff_data": diff_data,
            "impact_data": impact_data,
            "impacted_sections": impacted,
        } if impact_result == "IMPACT_DETECTED" and impacted else None
    else:
        msg = format_validation_markdown(result, diff_data)
        plan = None

    # Append draft warning to message if applicable
    warning_msg = _get_draft_warnings(section)
    if warning_msg:
        msg = warning_msg + "\n\n" + msg

    return msg, plan

def _build_candidate_sections(section: str, checkpoint) -> List[Tuple[str, str]]:
    candidates: List[Tuple[str, str]] = []

    if not section:
        return candidates

    def add(name: str):
        if not name or name == section:
            return
        from state.checkpoint_manager import get_section_content
        from state.drafts_manager import DraftsManager
        
        drafts_mgr = DraftsManager()
        # Prioritize USER draft content if exists
        if drafts_mgr.has(name) and drafts_mgr.get_type(name) == "user":
            content = drafts_mgr.get_content(name)
        else:
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

def _get_draft_warnings(exclude_section: str) -> str:
    """Check for existing USER drafts in other sections and return a warning markdown string."""
    from state.drafts_manager import DraftsManager
    drafts_mgr = DraftsManager()
    user_drafts = drafts_mgr.get_user_drafts()
    
    # Exclude current section since we are validating it actively
    other_drafts = [s for s in user_drafts if s != exclude_section]
    
    if other_drafts:
        draft_names = ", ".join([f"`{d}`" for d in other_drafts])
        return f"""
> [!WARNING]
> **Validation Context Alert**: The following sections have active **User Drafts** that were used for validation context instead of the checkpoint versions: {draft_names}.
> Ensure these drafts are consistent before applying major changes.
"""
    return ""

