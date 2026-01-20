from typing import List, Dict, Any, Optional
from langchain_xai import ChatXAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


def convert_reasoning_effort(value: str) -> Optional[str]:
    """Convert UI reasoning effort values to xAI-compatible values.
    
    xAI Grok accepts: 'low', 'medium', 'high'
    """
    if not value or value == "Not Set":
        return None
    
    mapping = {
        "Very High": "high",
        "High": "high",
        "Medium": "medium",
        "Low": "low",
        "Minimal": "low",
        "None": None
    }
    result = mapping.get(value)
    return result if result is not None else value.lower()


def generate_text(settings: Dict[str, Any], messages: List[Dict[str, str]], **kwargs) -> str:
    api_key = settings.get("api_key")
    if not api_key:
        raise ValueError("xAI API Key is missing.")
        
    model = settings.get("technical_name") or "grok-beta"
    reasoning = settings.get("reasoning", False)
    
    try:
        llm_params = {
            "xai_api_key": api_key,
            "model": model,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4000),
            "timeout": kwargs.get("timeout", 60)
        }
        
        if reasoning:
            reasoning_effort_raw = kwargs.get("reasoning_effort")
            if reasoning_effort_raw:
                reasoning_effort = convert_reasoning_effort(reasoning_effort_raw)
                if reasoning_effort:
                    llm_params["reasoning_effort"] = reasoning_effort
        
        llm = ChatXAI(**llm_params)
        
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
        return response.content
        
    except Exception as e:
        raise Exception(f"xAI Text Error (LangChain): {e}")
