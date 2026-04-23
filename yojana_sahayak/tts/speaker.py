"""
Text-to-Speech for Hindi and English output.

Uses gTTS (Google Text-to-Speech) by default, with AI4Bharat
as a fallback for higher-quality Indic voices.
"""

import tempfile
import re
from pathlib import Path
from typing import Optional


def detect_language(text: str) -> str:
    """Detect if text is primarily Hindi (Devanagari) or English."""
    devanagari = len(re.findall(r'[\u0900-\u097F]', text))
    total = max(len(text.split()), 1)
    return "hi" if devanagari > total * 0.3 else "en"


def synthesize(text: str, lang: Optional[str] = None,
               output_path: Optional[str] = None) -> str:
    """
    Convert text to speech audio.

    Args:
        text: Text to speak.
        lang: Language code ('hi' or 'en'). Auto-detected if None.
        output_path: Path for output file. Temp file if None.

    Returns:
        Path to the generated audio file (MP3).
    """
    from gtts import gTTS

    if lang is None:
        lang = detect_language(text)

    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        output_path = tmp.name

    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(output_path)
    return output_path


def play(audio_path: str) -> None:
    """Play an audio file through the default speakers."""
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
    except ImportError:
        import subprocess
        import sys
        if sys.platform == "darwin":
            subprocess.run(["afplay", audio_path], check=False)
        else:
            print(f"Audio saved to {audio_path} (install pygame for playback)")

