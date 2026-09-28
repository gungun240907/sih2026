import os
from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY       = os.getenv("GROQ_API_KEY")
GROQ_MODEL         = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GMAIL_ADDRESS      = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
GOOGLE_SHEET_NAME  = os.getenv("GOOGLE_SHEET_NAME", "Job Applications")
KEYWORDS           = ["AI Engineer", "Machine Learning Engineer"]
LOCATION           = "Bengaluru"
MATCH_THRESHOLD    = 0.65
AUTO_APPLY_THRESHOLD = 0.85
HEADLESS           = os.getenv("HEADLESS", "true").strip().lower() in ("1", "true", "yes", "on")