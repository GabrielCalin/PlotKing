# -*- coding: utf-8 -*-
# pipeline/runner_validate.py
"""
Pipeline dedicat pentru validarea editărilor.
Rulează version_diff, validări LLM pentru Chapters Overview (când e cazul),
și impact_analyzer pentru a construi planul.
"""

from handlers.editor.utils import format_validation_markdown

from state.checkpoint_manager import get_checkpoint, get_section_content
from state.infill_manager import InfillManager
from state.drafts_manager import DraftsManager, DraftType
from llm.version_diff import call_llm_version_diff
from llm.impact_analyzer import call_llm_impact_analysis
from llm.overview_validator_after_edit import call_llm_overview_validator_after_edit


def _format_overview_validation_errors(errors):
    details = "\n".join(f"- {err}" for err in errors)
    return f"""## ❌ Chapters Overview validation failed

{details}
"""


def _get_draft_warning(exclude_section: str) -> str:
    drafts_mgr = DraftsManager()
    user_drafts = drafts_mgr.get_user_drafts()
    other_drafts = [s for s in user_drafts if s != exclude_section]
    if other_drafts:
        draft_names = ", ".join([f"`{d}`" for d in other_drafts])
        return (
            "⚠️ **Validation is based on other drafts.**\n"
            f"Some related sections are still drafts: {draft_names}.\n"
            "Ensure these drafts are consistent before applying changes."
        )
    return ""


def _get_fill_draft_warning(exclude_section: str) -> str:
    drafts_mgr = DraftsManager()
    fill_drafts = drafts_mgr.get_fill_drafts()
    other_fills = [s for s in fill_drafts if s != exclude_section]
    if other_fills:
        fill_names = ", ".join([f"`{d}`" for d in other_fills])
        return (
            "⚠️ **Multiple fill drafts present.**\n"
            f"Other fill drafts exist: {fill_names}.\n"
            "The current fill will not be validated against other fill drafts."
        )
    return ""


def _append_warnings(section: str, msg: str) -> str:
    warning_msg = _get_draft_warning(section)
    if warning_msg:
        msg = warning_msg + "\n\n" + msg
    im = InfillManager()
    if im.is_fill(section):
        fill_warning_msg = _get_fill_draft_warning(section)
        if fill_warning_msg:
            msg = fill_warning_msg + "\n\n" + msg
    return msg


def build_fill_chapter_message(chapter_num: int, total_chapters: int) -> str:
    if chapter_num is None:
        return "New Chapter Created"

    if total_chapters == 0:
        return "New Chapter 1 will be created as the first chapter"
    if chapter_num == 1:
        return "New Chapter 1 will be inserted at the beginning, shifting all existing chapters forward by 1"
    if chapter_num > total_chapters:
        return f"New Chapter {chapter_num} will be inserted at the end, after Chapter {total_chapters}"

    prev_chapter = chapter_num - 1
    return f"New Chapter {chapter_num} will be inserted between existing Chapter {prev_chapter} and Chapter {chapter_num}, shifting chapters {chapter_num} onwards forward by 1"


def build_candidate_sections(section: str, checkpoint):
    candidates = []

    if not section:
        return candidates

    def add(name: str):
        if not name or name == section:
            return
        from state.checkpoint_manager import get_section_content

        drafts_mgr = DraftsManager()
        if drafts_mgr.has_type(name, DraftType.USER.value):
            content = drafts_mgr.get_content(name, DraftType.USER.value)
        else:
            content = get_section_content(name) or ""
        candidates.append((name, content))

    total_chapters = len(checkpoint.chapters_full or [])

    if section in {"Expanded Plot", "Chapters Overview"}:
        add("Expanded Plot")
        add("Chapters Overview")
        for idx in range(1, total_chapters + 1):
            add(f"Chapter {idx}")
    elif section.startswith("Fill"):
        add("Expanded Plot")
        add("Chapters Overview")
        im = InfillManager()
        chapter_num = im.parse_fill_target(section)
        if chapter_num:
            for idx in range(chapter_num, total_chapters + 1):
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

    unique = []
    seen = set()
    for name, content in candidates:
        if name in seen:
            continue
        seen.add(name)
        unique.append((name, content))
    return unique




def run_validate_pipeline(section, draft):
    checkpoint = get_checkpoint()
    if not checkpoint:
        return "Error: No checkpoint found.", None, False

    im = InfillManager()
    is_fill = im.is_fill(section)
    chapter_num = im.parse_fill_target(section) if is_fill else None

    if is_fill:
        result = "CHANGES_DETECTED"
        total_chapters = len(checkpoint.chapters_full or [])
        chapter_msg = build_fill_chapter_message(chapter_num, total_chapters)
        diff_data = {"changes": [chapter_msg]}
    else:
        original_version = get_section_content(section) or ""
        result, diff_data = call_llm_version_diff(
            section_type=section,
            original_version=original_version,
            modified_version=draft or "",
            genre=checkpoint.genre or "",
        )

    if result in {"ERROR", "UNKNOWN", "NO_CHANGES"}:
        msg = format_validation_markdown(result, diff_data)
        return _append_warnings(section, msg), None, False

    if result != "CHANGES_DETECTED":
        msg = format_validation_markdown(result, diff_data)
        return _append_warnings(section, msg), None, False

    if diff_data.get("changes"):
        diff_summary_text = "\n".join(f"- {item}" for item in diff_data.get("changes", []) if item)
    else:
        diff_summary_text = diff_data.get("message", "")

    if section == "Chapters Overview":
        validator_result, validator_data = call_llm_overview_validator_after_edit(
            new_overview=draft or "",
            diff_summary=diff_summary_text,
        )
        if validator_result == "ISSUES":
            errors = []
            numbering = validator_data.get("numbering", {})
            deleted = validator_data.get("deleted", {})
            if not numbering.get("valid", True):
                reason = numbering.get("reason", "")
                errors.append(f"Chapter numbering is invalid. {reason}".strip())
            if deleted.get("detected", False):
                reason = deleted.get("reason", "")
                errors.append(f"Chapter deletion detected. Removing chapters is not supported. {reason}".strip())
            if errors:
                msg = _format_overview_validation_errors(errors)
                return msg, None, True
        elif validator_result == "ERROR":
            error_msg = validator_data.get("error", "Unknown error")
            msg = f"## ❌ Overview validation error\n\n{error_msg}"
            return msg, None, True

    candidates = build_candidate_sections(section, checkpoint)

    if is_fill and chapter_num is not None:
        section_name_for_impact = f"Chapter {chapter_num} (Candidate)"
    else:
        section_name_for_impact = section

    total_chapters = len(checkpoint.chapters_full or [])
    impact_result, impact_data, impacted = call_llm_impact_analysis(
        section_name=section_name_for_impact,
        edited_section_content=draft or "",
        diff_summary=diff_summary_text,
        candidate_sections=candidates,
        is_infill=is_fill,
        total_chapters=total_chapters,
    )

    msg = format_validation_markdown(result, diff_data, impact_result, impact_data, impacted)
    plan = {
        "edited_section": section_name_for_impact,
        "diff_data": diff_data,
        "impact_data": impact_data,
        "impacted_sections": impacted,
        "fill_name": section if is_fill else None,
    } if impact_result == "IMPACT_DETECTED" and impacted else None

    return _append_warnings(section, msg), plan, False

