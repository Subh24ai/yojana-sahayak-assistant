"""Centralized configuration for all pipeline components."""

from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# ── HuggingFace ───────────────────────────────────────────────────────────────
HF_USERNAME = "Subh24ai"
HF_DATASET = f"{HF_USERNAME}/yojana-sahayak-instruct"
HF_MODEL_MERGED = f"{HF_USERNAME}/yojana-sahayak-qwen2.5-1.5b-merged"
HF_MODEL_QLORA = f"{HF_USERNAME}/yojana-sahayak-qwen2.5-1.5b-qlora"
BASE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"

# ── ASR ───────────────────────────────────────────────────────────────────────
WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"
SAMPLE_RATE = 16000
RECORD_DURATION_SEC = 6

# ── RAG ───────────────────────────────────────────────────────────────────────
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
RAG_TOP_K = 3
RAG_MIN_SCORE = 0.75
RAG_MIN_SCORE_NAMED = 0.45  # lower threshold for known scheme aliases

TRAIN_CLEAN_PATH = str(DATA_DIR / "train_clean.jsonl")
CORE_SCHEMES_PATH = str(DATA_DIR / "core_schemes.jsonl")

# ── LLM ───────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are Yojana Sahayak, a concise assistant for Indian government welfare schemes. "
    "Rules you must follow:\n"
    "1. Answer ONLY what the user asked — no extra background, history, or process details.\n"
    "2. Keep your answer to 3-5 sentences maximum. Stop after that.\n"
    "3. Reply in the same language the user used (Hindi, English, or Hinglish).\n"
    "4. If the provided reference does not answer the question, say: "
    "'Mujhe is scheme ke baare mein yeh specific jankari nahi hai.' Do NOT make up information."
)
MAX_HISTORY_TURNS = 5
LLM_MAX_TOKENS = 150
LLM_TEMPERATURE = 0.1

# ── Scheme Aliases (for query expansion) ──────────────────────────────────────
SCHEME_ALIASES = {
    "pm kisan":     "Pradhan Mantri Kisan Samman Nidhi",
    "pm awas":      "PM Awas Yojana",
    "ayushman":     "Ayushman Bharat PM-JAY",
    "ujjwala":      "PM Ujjwala Yojana",
    "mudra":        "Pradhan Mantri Mudra Yojana",
    "mnrega":       "Mahatma Gandhi National Rural Employment Guarantee",
    "mgnrega":      "Mahatma Gandhi National Rural Employment Guarantee",
    "sukanya":      "Sukanya Samriddhi Yojana",
    "atal pension": "Atal Pension Yojana",
    "pmkvy":        "Pradhan Mantri Kaushal Vikas Yojana",
}

# ── LLM output noise markers (web-scraping artifacts the model may hallucinate) ─
NOISE_MARKERS = (
    "sEligibility", "Application ProcessDocuments Required",
    "Frequently Asked Questions", "Sources And References",
    "Something went wrong", "Was this helpful",
    "Are you sure", "sign out", "CancelSign", "Sign OutEng",
    "NowDocuments Required", "\xef\xbb\xbf",
    # Hallucination transition phrases
    "इस प्रकार,", "Is prakar,", "Hamaare eligibility",
    "hamaare eligibility", "Additional eligibility",
)

# ── ASR Corrections ───────────────────────────────────────────────────────────
ASR_CORRECTIONS = {
    # Devanagari scheme name errors
    "आइसमान":      "आयुष्मान",
    "आइश्मान":     "आयुष्मान",
    "पीम":          "पीएम",
    "पी-म":         "पीएम",
    "पी-एम":        "पीएम",
    "प्यांकिसान":   "पीएम किसान",
    "प्यांकिसन":    "पीएम किसान",
    # Common word misheard errors
    "इलेजवल":      "एलिजिबल",
    "फिरीक":        "फ्री",
    "ऐस कनेक्शन":  "गैस कनेक्शन",
    "ऐस":           "गैस",
    "निलेज":        "जानकारी",
    "बलाएं":        "बताएं",
    "अपलाई":       "अप्लाई",
    "डाकुमेंट्स":  "डॉक्यूमेंट्स",
    # Scheme name errors
    "उज्जुला":     "उज्ज्वला",
    # Roman script errors
    "pm kisaan":    "PM Kisan",
    "ayushmann":    "Ayushman",
    "ujwala":       "Ujjwala",
    "mudhra":       "Mudra",
}
