import time
from scraper.linkedin_scraper import LinkedInScraper
from scraper.naukri_scraper import NaukriScraper
from matcher.resume_matcher import score_job, filter_jobs
from notifier.email_notifier import send_daily_digest
from tracker.sheets_tracker import log_jobs
from config import KEYWORDS, LOCATION, MATCH_THRESHOLD, AUTO_APPLY_THRESHOLD

def load_resume() -> str:
    with open("resume.txt", "r", encoding="utf-8") as f:
        return f.read()

def run_pipeline():
    print("=" * 50)
    print("JOB AGENT PIPELINE STARTING")
    print("=" * 50)

    resume_text = load_resume()
    all_jobs = []

    # Step 1: Scrape all portals
    print(f"\n[1/3] Scraping job portals...")

    print("  → LinkedIn")
    linkedin = LinkedInScraper(keywords=KEYWORDS, location=LOCATION)
    linkedin_jobs = linkedin.scrape(max_jobs=10)
    print(f"     Found {len(linkedin_jobs)} jobs")
    all_jobs.extend(linkedin_jobs)

    print("  → Naukri")
    naukri = NaukriScraper(keywords=KEYWORDS, location=LOCATION)
    naukri_jobs = naukri.scrape(max_jobs=10)
    print(f"     Found {len(naukri_jobs)} jobs")
    all_jobs.extend(naukri_jobs)

    print(f"\n  Total scraped: {len(all_jobs)} jobs across 2 portals")

    # Step 2: Score
    print(f"\n[2/3] Scoring {len(all_jobs)} jobs against your resume...")
    for i, job in enumerate(all_jobs):
        print(f"      {i+1}/{len(all_jobs)}: {job.title} at {job.company} [{job.source}]")
        all_jobs[i] = score_job(job, resume_text)
        time.sleep(0.5)

    # Step 3: Filter + Log
    print(f"\n[3/3] Filtering and logging to Google Sheets...")
    good_jobs = filter_jobs(all_jobs, threshold=MATCH_THRESHOLD)
    print(f"      {len(good_jobs)} jobs passed threshold out of {len(all_jobs)}")
    log_jobs(good_jobs)

    # Step 4: Send email digest for high scoring jobs
    print("\n[4/4] Sending email digest...")
    high_score_jobs = [j for j in good_jobs if j.match_score >= AUTO_APPLY_THRESHOLD]
    send_daily_digest(high_score_jobs)

    # Summary
    print("\n" + "=" * 50)
    print("PIPELINE COMPLETE — SUMMARY")
    print("=" * 50)
    for job in good_jobs:
        rec = job.match_meta.get("recommendation", "").upper()
        print(f"  [{rec}] {job.match_score:.0%} | {job.title} at {job.company} [{job.source}]")

    print(f"\nTotal logged: {len(good_jobs)}")
    print("=" * 50)

if __name__ == "__main__":
    run_pipeline()