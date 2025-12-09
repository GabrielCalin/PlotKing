import requests
from typing import List, Dict, Any

def generate_text(settings: Dict[str, Any], messages: List[Dict[str, str]], **kwargs) -> str:
    url = settings.get("url", "http://127.0.0.1:1234")
    # Ensure URL ends with /v1/chat/completions if not present, or assume user provides base URL?
    # User said: "LM Studio: endpoint (URL local)"
    # Default is http://127.0.0.1:1234.
    # LM Studio usually listens on /v1/chat/completions.
    # I should append /v1/chat/completions if the user provided root.
    
    if not url.endswith("/v1/chat/completions"):
        if url.endswith("/"):
            url += "v1/chat/completions"
        else:
            url += "/v1/chat/completions"

    model = settings.get("technical_name") or "local-model" # Fallback if empty
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": kwargs.get("temperature", 0.7),
        "max_tokens": kwargs.get("max_tokens", -1),
        "top_p": kwargs.get("top_p", 0.9),
        "stream": False
    }
    
    # Merge any other kwargs that might be relevant? 
    # For now, stick to basics.
    
    try:
        response = requests.post(url, json=payload, timeout=kwargs.get("timeout", 1200))
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        raise Exception(f"LM Studio Error: {e}")
