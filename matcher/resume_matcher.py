import json
from openai import OpenAI
from config import GROQ_API_KEY, GROQ_MODEL
from tracker.models import Job
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

def score_job(job: Job, resume_text: str) -> Job:
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{
                "role": "user",
                "content": SCORE_PROMPT.format(
                    resume=resume_text,
                    jd=job.description
                )
            }],
            temperature=0.1,
        )
        raw = response.choices[0].message.content.strip()
        result = json.loads(raw)
        job.match_score = float(result.get("score", 0.0))
        job.match_meta = result
    except Exception as e:
        print(f"Scoring failed for {job.title} at {job.company}: {e}")
        job.match_score = 0.0
        job.match_meta = {}
    return job


def filter_jobs(jobs: list[Job], threshold: float = 0.65) -> list[Job]:
    filtered = []
    for j in jobs:
        exp_req = j.match_meta.get("experience_required", 0)
        if exp_req > 20:
            exp_req = 0
        if exp_req > 2:
            print(f"  Skipping (requires {exp_req} yrs): {j.title} at {j.company}")
            continue

        if j.match_score >= threshold:
            filtered.append(j)
    return filtered