"""LLM resume analysis with heuristic fallback (mirrors matcher style)."""

import json

from app.config import GROQ_API_KEY, LLM_MODEL
from app.core.matcher.resume_matcher import COMMON_SKILLS, extract_json

ANALYZE_PROMPT = """
You are a hiring expert and ATS specialist. Analyze this resume and return
ONLY valid JSON with exactly this shape, no extra text:
{{
  "skills": ["skill1", "skill2"],
  "roles": ["current or target role"],
  "years_experience": 0,
  "suggested_keywords": ["AI Engineer", "Machine Learning Engineer"],
  "suggested_location": "Bengaluru",
  "ats_score": 75,
  "strengths": ["strength1"],
  "gaps": ["gap1"],
  "summary": "2-3 sentence professional summary"
}}

Rules:
- skills: 5-15 concrete technical skills found in the resume
- years_experience: integer 0-20 (internships count as 0-1)
- suggested_keywords: 2-4 job titles to search for, based on the resume
- suggested_location: an Indian job-hub city mentioned in the resume, else "Bengaluru"
- ats_score: 0-100 for clarity, keywords, measurable impact
- strengths/gaps: 2-4 short bullets each

RESUME:
{resume}
"""


def _fallback(text: str) -> dict:
    lower = text.lower()
    skills = [s.title() for s in COMMON_SKILLS if s in lower][:12]
    keywords = ["AI Engineer", "Machine Learning Engineer"]
    if "data" in lower and "engineer" in lower:
        keywords = ["Data Engineer", "AI Engineer"]
    location = "Bengaluru"
    for city in ("mumbai", "hyderabad", "chennai", "pune", "delhi", "gurugram", "noida"):
        if city in lower:
            location = city.title()
            break
    score = min(90, 50 + len(skills) * 3 + (10 if "intern" in lower else 0))
    return {
        "skills": skills,
        "roles": ["AI/ML Engineer"],
        "years_experience": 1 if "intern" in lower else 0,
        "suggested_keywords": keywords,
        "suggested_location": location,
        "ats_score": score,
        "strengths": ["Hands-on project experience"][:1],
        "gaps": ["Add measurable impact numbers to each role"],
        "summary": "Heuristic analysis (LLM unavailable). Upload was parsed successfully.",
        "fallback_used": True,
    }


def analyze_resume(text: str) -> dict:
    text = (text or "").strip()
    if len(text) < 50:
        raise ValueError("Resume text too short to analyze (min 50 characters)")
    if not GROQ_API_KEY:
        return _fallback(text)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": ANALYZE_PROMPT.format(resume=text[:12000])}],
            temperature=0.2,
        )
        raw = resp.choices[0].message.content
        result = extract_json(raw)
        return {
            "skills": [str(s) for s in result.get("skills", [])][:15],
            "roles": [str(s) for s in result.get("roles", [])][:5],
            "years_experience": max(0, min(20, int(float(result.get("years_experience", 0) or 0)))),
            "suggested_keywords": [str(s) for s in result.get("suggested_keywords", [])][:4],
            "suggested_location": str(result.get("suggested_location", "Bengaluru")),
            "ats_score": max(0, min(100, int(float(result.get("ats_score", 0) or 0)))),
            "strengths": [str(s) for s in result.get("strengths", [])][:5],
            "gaps": [str(s) for s in result.get("gaps", [])][:5],
            "summary": str(result.get("summary", "")),
        }
    except Exception as e:
        print(f"  Resume analysis fallback -> {type(e).__name__}: {e}")
        out = _fallback(text)
        out["summary"] = f"Heuristic analysis (Groq unavailable: {type(e).__name__})."
        return out
