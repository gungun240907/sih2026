from scraper.linkedin_scraper import LinkedInScraper
from matcher.resume_matcher import score_job, filter_jobs

with open("resume.txt", "r", encoding="utf-8") as f:
    resume_text = f.read()

scraper = LinkedInScraper(keywords=["AI Engineer"], location="Bengaluru")
jobs = scraper.scrape(max_jobs=3)

print("\n--- Scoring jobs against your resume ---\n")
for job in jobs:
    job = score_job(job, resume_text)
    print(f"{job.title} | {job.company}")
    print(f"  Score       : {job.match_score:.0%}")
    print(f"  Recommend   : {job.match_meta.get('recommendation')}")
    print(f"  Reason      : {job.match_meta.get('reason')}")
    print(f"  Matched     : {job.match_meta.get('matched_skills')}")
    print(f"  Missing     : {job.match_meta.get('missing_skills')}")
    print()

print("--- After filtering (threshold 0.65) ---")
good_jobs = filter_jobs(jobs)
for j in good_jobs:
    print(f"  ✓ {j.title} | {j.company} | {j.match_score:.0%}")