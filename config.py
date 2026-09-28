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

# Indian job-hub cities the scraper supports (mirrors backend/app/cities.py)
INDIAN_CITIES = [
    "Bengaluru", "Mumbai", "Delhi NCR", "Hyderabad", "Chennai", "Pune",
    "Kolkata", "Ahmedabad", "Gurugram", "Noida", "Jaipur", "Lucknow",
    "Chandigarh", "Kochi", "Coimbatore", "Indore", "Bhopal", "Nagpur",
    "Surat", "Vadodara", "Thiruvananthapuram", "Bhubaneswar",
    "Visakhapatnam", "Mysuru", "Dehradun", "Guwahati", "Patna", "Ranchi",
    "Jodhpur", "Vijayawada",
]

CITY_ALIASES = {
    "bangalore": "Bengaluru", "bombay": "Mumbai", "delhi": "Delhi NCR",
    "new delhi": "Delhi NCR", "ncr": "Delhi NCR", "gurgaon": "Gurugram",
    "calcutta": "Kolkata", "madras": "Chennai", "poona": "Pune",
    "cochin": "Kochi", "trivandrum": "Thiruvananthapuram",
    "vizag": "Visakhapatnam", "mysore": "Mysuru",
}


def normalize_city(raw):
    """Resolve user input to a canonical city name, or raise ValueError."""
    key = " ".join((raw or "").strip().split()).lower()
    if not key:
        return LOCATION
    if key in CITY_ALIASES:
        return CITY_ALIASES[key]
    for city in INDIAN_CITIES:
        if city.lower() == key:
            return city
    raise ValueError(
        f"Unsupported location {raw!r} — choose a city in India "
        f"({', '.join(INDIAN_CITIES)})"
    )