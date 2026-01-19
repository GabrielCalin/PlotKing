import os
import base64
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from openai import OpenAI


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
            reasoning_effort = kwargs.get("reasoning_effort", "medium")
            if reasoning_effort:
                llm_params["reasoning_effort"] = reasoning_effort
        
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
