import sys

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, 'reconfigure'):
        _s.reconfigure(encoding='utf-8', errors='replace')

from notifier.email_notifier import send_daily_digest
from tracker.models import Job
from datetime import datetime

# Fake job to test email
test_job = Job(
    title="AI Engineer",
    company="Test Company",
    location="Bengaluru",
    url="https://linkedin.com",
    description="Test description",
    source="test",
    scraped_at=datetime.now().isoformat(),
    match_score=0.85,
    match_meta={
        "recommendation": "apply",
        "matched_skills": ["Python", "ML"],
        "missing_skills": ["LangChain"]
    }
)

send_daily_digest([test_job])