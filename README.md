# 🇮🇳 Yojana Sahayak — Sovereign Voice Agent for Indian Government Schemes

A **fully offline, multilingual voice AI system** with MCP tool-calling that helps Indian citizens discover and understand government welfare schemes in Hindi and English.

**Designed for air-gapped, on-premise deployment. Zero internet dependency at runtime.**

```
Hindi Voice ──→ Whisper ASR ──→ Query Rewrite ──→ RAG (FAISS) ──→ Fine-tuned Qwen2.5 ──→ TTS ──→ Hindi Voice
                                                       ↑
                                              MCP Server (stdio)
                                          ┌──────────┴──────────┐
                                          │  search_schemes     │
                                          │  get_scheme_details │
                                          │  check_eligibility  │
                                          │  list_schemes       │
                                          └─────────────────────┘
```

## Why This Exists

600M+ Indians are eligible for government welfare schemes but can't navigate them — language barriers, digital literacy gaps, and bureaucratic complexity. Yojana Sahayak is a voice-first AI agent that speaks Hindi, runs without internet, and can be deployed inside government offices, CSC centers, or air-gapped data centers.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        YOJANA SAHAYAK                                │
│                                                                      │
│  ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐          │
│  │  ASR    │──→│  Query   │──→│   RAG    │──→│   LLM    │──→ TTS   │
│  │ Whisper │   │ Rewrite  │   │  FAISS   │   │  Qwen2.5 │          │
│  │ MLX    │   │ ASR Fix  │   │ MiniLM   │   │  QLoRA   │          │
│  └─────────┘   └──────────┘   └────┬─────┘   └──────────┘          │
│                                     │                                │
│                              ┌──────┴──────┐                        │
│                              │ MCP Server  │ ← stdio (no network)   │
│                              │ 4 tools     │                        │
│                              │ 591+ facts  │                        │
│                              └─────────────┘                        │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │  Data: 39,957 bilingual QA pairs · 2,872 schemes          │     │
│  │  Model: Qwen2.5-1.5B QLoRA (perplexity 1.15)              │     │
│  │  ASR: Whisper large-v3-turbo (24% WER Hindi, RTF 0.37)    │     │
│  └─────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────┘
```

## Benchmarks

| Component | Metric | Value | Hardware |
|-----------|--------|-------|----------|
| ASR (Whisper MLX) | WER (Hindi) | **24%** | Apple M4 Air |
| ASR (Whisper MLX) | RTF | **0.37** (2.7× real-time) | Apple M4 Air |
| LLM (QLoRA) | Perplexity | **1.15** | Kaggle T4 (54 min train) |
| LLM (QLoRA) | Eval Loss | **0.2076** | — |
| RAG (FAISS) | Index size | **591 facts** | — |
| Dataset | Total pairs | **39,957** (EN + HI) | — |
| Dataset | Schemes covered | **2,872** | myscheme.gov.in |
| E2E Pipeline | Latency | **~12s** (CPU-only) | Apple M4 Air |

## Quick Start

```bash
# Clone
git clone https://github.com/Subh24ai/yojana-sahayak.git
cd yojana-sahayak

# Install
pip install -e ".[all]"

# Text query
python -m yojana_sahayak.cli --text "PM Kisan ke liye kaun eligible hai?"

# Voice mode (requires mic)
python -m yojana_sahayak.cli --voice

# Gradio web demo
python -m yojana_sahayak.cli --gradio

# MCP server (for agentic integration)
python -m yojana_sahayak.mcp.server
```

## MCP Server — Tool-Calling for Agentic AI

The MCP server exposes government scheme knowledge as tools that any LLM agent can invoke via the [Model Context Protocol](https://modelcontextprotocol.io/). Uses **stdio transport** — zero network dependency, ideal for air-gapped environments.

### Available Tools

| Tool | Description | Example Input |
|------|-------------|---------------|
| `search_schemes` | Semantic search over 591+ scheme facts | `"PM Kisan eligibility"` |
| `get_scheme_details` | Get specific scheme info by name/field | `"Ayushman Bharat", "benefits"` |
| `check_eligibility` | Check eligibility with user context | `"Mudra Loan", "small business owner"` |
| `list_schemes` | List all indexed schemes | — |

### Integration with Claude Desktop / Cursor

Add to your MCP config:

```json
{
  "mcpServers": {
    "yojana-sahayak": {
      "command": "python",
      "args": ["-m", "yojana_sahayak.mcp.server"],
      "cwd": "/path/to/yojana-sahayak"
    }
  }
}
```

### Programmatic Usage

```python
from yojana_sahayak.mcp.server import search_schemes, check_eligibility

# Semantic search
results = search_schemes("Ujjwala Yojana gas connection", top_k=3)

# Eligibility check
eligibility = check_eligibility("PM Kisan", "farmer with 1 hectare in UP")
```

## Air-Gapped Deployment

This system is designed for environments where data cannot leave the building — government offices, defense installations, regulated enterprises.

```bash
# Build container with all models pre-cached
docker build -t yojana-sahayak .

# Run — zero internet required at runtime
docker run -it yojana-sahayak

# Or with Gradio demo
docker run -p 7860:7860 yojana-sahayak python -m yojana_sahayak.cli --gradio
```

**What runs offline:**
- ✅ Whisper ASR (MLX, cached locally)
- ✅ FAISS retrieval (in-memory index)
- ✅ Fine-tuned Qwen2.5-1.5B (MLX, cached locally)
- ✅ MCP server (stdio transport, no network)
- ⚠️ gTTS requires internet (swap with AI4Bharat TTS for fully offline)

## Project Structure

```
yojana-sahayak/
├── yojana_sahayak/
│   ├── __init__.py              # Package metadata
│   ├── config.py                # Centralized configuration
│   ├── cli.py                   # CLI entry point
│   ├── demo.py                  # Gradio web UI (voice + text + latency tracking)
│   ├── asr/
│   │   └── whisper.py           # Whisper MLX ASR + query rewrite
│   ├── rag/
│   │   └── retriever.py         # FAISS retriever with noise filtering
│   ├── llm/
│   │   └── generator.py         # Fine-tuned Qwen2.5 generation
│   ├── tts/
│   │   └── speaker.py           # Text-to-speech synthesis
│   ├── mcp/
│   │   └── server.py            # MCP server (4 tools, stdio transport)
│   ├── agent/
│   │   └── pipeline.py          # End-to-end pipeline orchestrator
│   └── data_pipeline/
│       ├── extract.py           # PDF extraction from myscheme.gov.in
│       └── generate_qa.py       # Bilingual QA pair generation
├── tests/
│   └── test_core.py             # Tests for MCP tools, RAG, ASR
├── data/
│   ├── core_schemes.jsonl       # Curated high-quality scheme facts
│   ├── train_clean.jsonl        # 31,965 clean training records
│   └── eval_clean.jsonl         # 7,992 clean eval records
├── adapters/
│   └── subh24ai/                # QLoRA adapter weights
├── Dockerfile                   # Air-gapped container deployment
├── Makefile                     # Common operations
├── pyproject.toml               # Project metadata + entry points
└── README.md
```

## Training & Data Pipeline

### Dataset: [Subh24ai/yojana-sahayak-instruct](https://huggingface.co/datasets/Subh24ai/yojana-sahayak-instruct)

- **Source:** 723 PDFs from [myscheme.gov.in](https://www.myscheme.gov.in) covering 2,872 schemes
- **Pipeline:** PDF extraction → structured field parsing → bilingual QA generation → noise filtering
- **Output:** 39,957 instruction-tuning pairs (20,961 English + 18,996 Hindi/Hinglish)
- **Fields:** description, eligibility, benefits, application_process, multi-turn conversations

### Model: [Subh24ai/yojana-sahayak-qwen2.5-1.5b-qlora](https://huggingface.co/Subh24ai/yojana-sahayak-qwen2.5-1.5b-qlora)

- **Base:** Qwen/Qwen2.5-1.5B-Instruct
- **Method:** QLoRA (4-bit NF4, r=16, α=32, dropout=0.05)
- **Target modules:** q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj
- **Training:** 10,000 samples, Kaggle T4 GPU, 54 minutes
- **Results:** Perplexity 1.15 | Eval loss 0.2076

## Testing

```bash
pytest tests/ -v
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| ASR | Whisper large-v3-turbo (MLX) |
| Embeddings | paraphrase-multilingual-MiniLM-L12-v2 |
| Vector Search | FAISS (IndexFlatIP, cosine similarity) |
| LLM | Qwen2.5-1.5B-Instruct + QLoRA |
| TTS | gTTS / AI4Bharat |
| Tool Protocol | MCP (Model Context Protocol) — stdio transport |
| Deployment | Docker, air-gapped capable |
| Data Source | myscheme.gov.in (2,872 government schemes) |

## Links

- **Dataset:** [huggingface.co/datasets/Subh24ai/yojana-sahayak-instruct](https://huggingface.co/datasets/Subh24ai/yojana-sahayak-instruct)
- **Model:** [huggingface.co/Subh24ai/yojana-sahayak-qwen2.5-1.5b-qlora](https://huggingface.co/Subh24ai/yojana-sahayak-qwen2.5-1.5b-qlora)
- **Author:** [Subhash Gupta](https://linkedin.com/in/subhash24gupta) · [GitHub](https://github.com/Subh24ai)

## License

Apache 2.0. Government scheme data sourced from India's public [MyScheme](https://www.myscheme.gov.in) portal.
