"""
Automatic Speech Recognition using Whisper MLX.

Optimized for Hindi speech on Apple Silicon. Runs fully offline
once the model is cached (~800MB download on first run).

Benchmarks (Apple M4 Air):
    - WER: 24% on Hindi scheme queries
    - RTF: 0.37 (2.7× faster than real-time)
"""

import re
import time
import tempfile
from pathlib import Path
from typing import Optional

from yojana_sahayak.config import (
    WHISPER_MODEL, SAMPLE_RATE, RECORD_DURATION_SEC, ASR_CORRECTIONS,
)


def transcribe(audio_path: str, language: str = "hi") -> dict:
    """
    Transcribe an audio file using Whisper.

    Tries MLX Whisper (Apple Silicon, local) first; falls back to Groq Whisper
    API when mlx_whisper is not installed and GROQ_API_KEY is set.

    Args:
        audio_path: Path to audio file (WAV preferred for MLX, any format for Groq).
        language: ISO language code ('hi' for Hindi).

    Returns:
        dict with 'text', 'latency_s', and optionally 'rtf'.
    """
    import os
    try:
        import mlx_whisper
    except ImportError:
        if os.environ.get("GROQ_API_KEY"):
            from yojana_sahayak.asr.groq_asr import transcribe as groq_transcribe
            return groq_transcribe(audio_path, language)
        raise ImportError(
            "mlx_whisper not installed. Run: pip install mlx-whisper\n"
            "Or set GROQ_API_KEY to use the Groq Whisper API instead."
        )

    start = time.time()
    result = mlx_whisper.transcribe(
        audio_path,
        path_or_hf_repo=WHISPER_MODEL,
        language=language,
        task="transcribe",
        word_timestamps=False,
    )
    elapsed = time.time() - start

    return {
        "text": result["text"].strip(),
        "latency_s": round(elapsed, 3),
        "rtf": round(elapsed / RECORD_DURATION_SEC, 4),
    }


def rewrite_query(text: str) -> str:
    """
    Apply ASR correction dictionary to fix common Whisper errors
    on Indian scheme names (Devanagari and Roman).

    Examples:
        'आइसमान भारत' → 'आयुष्मान भारत'
        'pm kisaan'     → 'PM Kisan'
    """
    for wrong, correct in ASR_CORRECTIONS.items():
        text = re.sub(wrong, correct, text, flags=re.IGNORECASE)
    return text.strip()


def record_mic(duration: int = RECORD_DURATION_SEC) -> str:
    """
    Record audio from the default microphone.

    Returns:
        Path to a temporary WAV file.
    """
    import sounddevice as sd
    from scipy.io import wavfile
    import numpy as np

    print(f"  Recording {duration}s... SPEAK NOW")
    audio = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
    )
    sd.wait()
    print("  ✓ Recording done")

    audio_int16 = (audio * 32767).astype("int16")
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    wavfile.write(tmp.name, SAMPLE_RATE, audio_int16)
    return tmp.name
