# -*- coding: utf-8 -*-
# handlers/create/utils.py

from typing import Dict, Any, List, Optional


def display_selected_chapter(chapter_name, chapters):
    if not chapters or not chapter_name:
        return ""
    try:
        idx = int(chapter_name.split(" ")[1]) - 1
    except Exception:
        return ""
    return chapters[idx] if 0 <= idx < len(chapters) else ""


def format_transition_block(transition: Optional[Dict[str, Any]], chapter_number: int) -> str:
    """
    Format a single transition contract as markdown for display.
    """
    if not transition:
        return ""
    
    t_type = transition.get("transition_type", "direct")
    entry = transition.get("entry_constraints", {})
    exit_p = transition.get("exit_payload", {})
    anchor = transition.get("anchor", {})
    thread = transition.get("narrative_thread", "main")
    
    lines = [f"### Chapter {chapter_number}"]
    lines.append(f"**Type:** `{t_type}` · **Thread:** `{thread}`")
    
    if t_type == "return":
        resume_from = anchor.get("resume_from_chapter")
        if resume_from:
            lines.append(f"↩️ **Continues from:** Chapter {resume_from} *(not from chapter {chapter_number - 1})*")
    elif t_type == "flashback":
        trigger = anchor.get("trigger")
        if trigger:
            lines.append(f"⏪ **Triggered by:** {trigger}")
    elif t_type == "parallel":
        lines.append("🔀 **Parallel thread** — different POV/location")
    elif t_type == "pov_switch":
        lines.append("👁️ **POV switch** — same timeline, different perspective")
    elif t_type == "time_skip":
        lines.append("⏩ **Time skip** — jumps forward in time")
    
    lines.append("")
    lines.append("**Entry:**")
    if entry.get("temporal_context"):
        lines.append(f"- 🕐 When: {entry['temporal_context']}")
    if entry.get("pov"):
        lines.append(f"- 👤 POV: {entry['pov']}")
    if entry.get("pickup_state"):
        lines.append(f"- ▶️ Start: {entry['pickup_state']}")
    
    do_not_explain = entry.get("do_not_explain", [])
    if do_not_explain:
        lines.append(f"- 🚫 Don't re-explain: {', '.join(do_not_explain)}")
    
    lines.append("")
    lines.append("**Exit:**")
    if exit_p.get("last_beat"):
        lines.append(f"- ⏹️ End: {exit_p['last_beat']}")
    
    carryover = exit_p.get("carryover_facts", [])
    if carryover:
        lines.append(f"- 📦 Carryover: {', '.join(carryover)}")
    
    open_threads = exit_p.get("open_threads", [])
    if open_threads:
        lines.append(f"- ❓ Open: {', '.join(open_threads)}")
    
    return "\n".join(lines)


def format_all_transitions(transitions: List[Dict[str, Any]]) -> str:
    """
    Format all transitions as a single markdown document for display.
    """
    if not transitions:
        return "_No transitions available_"
    
    blocks = []
    for i, transition in enumerate(transitions):
        block = format_transition_block(transition, i + 1)
        if block:
            blocks.append(block)
    
    if not blocks:
        return "_No transitions available_"
    
    header = "## 🔗 Chapter Transitions\n\n"
    return header + "\n\n---\n\n".join(blocks)
