from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


def convert_reasoning_effort(value: str) -> Optional[str]:
    """Convert UI reasoning effort values to Gemini thinking_level values.
    
    Gemini 3+ accepts only: 'low' or 'high'
    See: https://ai.google.dev/gemini/docs/reasoning
    """
    if not value or value == "Not Set":
        return None
    
    mapping = {
        "Very High": "high",
        "High": "high",
        "Medium": "high",
        "Low": "low",
        "Minimal": "low",
        "None": None
    }
    result = mapping.get(value)
    return result if result is not None else value.lower()


def generate_text(settings: Dict[str, Any], messages: List[Dict[str, str]], **kwargs) -> str:
    api_key = settings.get("api_key")
    if not api_key:
        raise ValueError("Gemini API Key is missing.")
        
    model = settings.get("technical_name") or "gemini-pro"
    reasoning = settings.get("reasoning", False)
    
    try:
        llm_params = {
            "google_api_key": api_key,
            "model": model,
            "temperature": kwargs.get("temperature", 0.7),
            "max_output_tokens": kwargs.get("max_tokens", 4000),
            "timeout": kwargs.get("timeout", 60)
        }
        
        if reasoning:
            reasoning_effort_raw = kwargs.get("reasoning_effort")
            if reasoning_effort_raw:
                thinking_level = convert_reasoning_effort(reasoning_effort_raw)
                if thinking_level:
                    llm_params["thinking_level"] = thinking_level
            
            max_reasoning_tokens = kwargs.get("max_reasoning_tokens")
            if max_reasoning_tokens:
                llm_params["thinking_budget"] = max_reasoning_tokens
        
        llm = ChatGoogleGenerativeAI(**llm_params)
        
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
        
        if hasattr(response, 'content'):
            content = response.content
            if isinstance(content, list):
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and 'text' in part:
                        text_parts.append(part['text'])
                    elif isinstance(part, str):
                        text_parts.append(part)
                return ''.join(text_parts)
            return str(content)
        else:
            return str(response)
        
    except Exception as e:
        raise Exception(f"Gemini Text Error (LangChain): {e}")
