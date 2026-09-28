import sys

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, 'reconfigure'):
        _s.reconfigure(encoding='utf-8', errors='replace')

from scraper.linkedin_scraper import LinkedInScraper
from matcher.resume_matcher import score_job
from tracker.sheets_tracker import log_jobs
with open("resume.txt", "r", encoding="utf-8") as f:
    resume_text = f.read()
scraper = LinkedInScraper(keywords=["AI Engineer"], location="Bengaluru")
jobs = scraper.scrape(max_jobs=3)

print("Scoring jobs...")
for i, job in enumerate(jobs):
    jobs[i] = score_job(job, resume_text)

print("Logging to Google Sheets...")
log_jobs(jobs)
print("Done! Check your Google Sheet.")