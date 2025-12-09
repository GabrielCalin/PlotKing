import requests
import base64
import os
from typing import Dict, Any, Optional

def generate_image(settings: Dict[str, Any], prompt: str, **kwargs) -> str:
    url = settings.get("url", "http://127.0.0.1:7860")
    
    # Needs /sdapi/v1/txt2img
    if not url.endswith("/sdapi/v1/txt2img"):
        base_url = url.rstrip("/")
        # If user provides full path, trust it? No, user usually provides base.
        # Check if user included sdapi...
        if "sdapi" not in base_url:
             url = f"{base_url}/sdapi/v1/txt2img"
    
    # Override settings
    # "daca e empty string nu punem model deloc" for override object
    # The requirement said: "Pt specificare model in payload in root se pune "override_settings" = { "sd_model_checkpoint": "Anything-V3.0-pruned" }"
    # We use technical_name for sd_model_checkpoint
    
    payload = {
        "prompt": prompt,
        "steps": kwargs.get("steps", 20),
        "width": kwargs.get("width", 512),
        "height": kwargs.get("height", 768),
        "cfg_scale": kwargs.get("cfg_scale", 7)
    }
    
    technical_name = settings.get("technical_name")
    if technical_name:
        payload["override_settings"] = {
            "sd_model_checkpoint": technical_name
        }
        
    try:
        response = requests.post(url, json=payload, timeout=kwargs.get("timeout", 1200))
        response.raise_for_status()
        r = response.json()
        image_b64 = r['images'][0]
        
        # Save to tmp
        tmp_dir = "tmp"
        os.makedirs(tmp_dir, exist_ok=True)
        # Unique name or overwrite? Overwrite cover.png is fine for now/consistent with previous behavior
        # But maybe we want unique to avoid caching issues?
        # User requirement didn't specify, but `export_handlers` reused `cover.png`.
        # I'll use a timestamp or uuid to be safe? 
        # Actually export_handlers used `cover.png`. I'll stick to that or `generated_cover.png`.
        
        output_path = os.path.join(tmp_dir, "cover.png")
        
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(image_b64))
            
        return os.path.abspath(output_path)
            
    except Exception as e:
        raise Exception(f"Automatic1111 Error: {e}")
