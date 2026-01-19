from typing import List, Dict, Any
from langchain_xai import ChatXAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


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
            reasoning_effort = kwargs.get("reasoning_effort")
            if reasoning_effort:
                llm_params["reasoning_effort"] = reasoning_effort
            max_reasoning_tokens = kwargs.get("max_reasoning_tokens")
            if max_reasoning_tokens:
                llm_params["max_reasoning_tokens"] = max_reasoning_tokens
        
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
