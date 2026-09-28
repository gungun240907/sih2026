import os
from pathlib import Path

from dotenv import load_dotenv

# backend/ directory — base for resume.txt, credentials.json and .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ── Secrets ──────────────────────────────────────────────────
GROQ_API_KEY       = os.getenv("GROQ_API_KEY")
GMAIL_ADDRESS      = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
RESEND_API_KEY     = os.getenv("RESEND_API_KEY")
GOOGLE_SHEET_NAME  = os.getenv("GOOGLE_SHEET_NAME", "Job Applications")

# ── File paths (resolved relative to backend/) ───────────────
RESUME_FILE        = BASE_DIR / os.getenv("RESUME_FILE", "resume.txt")
CREDENTIALS_FILE   = BASE_DIR / os.getenv("CREDENTIALS_FILE", "credentials.json")

# ── Scraping ─────────────────────────────────────────────────
HEADLESS           = os.getenv("HEADLESS", "false").lower() in ("1", "true", "yes")

# ── Search settings (defaults; overridable per API request) ──
DEFAULT_KEYWORDS           = ["AI Engineer", "Machine Learning Engineer"]
DEFAULT_LOCATION           = "Bengaluru"
DEFAULT_MATCH_THRESHOLD    = 0.65
DEFAULT_AUTO_APPLY_THRESHOLD = 0.85
DEFAULT_MAX_JOBS_PER_PORTAL  = 10

# ── CORS ─────────────────────────────────────────────────────
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000",
).split(",")

# ── LLM ──────────────────────────────────────────────────────
LLM_MODEL = "llama-3.3-70b-versatile"
