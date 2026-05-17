# ============================================================================
# Yojana Sahayak — Sovereign Voice Agent
# Supports: Telegram Bot (default), MCP server, Gradio demo, CLI
# ============================================================================

FROM python:3.11-slim AS base

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libsndfile1 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies — core + cloud (bot + groq, no MLX)
COPY requirements.txt .
RUN pip install --no-cache-dir \
    sentence-transformers \
    faiss-cpu \
    gtts \
    numpy \
    python-dotenv \
    groq \
    "python-telegram-bot[webhooks]" \
    "mcp[cli]"

# Application code
COPY yojana_sahayak/ yojana_sahayak/
COPY data/ data/
COPY pyproject.toml .

RUN pip install --no-cache-dir -e . --no-deps

# Pre-download embedding model during build so the container starts fast
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"

EXPOSE 8000

# Default: Telegram bot (set TELEGRAM_BOT_TOKEN + GROQ_API_KEY in env)
CMD ["python", "-m", "yojana_sahayak.bot.telegram_bot"]

# Alternative commands:
# MCP server:   docker run --env-file .env yojana-sahayak python -m yojana_sahayak.mcp.server
# Gradio demo:  docker run --env-file .env -p 7860:7860 yojana-sahayak python -m yojana_sahayak.cli --gradio
# Text query:   docker run --env-file .env yojana-sahayak python -m yojana_sahayak.cli --text "PM Kisan"
