import json
from openai import OpenAI
from app.config import DEFAULT_MATCH_THRESHOLD, GROQ_API_KEY, LLM_MODEL
from app.core.tracker.models import Job
client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)
SCORE_PROMPT = """
You are a recruiting expert. Given a resume and a job description,
return ONLY valid JSON with exactly this shape, no extra text:
{{
  "score": 0.0,
  "matched_skills": ["skill1", "skill2"],
  "missing_skills": ["skill1", "skill2"],
  "recommendation": "apply",
  "reason": "one sentence explaining the score",
  "experience_required": 0,
  "experience_match": true
}}

Rules:
- score must be a float between 0.0 and 1.0
- recommendation must be one of: "apply", "maybe", "skip"
- experience_required: extract the MINIMUM years of experience required from the JD as an integer
  * If fresher / no experience mentioned / 0-2 years → set to 0
  * If 2+ years minimum → set to the exact minimum number
  * If you cannot determine it clearly → set to 0
  * Never return a number above 20
- experience_match: set to true if experience_required <= 2, false otherwise
- Score normally based on skills match regardless of experience

RESUME:
{resume}

JOB DESCRIPTION:
{jd}
"""

VALID_RECOMMENDATIONS = ("apply", "maybe", "skip")
MAX_EXPERIENCE_YEARS = 20


class ScoringError(Exception):
    """Raised when the model response cannot be turned into a usable result."""


def extract_json(raw: str) -> dict:
    """Parse the model reply into a dict, tolerating fences and prose.

    Models occasionally wrap the payload in ```json fences or prepend a
    sentence of commentary. A bare json.loads() raises on all of those, and
    the old code swallowed that into a silent 0% score.
    """
    text = (raw or "").strip()
    if not text:
        raise ScoringError("empty response from model")

    if text.startswith("```"):
        text = text.split("```", 2)[1] if text.count("```") >= 2 else text.lstrip("`")
        text = text.removeprefix("json").strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ScoringError("no JSON object found in response: %r" % text[:120])
        try:
            parsed = json.loads(text[start:end + 1])
        except json.JSONDecodeError as e:
            raise ScoringError("malformed JSON (%s) in response: %r" % (e.msg, text[:120]))

    if not isinstance(parsed, dict):
        raise ScoringError("expected a JSON object, got %s" % type(parsed).__name__)
    return parsed


def _coerce_score(value) -> float:
    """Accept 0.85, "0.85", "85%", "85" and clamp to 0.0-1.0."""
    if isinstance(value, bool) or value is None:
        raise ScoringError("score missing or not numeric: %r" % (value,))
    if isinstance(value, (int, float)):
        score = float(value)
        if score > 1.0:
            score /= 100.0
    else:
        text = str(value).strip()
        if text.endswith("%"):
            text = text[:-1].strip()
        try:
            score = float(text)
        except ValueError:
            raise ScoringError("score not numeric: %r" % (value,))
        if score > 1.0:
            score /= 100.0
    return max(0.0, min(1.0, score))


def _coerce_skills(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [s.strip() for s in value.split(",") if s.strip()]
    if isinstance(value, (list, tuple)):
        return [str(s).strip() for s in value if str(s).strip()]
    raise ScoringError("skills not a list: %r" % type(value).__name__)


def normalize_result(result: dict) -> dict:
    """Force the model's reply into the exact shape the rest of the app relies on."""
    score = _coerce_score(result.get("score"))

    rec = str(result.get("recommendation") or "").strip().lower()
    if rec not in VALID_RECOMMENDATIONS:
        rec = "apply" if score >= 0.85 else "maybe" if score >= DEFAULT_MATCH_THRESHOLD else "skip"

    try:
        exp_raw = result.get("experience_required", 0)
        exp_required = int(float(exp_raw)) if exp_raw not in (None, "") else 0
    except (TypeError, ValueError):
        exp_required = 0
    if exp_required < 0 or exp_required > MAX_EXPERIENCE_YEARS:
        exp_required = 0

    return {
        "score": score,
        "recommendation": rec,
        "reason": str(result.get("reason") or "").strip(),
        "matched_skills": _coerce_skills(result.get("matched_skills")),
        "missing_skills": _coerce_skills(result.get("missing_skills")),
        "experience_required": exp_required,
        "experience_match": bool(result.get("experience_match", exp_required <= 2)),
    }


COMMON_SKILLS = [
    "python", "machine learning", "deep learning", "ai", "artificial intelligence",
    "nlp", "computer vision", "llm", "scikit-learn", "pandas", "numpy", "pytorch",
    "tensorflow", "sql", "postgresql", "mysql", "docker", "airflow", "react",
    "javascript", "fastapi", "django", "rest api", "git", "etl", "cloud",
    "aws", "azure", "tableau", "power bi"
]


def _heuristic_fallback_score(job: Job, resume_text: str, error_detail: str) -> dict:
    """Fallback scorer when Groq API key is invalid, missing, or rate-limited."""
    text_lower = (job.title + " " + job.description).lower()
    resume_lower = resume_text.lower()

    matched: list[str] = []
    missing: list[str] = []
    for skill in COMMON_SKILLS:
        if skill in text_lower:
            if skill in resume_lower:
                matched.append(skill.title())
            else:
                missing.append(skill.title())

    # Base score on title relevance and matched skills
    base = 0.55
    title_lower = job.title.lower()
    if any(k in title_lower for k in ("ai", "machine learning", "ml", "engineer", "data")):
        base += 0.15
    score = min(0.92, base + (len(matched) * 0.05))

    rec = "apply" if score >= 0.85 else "maybe" if score >= DEFAULT_MATCH_THRESHOLD else "skip"
    err_short = error_detail.split(":")[0]
    return {
        "score": round(score, 2),
        "recommendation": rec,
        "reason": f"Skill fallback: {len(matched)} skills matched (Groq: {err_short})",
        "matched_skills": matched[:6],
        "missing_skills": missing[:4],
        "experience_required": 0,
        "experience_match": True,
        "fallback_used": True,
    }


def score_job(job: Job, resume_text: str) -> Job:
    """Score one job using Groq LLM with heuristic fallback if the API is unavailable."""
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{
                "role": "user",
                "content": SCORE_PROMPT.format(resume=resume_text, jd=job.description),
            }],
            temperature=0.1,
        )
        raw = response.choices[0].message.content
        job.match_meta = normalize_result(extract_json(raw))
        job.match_score = job.match_meta["score"]
    except Exception as e:
        detail = "%s: %s" % (type(e).__name__, e)
        print(f"  Scoring fallback for {job.title} at {job.company} -> {detail}")
        job.match_meta = _heuristic_fallback_score(job, resume_text, detail)
        job.match_score = job.match_meta["score"]
    return job


def filter_jobs(jobs: list[Job], threshold: float = 0.65) -> list[Job]:
    filtered = []
    for j in jobs:
        # a job whose scoring explicitly errored without fallback is skipped
        if j.match_meta.get("score_error"):
            continue

        exp_req = j.match_meta.get("experience_required", 0)
        if exp_req > 20:
            exp_req = 0
        if exp_req > 2:
            print(f"  Skipping (requires {exp_req} yrs): {j.title} at {j.company}")
            continue

        if j.match_score >= threshold:
            filtered.append(j)
    return filtered