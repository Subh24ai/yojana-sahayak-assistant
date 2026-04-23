# ============================================================================
# Yojana Sahayak — Sovereign Voice Agent
# Air-gapped, on-premise deployment. Zero internet dependency at runtime.
# ============================================================================

FROM python:3.11-slim AS base

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libsndfile1 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY yojana_sahayak/ yojana_sahayak/
COPY data/ data/
COPY pyproject.toml .

# Pre-download models during build (so runtime needs zero internet)
# Uncomment these for fully air-gapped deployment:
# RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"
# RUN python -c "from yojana_sahayak.rag.retriever import SchemeRetriever; r = SchemeRetriever(); r.build_index()"

EXPOSE 8000

# Default: run MCP server (stdio transport)
ENTRYPOINT ["python", "-m", "yojana_sahayak.mcp.server"]

# Alternative commands:
# MCP server:    docker run yojana-sahayak
# Text query:    docker run yojana-sahayak python -m yojana_sahayak.cli --text "PM Kisan eligibility"
# Gradio demo:   docker run -p 7860:7860 yojana-sahayak python -m yojana_sahayak.cli --gradio
