"""
LLM generation using fine-tuned Qwen2.5-1.5B.

Loads via MLX for Apple Silicon inference. Supports conversation
history and RAG-augmented prompting.
"""

from typing import Optional

import re

from yojana_sahayak.config import (
    HF_MODEL_MERGED, SYSTEM_PROMPT, LLM_MAX_TOKENS, LLM_TEMPERATURE,
    MAX_HISTORY_TURNS, NOISE_MARKERS,
)

# Thai, CJK, Cyrillic — none of these should appear in Hindi/English output
_FOREIGN_SCRIPT_RE = re.compile(
    r'[\u0e00-\u0e7f'   # Thai
    r'\u4e00-\u9fff'    # CJK unified ideographs
    r'\u3040-\u30ff'    # Hiragana / Katakana
    r'\u0400-\u04ff]+'  # Cyrillic
)

_SENTENCE_END = re.compile(r'(?<=[.!?।])\s')
_MAX_CHARS = 500

# Patterns that signal the model is starting to hallucinate or ramble
_HALLUCINATION_MARKERS = re.compile(
    r'(इस प्रकार[,\s]|Is prakar[,\s]|Therefore[,\s]|Thus[,\s]|'
    r'In this (way|manner)[,\s]|\n\s*\d+\.\s|\n\s*[-•]\s)',
    re.IGNORECASE,
)


def _truncate_at_noise(text: str) -> str:
    """Strip web-scraping boilerplate, foreign-script, and hallucination patterns."""
    for marker in NOISE_MARKERS:
        idx = text.find(marker)
        if idx != -1:
            text = text[:idx].rstrip(" \n\t,;:")
    match = _FOREIGN_SCRIPT_RE.search(text)
    if match:
        text = text[:match.start()].rstrip(" \n\t,;:।")
    # Cut at the first hallucination trigger (only if there's already a sentence before it)
    h_match = _HALLUCINATION_MARKERS.search(text)
    if h_match and h_match.start() > 40:
        text = text[:h_match.start()].rstrip(" \n\t,;:।")
    return text


def _clip_to_sentences(text: str, max_chars: int = _MAX_CHARS) -> str:
    """Cut text at the last complete sentence boundary within max_chars."""
    if len(text) <= max_chars:
        return text
    chunk = text[:max_chars]
    splits = list(_SENTENCE_END.finditer(chunk))
    if splits:
        cut = splits[-1].start() + 1
        return chunk[:cut].rstrip()
    return chunk.rstrip()

_model = None
_tokenizer = None


def load_model():
    """Load the fine-tuned model (downloads ~3GB on first run)."""
    global _model, _tokenizer
    if _model is not None:
        return _model, _tokenizer

    print("Loading fine-tuned Qwen2.5-1.5B (first run downloads model)...")
    from mlx_lm import load
    _model, _tokenizer = load(HF_MODEL_MERGED)
    return _model, _tokenizer


def generate(question: str, context: str = "",
             history: Optional[list] = None) -> str:
    """
    Generate an answer using the fine-tuned LLM.

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
