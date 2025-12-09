import requests
import os
import base64
from typing import List, Dict, Any

def generate_text(settings: Dict[str, Any], messages: List[Dict[str, str]], **kwargs) -> str:
    api_key = settings.get("api_key")
    if not api_key:
        raise ValueError("OpenAI API Key is missing.")
        
    model = settings.get("technical_name") or "gpt-4o" # Default if empty? Or gpt-3.5-turbo
    
    url = "https://api.openai.com/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": kwargs.get("temperature", 0.7),
        "max_tokens": kwargs.get("max_tokens", 4000), # Default max tokens
        "top_p": kwargs.get("top_p", 1.0),
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=kwargs.get("timeout", 60))
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        raise Exception(f"OpenAI Text Error: {e}")


def generate_image(settings: Dict[str, Any], prompt: str, **kwargs) -> str:
    api_key = settings.get("api_key")
    if not api_key:
        raise ValueError("OpenAI API Key is missing.")
        
    model = settings.get("technical_name") or "dall-e-3"
    
    url = "https://api.openai.com/v1/images/generations"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # OpenAI size must be supported. DALL-E 3 supports 1024x1024, 1024x1792, etc.
    # Our app requests 512x768 usually via kwargs (width, height).
    
    width = kwargs.get("width")
    height = kwargs.get("height")
    
    if width and height:
        size = f"{width}x{height}"
    else:
        # Defaults if not provided
        size = "1024x1024" # Safe default for DALL-E 3
        if "dall-e-2" in model:
            size = "512x512" 
    
    payload = {
        "model": model,
        "prompt": prompt,
        "n": 1,
        "size": size,
        "response_format": "b64_json" # Get b64 to save locally matches our flow
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=kwargs.get("timeout", 60))
        response.raise_for_status()
        data = response.json()
        image_b64 = data["data"][0]["b64_json"]
        
        tmp_dir = "tmp"
        os.makedirs(tmp_dir, exist_ok=True)
        output_path = os.path.join(tmp_dir, "cover.png")
        
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(image_b64))
            
        return os.path.abspath(output_path)
        
    except Exception as e:
        raise Exception(f"OpenAI Image Error: {e}")
