# -*- coding: utf-8 -*-
# utils/json_utils.py
"""
Utilitare pentru deserializarea JSON din răspunsurile LLM.
"""

import json
import re


def extract_json_from_response(content: str) -> dict:
    """
    Extrage JSON-ul din răspuns, suportând atât formatul pur cât și cel wrappat în tag-uri speciale.
    
    Suportă formate precum:
    - JSON pur: {"key": "value"}
    - Wrappat în tag-uri: <|channel|>final <|constrain|>JSON<|message|>{"key": "value"}
    
    Args:
        content: Conținutul răspunsului de la LLM
        
    Returns:
        dict: Obiectul JSON parsat
        
    Raises:
        ValueError: Dacă nu se poate extrage JSON valid din răspuns
    """
    content = content.strip()
    
    # Încearcă să parseze direct JSON-ul
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # Elimină tag-urile speciale comune (gpt-oss format)
    cleaned = re.sub(r'<\|[^|]+\|>', '', content)
    cleaned = cleaned.strip()
    
    # Încearcă din nou după eliminarea tag-urilor
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # Caută primul { și ultimul } pentru a extrage blocul JSON
    start_idx = content.find('{')
    end_idx = content.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_str = content[start_idx:end_idx + 1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    # Dacă tot nu reușește, aruncă excepție
    raise ValueError(f"Could not extract valid JSON from response: {content[:200]}...")

