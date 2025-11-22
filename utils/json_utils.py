# -*- coding: utf-8 -*-
# utils/json_utils.py
"""
Utilitare pentru deserializarea JSON din răspunsurile LLM.
"""

import json
import re
import json_repair


def extract_json_from_response(content: str) -> dict:
    """
    Extrage JSON-ul din răspuns, suportând atât formatul pur cât și cel wrappat în tag-uri speciale.
    Folosește json-repair pentru a repara erorile comune (ex. triple quotes, newlines neescapate).
    
    Args:
        content: Conținutul răspunsului de la LLM
        
    Returns:
        dict: Obiectul JSON parsat
        
    Raises:
        ValueError: Dacă nu se poate extrage JSON valid din răspuns
    """
    content = content.strip()
    
    # 1. Încearcă să parseze direct JSON-ul (cel mai rapid și corect)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # 2. Elimină tag-urile speciale comune (gpt-oss format) și încearcă din nou
    # Suportă formate precum: <|channel|>final <|constrain|>JSON<|message|>{"key": "value"}
    cleaned = re.sub(r'<\|[^|]+\|>', '', content).strip()
    if cleaned != content:
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
    
    # 3. Folosește json_repair pentru a repara și extrage JSON-ul
    # Această librărie gestionează automat triple quotes, tag-uri din jurul JSON-ului, etc.
    try:
        decoded = json_repair.repair_json(content, return_objects=True)
        if isinstance(decoded, dict):
            return decoded
        elif isinstance(decoded, list) and len(decoded) > 0 and isinstance(decoded[0], dict):
            # Dacă a returnat o listă, returnăm primul element dacă e dict
            return decoded[0]
    except Exception:
        pass
    
    # 3. Fallback manual pentru cazuri extreme (deși json_repair ar trebui să acopere majoritatea)
    # Caută primul { și ultimul }
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

