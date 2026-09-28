"""Indian job-hub cities supported by the scraper.

Single source of truth for location validation. The frontend ships the same
list for its city dropdown; the API validates against it (case-insensitive,
with common aliases resolved to canonical names).
"""

INDIAN_CITIES: list[str] = [
    "Bengaluru",
    "Mumbai",
    "Delhi NCR",
    "Hyderabad",
    "Chennai",
    "Pune",
    "Kolkata",
    "Ahmedabad",
    "Gurugram",
    "Noida",
    "Jaipur",
    "Lucknow",
    "Chandigarh",
    "Kochi",
    "Coimbatore",
    "Indore",
    "Bhopal",
    "Nagpur",
    "Surat",
    "Vadodara",
    "Thiruvananthapuram",
    "Bhubaneswar",
    "Visakhapatnam",
    "Mysuru",
    "Dehradun",
    "Guwahati",
    "Patna",
    "Ranchi",
    "Jodhpur",
    "Vijayawada",
]

# Common alternate names / spellings -> canonical city name (all lowercase keys)
CITY_ALIASES: dict[str, str] = {
    "bangalore": "Bengaluru",
    "bombay": "Mumbai",
    "delhi": "Delhi NCR",
    "new delhi": "Delhi NCR",
    "gurgaon": "Gurugram",
    "calcutta": "Kolkata",
    "madras": "Chennai",
    "poona": "Pune",
    "cochin": "Kochi",
    "trivandrum": "Thiruvananthapuram",
    "vizag": "Visakhapatnam",
    "mysore": "Mysuru",
    "ncr": "Delhi NCR",
}

_DEFAULT = "Bengaluru"


def normalize_city(raw: str | None) -> str:
    """Resolve user input to a canonical city name, or raise ValueError."""
    if raw is None:
        return _DEFAULT
    key = " ".join(raw.strip().split()).lower()
    if not key:
        return _DEFAULT
    if key in CITY_ALIASES:
        return CITY_ALIASES[key]
    for city in INDIAN_CITIES:
        if city.lower() == key:
            return city
    raise ValueError(
        f"Unsupported location {raw!r} — choose a city in India "
        f"({', '.join(INDIAN_CITIES)})"
    )


def slugify_city(city: str) -> str:
    """URL-slug form used by Naukri search URLs, e.g. 'Delhi NCR' -> 'delhi-ncr'."""
    return "-".join(city.lower().split())
