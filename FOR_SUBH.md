# FOR_SUBH.md — What Changed and Why

## What We Did: "Reforged" Yojana Sahayak

Took your 5 flat `day*.py` files (1,533 lines total) and restructured into a **20-file modular Python package** (1,292 lines — actually *fewer* lines because we eliminated duplication).

## The Core Transformation

### Before (how a hiring manager sees it):
```
day1_cleanup.py    ← "learning journal"
day2_whisper.py    ← "homework assignment"
day4_pipeline.py   ← "tutorial project"
1 commit, 0 stars
```

### After (how they see it now):
```
yojana_sahayak/    ← "production package"
├── mcp/server.py  ← "wait, this person built MCP tools?"
├── rag/retriever.py
├── asr/whisper.py
├── agent/pipeline.py
├── Dockerfile     ← "air-gapped deployment?!"
└── tests/         ← "they write tests too?"
```

## Why Each Decision Was Made

### 1. MCP Server (server.py — 226 lines) ← THE WEAPON

**Why this matters more than everything else combined:**

Sarvam's Chanakya JD literally says "MCP servers, document ingestion pipelines, agentic frameworks." You had 2 of 3. Now you have all 3.

The MCP server exposes 4 tools via stdio transport:
- `search_schemes` — semantic search over your FAISS index
- `get_scheme_details` — direct lookup by scheme name
- `check_eligibility` — eligibility check with user context
- `list_schemes` — list all indexed schemes

**Why stdio transport:** Air-gapped environments can't make HTTP calls. MCP over stdio runs as a child process with zero network dependency. This is exactly what Chanakya needs for government deployments.

**The insight most people miss:** MCP isn't just an API — it's a *protocol* that lets any LLM invoke your tools. Your fine-tuned Qwen can call these tools. Claude can call these tools. Any orchestrator can. That's the point.

### 2. Modular Package Structure

**Why not keep `day*.py`?** Because naming reveals how you think. `day1_pipeline.py` says "I built this in a sprint." `yojana_sahayak/rag/retriever.py` says "I engineer systems."

The module boundaries aren't arbitrary — each maps to a **replaceable component:**
- Swap `asr/whisper.py` with a different ASR engine → nothing else changes
- Swap `rag/retriever.py` with Milvus/Pinecone → pipeline still works
- Swap `llm/generator.py` with vLLM → same interface

This is how production teams think. Senior engineers recognize this immediately.

### 3. Config Module (config.py)

**Before:** Magic strings scattered across files (`"mlx-community/whisper-large-v3-turbo"` hardcoded in 3 places).

**After:** Single source of truth. Change one value, everything updates.

### 4. SchemeRetriever as a Class

**Before:** Global variables (`_rag_index`, `_rag_docs`, `_rag_encoder`) with module-level mutation.

**After:** `SchemeRetriever` class with clean lifecycle. You can create multiple instances, mock in tests, inspect state. This is the #1 code quality signal senior engineers look for.

### 5. PipelineResult Dataclass

**Before:** `run_pipeline()` returned a raw dict. Caller had to guess what keys exist.

**After:** `PipelineResult` dataclass with typed fields. IDE autocomplete works. No key errors.

### 6. Dockerfile

**Why not Docker Compose?** Overkill for a single-service system. A clean Dockerfile that can pre-cache models during `docker build` is exactly what an air-gapped deployment needs.

### 7. Tests

**What's tested:** Config validity, ASR corrections (Devanagari + English), MCP tool interfaces, data quality (no scraping artifacts in core_schemes.jsonl), TTS language detection.

**What's NOT tested (and that's OK for now):** End-to-end pipeline (needs GPU), Whisper transcription (needs audio files), Gradio UI. These are integration tests — add them when you have CI/CD.

## Rejected Alternatives

1. **FastAPI wrapper instead of MCP** — Considered but rejected. MCP is the specific technology Sarvam lists in their JD. FastAPI doesn't work in air-gapped stdio mode.

2. **Separate repos for MCP + pipeline** — Rejected. One repo, one `pip install`. Makes the story cleaner.

3. **Building a new project from scratch** — Rejected. Your existing code has real production signals (noise filtering, cosine thresholds, ASR corrections). Throwing it away would lose that credibility.

## What You Need to Do Next

### Day 1 (Today — 2 hours):
1. Create a new GitHub repo `yojana-sahayak` (or force-push to existing)
2. Extract the tar.gz, commit with a clean history
3. Make multiple commits (don't squash into 1) — commit structure, then modules, then tests, then README
4. Apply to Sarvam + all 11 companies IN PARALLEL

### Day 2 (Tomorrow — 3 hours):
1. Test the MCP server locally: `pip install -e ".[mcp]" && python -m yojana_sahayak.mcp.server`
2. Fix any bugs you find
3. Run `pytest tests/ -v` and fix failures
4. Record a 2-minute demo video (screen recording showing the pipeline working)

### Day 3:
1. Write a LinkedIn post: "I built a sovereign voice agent with MCP tools for Indian government schemes — runs fully offline, no API calls, designed for air-gapped deployment"
2. Tag @SarvamAI
3. Update all application emails with the new repo link

## Transferable Lessons

1. **Packaging > building.** You already had 90% of the capabilities. The 10% that mattered was how they were organized and presented.

2. **Name your files like a senior engineer.** `retriever.py` beats `day4_pipeline.py` every time. The file tree IS your first interview.

3. **MCP is the new moat for AI engineers.** Very few people have built MCP servers. It's the "Docker for LLM tools" moment — early adopters get disproportionate credit.

4. **Tests signal seniority more than code.** A junior writes code. A mid-level writes working code. A senior writes tested code. Even 142 lines of tests changes how your entire project is perceived.
