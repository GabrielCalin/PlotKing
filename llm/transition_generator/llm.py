# -*- coding: utf-8 -*-
# llm/transition_generator/llm.py

import json
import re
import textwrap
from typing import List, Dict, Any, Optional
from provider import provider_manager
from state.settings_manager import settings_manager


TRANSITION_PROMPT = textwrap.dedent("""
You are a **narrative continuity architect** for novel writing.

Your task: Analyze the chapters overview and generate a **transition contract** for each chapter.

---

## TRANSITION TYPES

| Type | When to use |
|------|-------------|
| `direct` | Chapter continues from the previous one linearly |
| `flashback` | Jumps to past events, different time period |
| `parallel` | Switches to different character/location in same timeframe |
| `return` | Returns to main thread after flashback/parallel |
| `pov_switch` | Same timeline, different character's perspective |
| `time_skip` | Jumps forward in time within same thread |

---

## DETECTION RULES

Mark as NON-direct if ANY of these are true:
- Different time period than previous chapter
- Different POV character with their own storyline
- Explicitly labeled as flashback/memory/parallel in overview
- Chapter returns to a character/situation from an earlier chapter (not the immediately previous one)

For `return` type:
- Identify which earlier chapter this continues from
- That chapter's exit state becomes this chapter's entry context

---

## OUTPUT FORMAT

For each chapter, output JSON with this structure:

```json
{{
  "chapter": <number>,
  "transition_type": "<direct|flashback|parallel|return|pov_switch|time_skip>",
  "narrative_thread": "<thread_id>",
  
  "anchor": {{
    "from_chapter": <number or null>,
    "resume_from_chapter": <number or null>,
    "trigger": "<what causes the transition, or null>"
  }},
  
  "entry_constraints": {{
    "temporal_context": "<when this chapter takes place>",
    "pov": "<main character of this chapter>",
    "pickup_state": "<concrete starting situation>",
    "do_not_explain": ["<fact 1>", "<fact 2>"]
  }},
  
  "exit_payload": {{
    "last_beat": "<specific final image/moment>",
    "carryover_facts": ["<new fact 1>", "<new fact 2>"],
    "open_threads": ["<question/tension 1>"],
    "thematic_echo": "<optional thematic link or null>"
  }},
  
  "characters": {{
    "new": ["<character_id_1>", "<character_id_2>"]
  }},
  
  "return_point": {{
    "thread": "<thread_id>",
    "resume_from_chapter": <number>
  }}
}}
```

Note: `return_point` should be `null` for `direct` type chapters.

---

## RULES

1. **Be factual, not emotional** - describe what happens, not how reader feels
2. **`last_beat` must be concrete** - a specific image, action, or line, not a summary
3. **`do_not_explain` prevents redundancy** - if a fact was established in previous chapters, don't repeat it
4. **`carryover_facts` are NEW information** - things established in this chapter that future chapters should know
5. **Chapter 1 has `anchor.from_chapter: null`** - it's the starting point
6. **Every non-direct transition needs proper `anchor`** - specify where it comes from or resumes
7. **`narrative_thread` should be consistent** - same ID for same storyline across chapters (e.g., "main", "backstory_maria", "parallel_detective")
8. **`characters.new`** - list ALL character IDs that appear in this chapter that are NEW TO THE READER:
   - **For Chapter 1:** ALL characters that appear are "new" — include ALL of them in the list.
   - **For later chapters:** Only characters appearing for the FIRST TIME in the story (not seen in previous chapters).
   - These characters must be introduced naturally, not just named.
9. **Exit of chapter N aligns with entry of chapter N+1** for direct continuations

---

## INPUT

Expanded Plot Summary:
\"\"\"{expanded_plot}\"\"\"

Chapters Overview:
\"\"\"{chapters_overview}\"\"\"

Number of chapters: {num_chapters}

---

Output a JSON array with exactly {num_chapters} transition objects, one per chapter.
Return ONLY valid JSON array, no other text or markdown formatting.
""").strip()


def _parse_json_response(content: str) -> List[Dict[str, Any]]:
    content = content.strip()
    
    if content.startswith("```"):
        lines = content.split("\n")
        start_idx = 1 if lines[0].startswith("```") else 0
        end_idx = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == "```":
                end_idx = i
                break
        content = "\n".join(lines[start_idx:end_idx])
    
    json_match = re.search(r'\[[\s\S]*\]', content)
    if not json_match:
        return []
    
    try:
        result = json.loads(json_match.group())
        if not isinstance(result, list):
            return []
        return result
    except json.JSONDecodeError:
        return []


def _validate_transition(transition: Dict[str, Any], chapter_num: int) -> bool:
    if not isinstance(transition, dict):
        return False
    if transition.get("chapter") != chapter_num:
        return False
    if "transition_type" not in transition:
        return False
    if "entry_constraints" not in transition:
        return False
    if "exit_payload" not in transition:
        return False
    return True


def call_llm_generate_transitions(
    expanded_plot: str,
    chapters_overview: str,
    num_chapters: int,
) -> List[Dict[str, Any]]:
    """
    Generate transition contracts for all chapters.
    
    Returns:
        List of transition dicts, one per chapter.
        Returns empty list if generation fails after all retries.
    """
    prompt = TRANSITION_PROMPT.format(
        expanded_plot=expanded_plot or "",
        chapters_overview=chapters_overview or "",
        num_chapters=num_chapters
    )
    
    messages = [
        {"role": "system", "content": "You are a narrative structure analyzer. Return only valid JSON."},
        {"role": "user", "content": prompt},
    ]
    
    task_params = settings_manager.get_task_params("transition_generator")
    retries = task_params.get("retries", 3)
    if retries is None:
        retries = 3
    retries = max(0, int(retries))
    
    for attempt in range(retries + 1):
        try:
            content = provider_manager.get_llm_response(
                task_name="transition_generator",
                messages=messages
            )
            
            transitions = _parse_json_response(content)
            
            if len(transitions) != num_chapters:
                if attempt < retries:
                    continue
                return []
            
            all_valid = True
            for i, transition in enumerate(transitions):
                if not _validate_transition(transition, i + 1):
                    all_valid = False
                    break
            
            if all_valid:
                return transitions
            
            if attempt < retries:
                continue
            return []
            
        except Exception:
            if attempt < retries:
                continue
            return []
    
    return []

