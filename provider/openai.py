import os
import base64
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from openai import OpenAI


def convert_reasoning_effort(value: str) -> Optional[str]:
    """Convert UI reasoning effort values to OpenAI-compatible values.
    
    OpenAI accepts: 'none', 'minimal', 'low', 'medium', 'high'
    For newer models (o1-series, o3-series, GPT-5-series), 'xhigh' is also supported.
    """
    if not value or value == "Not Set":
        return None
    
    mapping = {
        "Very High": "xhigh",
        "High": "high",
        "Medium": "medium",
        "Low": "low",
        "Minimal": "minimal",
        "None": "none"
    }
    return mapping.get(value, value.lower())


def generate_text(settings: Dict[str, Any], messages: List[Dict[str, str]], **kwargs) -> str:
    api_key = settings.get("api_key")
    if not api_key:
        raise ValueError("OpenAI API Key is missing.")
        
    model = settings.get("technical_name") or "gpt-4o"
    reasoning = settings.get("reasoning", False)
    
    try:
        llm_params = {
            "api_key": api_key,
            "model": model,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4000),
            "request_timeout": kwargs.get("timeout", 60)
        }
        
        if reasoning:
            reasoning_config = {}
            
            reasoning_effort_raw = kwargs.get("reasoning_effort")
            if reasoning_effort_raw:
                reasoning_effort = convert_reasoning_effort(reasoning_effort_raw)
                if reasoning_effort:
                    reasoning_config["effort"] = reasoning_effort
            
            if reasoning_config:
                llm_params["reasoning"] = reasoning_config
        
        llm = ChatOpenAI(**llm_params)
        
        lc_messages = []
        for m in messages:
            role = m.get("role")
            content = m.get("content")
            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            else:
                lc_messages.append(HumanMessage(content=content))
                
        response = llm.invoke(lc_messages)
        content = response.content
        
        if isinstance(content, str):
            return content
        elif hasattr(content, '__iter__') and not isinstance(content, (str, bytes)):
            parts = []
            for part in content:
                if isinstance(part, str):
                    parts.append(part)
                elif isinstance(part, dict):
                    if 'text' in part:
                        parts.append(str(part['text']))
                    elif 'type' in part and part.get('type') == 'text':
                        parts.append(str(part.get('text', '')))
            return ''.join(parts) if parts else str(content)
        else:
            return str(content)
        
    except Exception as e:
        raise Exception(f"OpenAI Text Error (LangChain): {e}")


def generate_image(settings: Dict[str, Any], prompt: str, **kwargs) -> str:
    api_key = settings.get("api_key")
    if not api_key:
        raise ValueError("OpenAI API Key is missing.")

    model = settings.get("technical_name") or "gpt-image-1"

    width = kwargs.get("width")
    height = kwargs.get("height")
    size = f"{width}x{height}" if width and height else "1024x1024"

    try:
        client = OpenAI(api_key=api_key)

        response = client.images.generate(
            model=model,
            prompt=prompt,
            size=size,
            n=1
        )

        img_b64 = response.data[0].b64_json

        os.makedirs("tmp", exist_ok=True)
        output_path = os.path.join("tmp", "cover.png")

        with open(output_path, "wb") as f:
            f.write(base64.b64decode(img_b64))

        return os.path.abspath(output_path)

    except Exception as e:
        raise Exception(f"OpenAI Image Error: {e}")
