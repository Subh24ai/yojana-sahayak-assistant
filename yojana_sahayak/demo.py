"""
Gradio Web Demo for Yojana Sahayak.

Usage:
    python -m yojana_sahayak.demo
    # or
    python -m yojana_sahayak.cli --gradio
"""

import gradio as gr
from yojana_sahayak.agent.pipeline import YojanaPipeline

_pipeline = None

# ── Content ───────────────────────────────────────────────────────────────────

EXAMPLES = [
    ["PM Kisan ke liye kaun eligible hai?"],
    ["What are the benefits of Ayushman Bharat?"],
    ["Ujjwala Yojana mein free gas connection kaise milega?"],
    ["Mudra loan ke liye kya documents chahiye?"],
    ["Who can apply for PM Awas Yojana?"],
    ["Sukanya Samriddhi Yojana kya hai?"],
    ["How to apply for Atal Pension Yojana?"],
    ["MGNREGA mein kitna paisa milta hai?"],
]

# Compact single-line header — all branding + stats in ~72px
HEADER_HTML = """
<div style="
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f3460 100%);
    border-radius: 10px;
    padding: 0.6rem 1.1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    flex-wrap: wrap;
    margin-bottom: 0.4rem;
    font-family: system-ui, -apple-system, sans-serif;
">
  <!-- brand -->
  <div style="display:flex; align-items:center; gap:0.55rem; flex-shrink:0;">
    <span style="font-size:1.55rem; line-height:1;">🇮🇳</span>
    <div>
      <div style="font-size:1.05rem; font-weight:800; color:#fff; letter-spacing:-0.02em; line-height:1.15;">Yojana Sahayak</div>
      <div style="font-size:0.68rem; color:rgba(255,255,255,0.58); line-height:1.2;">Sovereign Voice Agent · Indian Government Schemes</div>
    </div>
  </div>
  <!-- badges + stats -->
  <div style="display:flex; flex-wrap:wrap; gap:0.28rem; align-items:center;">
    <span style="background:rgba(255,255,255,0.11); border:1px solid rgba(255,255,255,0.2);
                 border-radius:20px; padding:0.15rem 0.55rem; font-size:0.68rem; color:#e2e8f0;">🎙️ Whisper MLX</span>
    <span style="background:rgba(255,255,255,0.11); border:1px solid rgba(255,255,255,0.2);
                 border-radius:20px; padding:0.15rem 0.55rem; font-size:0.68rem; color:#e2e8f0;">🔍 FAISS RAG</span>
    <span style="background:rgba(255,255,255,0.11); border:1px solid rgba(255,255,255,0.2);
                 border-radius:20px; padding:0.15rem 0.55rem; font-size:0.68rem; color:#e2e8f0;">🧠 Qwen2.5 QLoRA</span>
    <span style="background:rgba(255,153,51,0.18); border:1px solid rgba(255,153,51,0.4);
                 border-radius:20px; padding:0.15rem 0.55rem; font-size:0.68rem; color:#fed7aa;">✈️ Offline</span>
    <span style="background:rgba(255,255,255,0.07); border:1px solid rgba(255,255,255,0.14);
                 border-radius:20px; padding:0.15rem 0.55rem; font-size:0.68rem; color:rgba(255,255,255,0.65);">
      24% WER &nbsp;·&nbsp; RTF 0.37 &nbsp;·&nbsp; 585 schemes &nbsp;·&nbsp; 39.9K pairs
    </span>
  </div>
</div>
"""


LATENCY_TEMPLATE = """
<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; margin-top: 0.25rem;">
  <div style="background:#f0f9ff; border:1px solid #bae6fd; border-radius:10px;
              padding:0.6rem; text-align:center;">
    <div style="font-size:1rem; font-weight:700; color:#0369a1;">{asr}</div>
    <div style="font-size:0.68rem; color:#64748b; margin-top:0.1rem;">ASR</div>
  </div>
  <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:10px;
              padding:0.6rem; text-align:center;">
    <div style="font-size:1rem; font-weight:700; color:#15803d;">{rag}</div>
    <div style="font-size:0.68rem; color:#64748b; margin-top:0.1rem;">RAG</div>
  </div>
  <div style="background:#fdf4ff; border:1px solid #e9d5ff; border-radius:10px;
              padding:0.6rem; text-align:center;">
    <div style="font-size:1rem; font-weight:700; color:#7e22ce;">{llm}</div>
    <div style="font-size:0.68rem; color:#64748b; margin-top:0.1rem;">LLM</div>
  </div>
  <div style="background:#fff7ed; border:1px solid #fed7aa; border-radius:10px;
              padding:0.6rem; text-align:center;">
    <div style="font-size:1rem; font-weight:700; color:#c2410c;">{total}</div>
    <div style="font-size:0.68rem; color:#64748b; margin-top:0.1rem;">Total</div>
  </div>
</div>
"""

LATENCY_EMPTY = LATENCY_TEMPLATE.format(asr="—", rag="—", llm="—", total="—")

RUNNING_HTML = """
<div style="
    display: flex; align-items: center; gap: 0.6rem;
    background: #eff6ff; border: 1px solid #bfdbfe;
    border-radius: 10px; padding: 0.6rem 1rem;
    font-family: system-ui, sans-serif; font-size: 0.88rem;
    color: #1e40af; font-weight: 500;
">
  <span style="display:inline-block; width:14px; height:14px;
               border:2px solid #93c5fd; border-top-color:#1d4ed8;
               border-radius:50%; animation:spin 0.8s linear infinite;"></span>
  Running pipeline… please wait
</div>
<style>
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
"""

CSS = """
footer { display: none !important; }

/* Prevent page-level scroll — everything fits in viewport */
body { overflow: hidden !important; }

.gradio-container {
    max-width: 100% !important;
    padding: 0.45rem 0.65rem 0 !important;
}

/* Tab nav */
.tab-nav { border-bottom: 2px solid #e5e7eb !important; }
.tab-nav button {
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    padding: 0.4rem 0.8rem !important;
}
.tab-nav button.selected {
    color: #1e40af !important;
    border-bottom-color: #1e40af !important;
    font-weight: 600 !important;
}

/* Primary buttons */
button.primary {
    background: linear-gradient(135deg, #1e40af, #1d4ed8) !important;
    border: none !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em !important;
    box-shadow: 0 2px 6px rgba(30,64,175,0.3) !important;
    transition: opacity 0.15s !important;
}
button.primary:hover { opacity: 0.9 !important; }

/* Left panel — scrolls inside its own box, never pushes page height */
.ys-left-col {
    overflow-y: auto !important;
    overflow-x: hidden !important;
    height: 100% !important;
    max-height: calc(100vh - 110px) !important;
    padding-right: 2px !important;
}

/* Transcript word highlighting */
.ys-word {
    display: inline;
    border-radius: 3px;
    padding: 0 2px;
    transition: background 0.08s, color 0.08s;
}
.ys-highlight {
    background: #fef08a;
    color: #1a1a1a;
    font-weight: 600;
}
"""

# JS injected once — finds the latest response's word spans in the chatbot bubble
# and highlights the current word as audio plays.
# Each response gets a data-ysv (version) number; JS always targets the highest one
# so old messages in the history never interfere.
HIGHLIGHT_SCRIPT = """
<script>
(function () {
    var bound = null;

    function latestTranscript() {
        var els = document.querySelectorAll('.ys-transcript');
        var best = null, bestV = -1;
        els.forEach(function (el) {
            var v = parseInt(el.getAttribute('data-ysv') || '0', 10);
            if (v > bestV) { bestV = v; best = el; }
        });
        return best;
    }

    function onTimeUpdate() {
        var transcript = latestTranscript();
        if (!transcript || !bound || !bound.duration) return;
        var words = transcript.querySelectorAll('.ys-word');
        if (!words.length) return;
        var idx = Math.floor((bound.currentTime / bound.duration) * words.length);
        idx = Math.min(idx, words.length - 1);
        words.forEach(function (w, i) {
            w.classList.toggle('ys-highlight', i === idx);
        });
    }

    function onEnded() {
        document.querySelectorAll('.ys-word.ys-highlight').forEach(function (w) {
            w.classList.remove('ys-highlight');
        });
    }

    function tryBind() {
        var el = document.querySelector('#ys-audio-out audio');
        if (!el || el === bound) return;
        if (bound) {
            bound.removeEventListener('timeupdate', onTimeUpdate);
            bound.removeEventListener('ended', onEnded);
        }
        bound = el;
        bound.addEventListener('timeupdate', onTimeUpdate);
        bound.addEventListener('ended', onEnded);
    }

    var obs = new MutationObserver(tryBind);
    function init() {
        obs.observe(document.body, { childList: true, subtree: true });
        tryBind();
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
</script>
"""

ARCH_MD = """\
#### Pipeline

```
Voice ──► Whisper large-v3-turbo (MLX)
              │
              ▼
        Query Rewrite (ASR correction dict)
              │
              ▼
        FAISS IndexFlatIP  ◄── sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
              │  top-k=3, cosine ≥ 0.40
              ▼
        Qwen2.5-1.5B-Instruct (QLoRA fine-tune, MLX)
              │
              ▼
           Answer
```

#### Stack

| Layer | Component |
|-------|-----------|
| ASR | `mlx-community/whisper-large-v3-turbo` |
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2` |
| Vector store | FAISS flat inner-product (dim 384) |
| LLM | `Qwen2.5-1.5B-Instruct` · QLoRA · 4-bit |
| MCP tools | `search_schemes` · `get_scheme_details` · `check_eligibility` · `list_schemes` |
| Infra | Docker · air-gapped · stdio MCP transport |

#### Benchmarks
- **ASR WER:** 24% on Hindi scheme queries · RTF 0.37 (2.7× real-time)
- **LLM:** perplexity 1.15 on held-out scheme QA
- **Data:** 585 scheme facts · 2,872 schemes · 39,957 instruct pairs
"""

# ── Helpers ───────────────────────────────────────────────────────────────────

_ys_version = 0


def _make_transcript_html(text: str) -> str:
    """Wrap each word in a span for in-bubble highlighting during audio playback.

    Uses an incrementing data-ysv attribute so the JS always targets the
    latest response and ignores spans left in older chat history messages.
    """
    global _ys_version
    _ys_version += 1
    spans = " ".join(
        f'<span class="ys-word" data-idx="{i}">{w}</span>'
        for i, w in enumerate(text.split())
    )
    return (
        f'<div class="ys-transcript" data-ysv="{_ys_version}" '
        f'style="line-height:1.9;">'
        + spans
        + "</div>"
    )


# ── Pipeline ──────────────────────────────────────────────────────────────────

def _get_pipeline() -> YojanaPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = YojanaPipeline()
    return _pipeline


def _append(history: list, user: str, assistant: str) -> list:
    history = list(history or [])
    history.append({"role": "user",      "content": user})
    history.append({"role": "assistant", "content": assistant})
    return history


def _latency_html(result) -> str:
    asr = f"{result.asr_latency:.2f}s" if not result.asr_skipped else "—"
    return LATENCY_TEMPLATE.format(
        asr=asr,
        rag=f"{result.rag_latency:.2f}s",
        llm=f"{result.llm_latency:.2f}s",
        total=f"{result.total_latency:.2f}s",
    )


def _show_running_text(text, history):
    """Step 1 for text: immediately echo the user message + spinner."""
    if not text or not text.strip():
        return history, text, RUNNING_HTML
    history = _append(list(history or []), text, "⏳ …")
    return history, text, RUNNING_HTML


def _run_text(text, history):
    """Step 2 for text: run pipeline and replace the placeholder."""
    if not text or not text.strip():
        return history, LATENCY_EMPTY, None
    pipeline = _get_pipeline()
    result = pipeline.run(text_input=text, speak=False)
    history = list(history or [])
    # Store response as highlighted HTML directly in the chatbot bubble
    html = _make_transcript_html(result.answer)
    if history and history[-1]["role"] == "assistant":
        history[-1]["content"] = html
    from yojana_sahayak.tts.speaker import synthesize
    audio_path = synthesize(result.answer)
    return history, _latency_html(result), audio_path


def _show_running_audio(audio, history):
    """Step 1 for voice: immediately show a spinner."""
    if audio is None:
        return history, RUNNING_HTML
    history = _append(list(history or []), "🎤 transcribing…", "⏳ …")
    return history, RUNNING_HTML


def _run_audio(audio, history):
    """Step 2 for voice: run pipeline and replace the placeholders."""
    if audio is None:
        return history, LATENCY_EMPTY, None
    pipeline = _get_pipeline()
    result = pipeline.run(audio_path=audio, speak=False)

    label = result.query_raw
    if result.query_clean != result.query_raw:
        label += f" → {result.query_clean}"

    history = list(history or [])
    # Replace placeholders added in step 1
    if len(history) >= 2:
        history[-2]["content"] = f"🎤 {label}"
        history[-1]["content"] = result.answer
    else:
        history = _append(history, f"🎤 {label}", result.answer)
    from yojana_sahayak.tts.speaker import synthesize
    audio_path = synthesize(result.answer)
    # Store response as highlighted HTML directly in the chatbot bubble
    html = _make_transcript_html(result.answer)
    if len(history) >= 2:
        history[-1]["content"] = html
    return history, _latency_html(result), audio_path


def clear_all():
    _get_pipeline().reset_history()
    return [], None, "", LATENCY_EMPTY, None


# ── UI ────────────────────────────────────────────────────────────────────────

def launch_gradio(share: bool = True):
    with gr.Blocks() as demo:

        gr.HTML(HIGHLIGHT_SCRIPT)
        gr.HTML(HEADER_HTML)

        history_state = gr.State([])

        with gr.Row(height="calc(100vh - 110px)"):

            # ── Left panel: all controls ──────────────────────────────────────
            with gr.Column(scale=1, min_width=290, elem_classes=["ys-left-col"]):

                with gr.Tabs():
                    with gr.Tab("🎤 Voice"):
                        audio_input = gr.Audio(
                            sources=["microphone"],
                            type="filepath",
                            label="Record in Hindi or English",
                        )
                        voice_btn = gr.Button("Ask", variant="primary")

                    with gr.Tab("⌨️ Text"):
                        text_input = gr.Textbox(
                            placeholder="PM Kisan ke liye kaun eligible hai?",
                            lines=3,
                            show_label=False,
                            submit_btn=True,
                        )
                        text_btn = gr.Button("Ask", variant="primary")
                        with gr.Accordion("Examples", open=False):
                            gr.Examples(examples=EXAMPLES, inputs=[text_input])

                    with gr.Tab("🔧 Info"):
                        gr.Markdown("#### ⏱ Latency")
                        latency_out = gr.HTML(LATENCY_EMPTY)
                        gr.Markdown("#### Pipeline")
                        gr.Markdown(ARCH_MD)

                clear_btn = gr.Button("Clear conversation", variant="secondary", size="sm")

                audio_out = gr.Audio(
                    label="Voice Response",
                    type="filepath",
                    autoplay=True,
                    interactive=False,
                    elem_id="ys-audio-out",
                )

            # ── Right panel: conversation fills all height ────────────────────
            with gr.Column(scale=2, min_width=460):
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height="calc(100vh - 150px)",
                    layout="bubble",
                    buttons=["copy"],
                    sanitize_html=False,
                    placeholder=(
                        "<div style='text-align:center; color:#9ca3af; margin-top:4rem;'>"
                        "<div style='font-size:2.5rem;'>🇮🇳</div>"
                        "<div style='margin-top:0.5rem; font-size:0.95rem;'>"
                        "Ask about any Indian government scheme<br>"
                        "<span style='font-size:0.82rem;'>Hindi · English · Hinglish</span>"
                        "</div></div>"
                    ),
                )

        # ── Events ────────────────────────────────────────────────────────────
        # Voice: step 1 → show spinner in chat immediately
        #        step 2 → run pipeline and fill in real answer
        voice_btn.click(
            _show_running_audio,
            inputs=[audio_input, history_state],
            outputs=[history_state, latency_out],
        ).then(
            lambda h: h, inputs=history_state, outputs=chatbot
        ).then(
            _run_audio,
            inputs=[audio_input, history_state],
            outputs=[history_state, latency_out, audio_out],
        ).then(lambda h: h, inputs=history_state, outputs=chatbot)

        # Text button: step 1 → echo user message + spinner
        #              step 2 → run pipeline
        def _wire_text(trigger):
            trigger.click(
                _show_running_text,
                inputs=[text_input, history_state],
                outputs=[history_state, text_input, latency_out],
            ).then(
                lambda h: h, inputs=history_state, outputs=chatbot
            ).then(
                _run_text,
                inputs=[text_input, history_state],
                outputs=[history_state, latency_out, audio_out],
            ).then(lambda h: h, inputs=history_state, outputs=chatbot)

        _wire_text(text_btn)

        text_input.submit(
            _show_running_text,
            inputs=[text_input, history_state],
            outputs=[history_state, text_input, latency_out],
        ).then(
            lambda h: h, inputs=history_state, outputs=chatbot
        ).then(
            _run_text,
            inputs=[text_input, history_state],
            outputs=[history_state, latency_out, audio_out],
        ).then(lambda h: h, inputs=history_state, outputs=chatbot)

        clear_btn.click(
            clear_all,
            outputs=[history_state, audio_input, text_input, latency_out, audio_out],
        ).then(lambda: [], outputs=chatbot)

    print("\nLaunching Yojana Sahayak Demo...")
    print("   Open in browser to test and record demo videos.\n")
    demo.launch(share=share, css=CSS, theme=gr.themes.Soft())


if __name__ == "__main__":
    launch_gradio()
