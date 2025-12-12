from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

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
    
    try:
        llm = ChatOpenAI(
            base_url=clean_url,
            api_key="lm-studio", # Dummy key required
            model=model,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", -1),
            request_timeout=kwargs.get("timeout", 1200),
            top_p=kwargs.get("top_p", 0.9)
        )
        
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
