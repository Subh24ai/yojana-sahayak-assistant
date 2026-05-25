"""
LLM generation using fine-tuned Qwen2.5-1.5B.

Loads via MLX for fully offline Apple Silicon inference.
Supports conversation history and RAG-augmented prompting.
"""

import re
from typing import Optional

from yojana_sahayak.config import (
    MLX_MODEL, SYSTEM_PROMPT, LLM_MAX_TOKENS, LLM_TEMPERATURE,
    MAX_HISTORY_TURNS, NOISE_MARKERS,
)

_FOREIGN_SCRIPT_RE = re.compile(
    r'[฀-๿'   # Thai
    r'一-鿿'    # CJK unified ideographs
    r'぀-ヿ'    # Hiragana / Katakana
    r'Ѐ-ӿ]+'  # Cyrillic
)

_SENTENCE_END = re.compile(r'(?<=[.!?।])\s')
_MAX_CHARS = 500

_HALLUCINATION_MARKERS = re.compile(
    r'(इस प्रकार[,\s]|Is prakar[,\s]|Therefore[,\s]|Thus[,\s]|'
    r'In this (way|manner)[,\s]|\n\s*\d+\.\s|\n\s*[-•]\s)',
    re.IGNORECASE,
)

_model = None
_tokenizer = None


def _truncate_at_noise(text: str) -> str:
    for marker in NOISE_MARKERS:
        idx = text.find(marker)
        if idx != -1:
            text = text[:idx].rstrip(" \n\t,;:")
    match = _FOREIGN_SCRIPT_RE.search(text)
    if match:
        text = text[:match.start()].rstrip(" \n\t,;:।")
    h_match = _HALLUCINATION_MARKERS.search(text)
    if h_match and h_match.start() > 40:
        text = text[:h_match.start()].rstrip(" \n\t,;:।")
    return _remove_repetition(text)


def _remove_repetition(text: str) -> str:
    """Detect and cut at the first repeating n-gram (catches looping output)."""
    words = text.split()
    for n in (4, 3, 2, 1):
        # +1 so the last valid window is included
        for i in range(len(words) - 2 * n + 1):
            phrase = tuple(words[i:i + n])
            if tuple(words[i + n:i + 2 * n]) == phrase:
                cut = " ".join(words[:i + n]).rstrip(" ,;:।")
                return cut
    return text


def _clip_to_sentences(text: str, max_chars: int = _MAX_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    chunk = text[:max_chars]
    splits = list(_SENTENCE_END.finditer(chunk))
    if splits:
        cut = splits[-1].start() + 1
        return chunk[:cut].rstrip()
    return chunk.rstrip()


def load_model():
    """Load Qwen2.5-1.5B-Instruct-4bit via MLX (downloads ~1 GB on first run)."""
    global _model, _tokenizer
    if _model is not None:
        return _model, _tokenizer

    print(f"Loading {MLX_MODEL} via MLX...")
    from mlx_lm import load
    _model, _tokenizer = load(MLX_MODEL)
    return _model, _tokenizer


def generate(question: str, context: str = "",
             history: Optional[list] = None) -> str:
    """
    Generate an answer using local Qwen2.5-1.5B via MLX (fully offline).

    Args:
        question: User's query (Hindi or English).
        context: RAG-retrieved context string.
        history: List of {"user": ..., "assistant": ...} dicts.

    Returns:
        Generated answer string.
    """
    from mlx_lm import generate as mlx_generate
    from mlx_lm.sample_utils import make_sampler

    model, tokenizer = load_model()

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

    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True,
    )

    sampler = make_sampler(temp=LLM_TEMPERATURE)
    response = mlx_generate(
        model, tokenizer, prompt=prompt,
        max_tokens=LLM_MAX_TOKENS, sampler=sampler, verbose=False,
    )
    cleaned = _truncate_at_noise(response.strip())
    return _clip_to_sentences(cleaned)
