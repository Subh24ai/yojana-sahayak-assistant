"""
ASR via Groq Whisper API (cloud).

Accepts OGG, WAV, MP3 and most audio formats directly — no conversion needed.
Significantly faster than real-time. Used when GROQ_API_KEY is set.
"""

import os
import time
from pathlib import Path

from yojana_sahayak.config import GROQ_WHISPER_MODEL


def transcribe(audio_path: str, language: str = "hi") -> dict:
    """
    Transcribe audio using Groq Whisper API.

    Args:
        audio_path: Path to audio file (OGG, WAV, MP3, etc.)
        language: ISO code ('hi' for Hindi, None for auto-detect).

    Returns:
        dict with 'text' and 'latency_s'.
    """
    from groq import Groq

    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    start = time.time()
    with open(audio_path, "rb") as f:
        result = client.audio.transcriptions.create(
            file=(Path(audio_path).name, f),
            model=GROQ_WHISPER_MODEL,
            language=language,
            response_format="text",
        )
    elapsed = time.time() - start

    text = result.strip() if isinstance(result, str) else result.text.strip()
    return {"text": text, "latency_s": round(elapsed, 3)}
