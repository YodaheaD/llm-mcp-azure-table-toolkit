# llm.py
import requests
from typing import List, Dict

LM_SERVER_URL = "http://localhost:8000/v1/chat/completions"


def _clean_assistant_output(text: str) -> str:
    """
    Ensures only the FIRST assistant message is returned.
    Removes any extra chat-template continuations.
    """
    if "<|assistant|>" in text:
        text = text.split("<|assistant|>", 1)[0]

    return text.strip()


def call_llm(
    messages: List[Dict[str, str]],
    temperature: float = 0.2,
) -> str:
    payload = {
        "model": "local-llama",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 256,
    }

    resp = requests.post(LM_SERVER_URL, json=payload)
    resp.raise_for_status()

    data = resp.json()
    raw = data["choices"][0]["message"]["content"]
    return _clean_assistant_output(raw)
