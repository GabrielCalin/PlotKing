from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


def convert_reasoning_effort(value: str) -> Optional[str]:
    """Convert UI reasoning effort values to LM Studio-compatible values.
    
    LM Studio uses OpenAI-compatible API, accepts: 'none', 'minimal', 'low', 'medium', 'high', 'xhigh'
    For newer reasoning models, 'xhigh' is supported.
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
    url = settings.get("url", "http://127.0.0.1:1234")
    
    # Clean URL for ChatOpenAI compatibility
    # ChatOpenAI expects base_url like "http://localhost:1234/v1"
    # If user provided default "http://127.0.0.1:1234", append "/v1"
    # If user provided ".../v1/chat/completions", strip "/chat/completions"
    
    clean_url = url.strip().rstrip("/")
    if clean_url.endswith("/chat/completions"):
        clean_url = clean_url.replace("/chat/completions", "")
    
    if not clean_url.endswith("/v1"):
        clean_url = f"{clean_url}/v1"

    model = settings.get("technical_name") or "local-model" 
    reasoning = settings.get("reasoning", False)
    
    try:
        llm_params = {
            "base_url": clean_url,
            "api_key": "lm-studio", # Dummy key required
            "model": model,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", -1),
            "request_timeout": kwargs.get("timeout", 1200),
            "top_p": kwargs.get("top_p", 0.9)
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
        return response.content

    except Exception as e:
        raise Exception(f"LM Studio Error (LangChain): {e}")
