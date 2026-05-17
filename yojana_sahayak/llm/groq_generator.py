"""
LLM generation via Groq API.

Used when GROQ_API_KEY is set — works on any machine, no Apple Silicon needed.
Model: llama-3.1-8b-instant (fast, Hindi-capable, free-tier friendly).
"""

import os
from typing import Optional

from yojana_sahayak.config import (
    GROQ_MODEL, SYSTEM_PROMPT, LLM_MAX_TOKENS, LLM_TEMPERATURE, MAX_HISTORY_TURNS,
)

_client = None


def _get_client():
    global _client
    if _client is None:
        from groq import Groq
        _client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    return _client


def generate(question: str, context: str = "",
             history: Optional[list] = None) -> str:
    """
    Generate an answer using Groq API.

    Args:
        question: User's query (Hindi or English).
        context: RAG-retrieved context string.
        history: List of {"user": ..., "assistant": ...} dicts.

    Returns:
        Generated answer string.
    """
    client = _get_client()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if history:
        for turn in history[-MAX_HISTORY_TURNS:]:
            messages.append({"role": "user", "content": turn["user"]})
            messages.append({"role": "assistant", "content": turn["assistant"]})

    if context:
        augmented = (
            f"Reference:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer ONLY using the reference above. "
            "Be direct and brief — answer exactly what was asked, nothing more."
        )
        messages.append({"role": "user", "content": augmented})
    else:
        messages.append({"role": "user", "content": question})

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        max_tokens=LLM_MAX_TOKENS,
        temperature=LLM_TEMPERATURE,
    )
    return response.choices[0].message.content.strip()
