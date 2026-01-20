from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


def convert_reasoning_effort(value: str) -> Optional[str]:
    """Convert UI reasoning effort values to OpenRouter-compatible values.
    
    OpenRouter accepts: 'none', 'minimal', 'low', 'medium', 'high', 'xhigh'
    See: https://openrouter.ai/docs/guides/best-practices/reasoning-tokens#reasoning-effort-level
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
        raise ValueError("OpenRouter API Key is missing.")
        
    model = settings.get("technical_name") or "openai/gpt-4o"
    reasoning = settings.get("reasoning", False)
    
    try:
        llm_params = {
            "api_key": api_key,
            "base_url": "https://openrouter.ai/api/v1",
            "model": model,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4000),
            "timeout": kwargs.get("timeout", 60)
        }
        
        if reasoning:
            reasoning_config = {}
            
            reasoning_effort_raw = kwargs.get("reasoning_effort")
            if reasoning_effort_raw:
                reasoning_effort = convert_reasoning_effort(reasoning_effort_raw)
                if reasoning_effort:
                    reasoning_config["effort"] = reasoning_effort
            
            max_reasoning_tokens = kwargs.get("max_reasoning_tokens")
            if max_reasoning_tokens:
                reasoning_config["max_tokens"] = max_reasoning_tokens
            
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
        elif isinstance(content, list):
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
        raise Exception(f"OpenRouter Text Error (LangChain): {e}")
