# -*- coding: utf-8 -*-
# llm/overview_tokenizer/llm.py

import json
import re
import textwrap
from typing import List, Dict, Any
from provider import provider_manager
from state.settings_manager import settings_manager


PROMPT_TEMPLATE = textwrap.dedent("""
You are a text structure analyzer.

Your task is to identify the starting line of each chapter in a chapters overview document.
The document has been pre-processed so that each line starts with a line number in brackets, like [1], [2], etc.

Instructions:
1. Analyze the provided text and identify where each chapter begins.
2. Chapters typically start with a heading like "#### Chapter 1: *Title*" or similar patterns.
3. Return a JSON array where each element contains:
   - "chapter": the chapter number (integer)
   - "line_index": the line number where that chapter starts (the number inside the brackets)
4. The array must be sorted by chapter number.
5. If you cannot identify exactly {num_chapters} chapters, return an empty JSON array: []
6. Return ONLY the JSON array, no other text.

---

### Example Input:
```
[1]#### Chapter 1: *The Beginning*
[2]**Description:** This chapter introduces the main character.
[3]The story opens in a small village where our hero lives.
[4]
[5]#### Chapter 2: *The Journey*
[6]**Description:** The hero embarks on their adventure.
[7]After receiving a mysterious letter, the hero decides to leave home.
```

### Example Output (for num_chapters=2):
```json
[
  {{"chapter": 1, "line_index": 1}},
  {{"chapter": 2, "line_index": 5}}
]
```

---

### Your Input:
Number of chapters to find: {num_chapters}

Document:
```
{prefixed_overview}
```

Return ONLY the JSON array:
""")


def _prefix_lines(text: str) -> str:
    """Prefix each line with [line_number] starting from 1."""
    lines = text.split('\n')
    return '\n'.join(f"[{i+1}]{line}" for i, line in enumerate(lines))


def _parse_json_response(content: str) -> List[Dict[str, Any]]:
    """Extract and parse JSON array from LLM response."""
    content = content.strip()
    
    json_match = re.search(r'\[[\s\S]*\]', content)
    if not json_match:
        return []
    
    try:
        result = json.loads(json_match.group())
        if not isinstance(result, list):
            return []
        for item in result:
            if not isinstance(item, dict):
                return []
            if "chapter" not in item or "line_index" not in item:
                return []
        return result
    except json.JSONDecodeError:
        return []


def call_llm_tokenize_overview(
    chapters_overview: str,
    num_chapters: int,
) -> List[Dict[str, int]]:
    """
    Use LLM to identify chapter boundaries in the overview.
    
    Returns:
        List of dicts with "chapter" and "line_index" keys, sorted by chapter.
        Returns empty list if tokenization fails or doesn't find exactly num_chapters.
    """
    prefixed_overview = _prefix_lines(chapters_overview)
    
    prompt = PROMPT_TEMPLATE.format(
        num_chapters=num_chapters,
        prefixed_overview=prefixed_overview
    )
    
    messages = [
        {"role": "system", "content": "You are a precise text structure analyzer. Return only valid JSON."},
        {"role": "user", "content": prompt},
    ]
    
    task_params = settings_manager.get_task_params("overview_tokenizer")
    retries = task_params.get("retries", 3)
    if retries is None:
        retries = 3
    retries = max(0, int(retries))
    
    for attempt in range(retries + 1):
        try:
            content = provider_manager.get_llm_response(
                task_name="overview_tokenizer",
                messages=messages
            )
            
            result = _parse_json_response(content)
            
            if len(result) == num_chapters:
                result.sort(key=lambda x: x["chapter"])
                return result
                
        except Exception:
            if attempt < retries:
                continue
            return []
    
    return []


