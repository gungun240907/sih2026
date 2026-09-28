"""Refactored pipeline orchestrator.

run_pipeline() is callable from the FastAPI background runner or the CLI.
It reports progress through an optional callback and never blocks on UI.
"""

import time
from datetime import datetime
from typing import Any, Callable

from app.config import (
    DEFAULT_AUTO_APPLY_THRESHOLD,
    DEFAULT_KEYWORDS,
    DEFAULT_LOCATION,
    DEFAULT_MATCH_THRESHOLD,
    DEFAULT_MAX_JOBS_PER_PORTAL,
    RESUME_FILE,
)
from app.core.matcher.resume_matcher import filter_jobs, score_job
from app.core.notifier.email_notifier import send_daily_digest
from app.core.scraper.linkedin_scraper import LinkedInScraper
from app.core.scraper.naukri_scraper import NaukriScraper
from app.core.tracker.models import Job
from app.core.tracker.sheets_tracker import is_sheets_configured, log_jobs

ProgressFn = Callable[[dict[str, Any]], None]


def load_resume() -> str:
    with open(RESUME_FILE, "r", encoding="utf-8") as f:
        return f.read()


def run_pipeline(
    progress: ProgressFn | None = None,
    *,
    keywords: list[str] | None = None,
    location: str | None = None,
    match_threshold: float = DEFAULT_MATCH_THRESHOLD,
    auto_apply_threshold: float = DEFAULT_AUTO_APPLY_THRESHOLD,
    max_jobs_per_portal: int = DEFAULT_MAX_JOBS_PER_PORTAL,
    resume_id: str | None = None,
    resume_text: str | None = None,
) -> dict[str, Any]:
    """Run the full agent pipeline and return a summary dict.

    progress receives dicts like:
      {"step": 1, "total_steps": 4, "event": "scrape_start", "message": "...", "data": {...}}
    """
    def emit(step: int, event: str, message: str, data: dict | None = None):
        if progress:
            progress({
                "step": step,
                "total_steps": 4,
                "event": event,
                "message": message,
                "data": data or {},
            })

    keywords = keywords or DEFAULT_KEYWORDS
    location = location or DEFAULT_LOCATION

    from app.core.resume import store as resume_store

    resume_text, resume_source = resume_store.resolve_text(resume_id, resume_text)
    all_jobs: list[Job] = []

    # Step 1: Scrape all portals (LinkedIn left Chrome window, Naukri right)
    emit(1, "scrape_start", f"Scraping LinkedIn and Naukri for '{', '.join(keywords)}' in {location}")

    def on_scrape_event(source, msg, job):
        data = {"source": source, "message": msg}
        if job is not None:
            data.update({"job_title": job.title, "job_company": job.company,
                         "job_url": job.url})
        emit(1, "scrape_job", msg, data)

    linkedin = LinkedInScraper(keywords=keywords, location=location)
    linkedin_jobs = linkedin.scrape(max_jobs=max_jobs_per_portal, headless=False,
                                    position="left", on_event=on_scrape_event)
    emit(1, "scrape_portal", f"LinkedIn: found {len(linkedin_jobs)} jobs", {"source": "linkedin", "found": len(linkedin_jobs)})
    all_jobs.extend(linkedin_jobs)

    naukri = NaukriScraper(keywords=keywords, location=location)
    naukri_jobs = naukri.scrape(max_jobs=max_jobs_per_portal, headless=False,
                                position="right", on_event=on_scrape_event)
    emit(1, "scrape_portal", f"Naukri: found {len(naukri_jobs)} jobs", {"source": "naukri", "found": len(naukri_jobs)})
    all_jobs.extend(naukri_jobs)

    emit(1, "scrape_done", f"Total scraped: {len(all_jobs)} jobs across 2 portals", {"total": len(all_jobs)})

    # No listings in this city: stop here (no LLM spend, no empty digest).
    if not all_jobs:
        note = f"No jobs available right now in {location}"
        emit(1, "no_jobs", note, {"total": 0, "location": location})
        summary = {
            "finished_at": datetime.now().isoformat(),
            "total_scraped": 0,
            "score_failures": 0,
            "total_logged": 0,
            "notified": 0,
            "location": location,
            "note": note,
            "jobs": [],
        }
        emit(4, "pipeline_complete", note, summary)
        return summary

    # Step 2: Score
    emit(2, "score_start", f"Scoring {len(all_jobs)} jobs against your resume", {"total": len(all_jobs)})
    score_failures = 0
    for i, job in enumerate(all_jobs):
        all_jobs[i] = score_job(job, resume_text)
        if all_jobs[i].match_meta.get("score_error"):
            score_failures += 1
        emit(2, "score_progress", f"Scored {i + 1}/{len(all_jobs)}: {job.title} at {job.company}",
             {"done": i + 1, "total": len(all_jobs)})
        time.sleep(0.5)
    if score_failures:
        emit(2, "score_done",
             f"Scored {len(all_jobs)} jobs - {score_failures} could not be scored (LLM/JSON error) and were excluded",
             {"total": len(all_jobs), "failed": score_failures})
    else:
        emit(2, "score_done", f"Scored {len(all_jobs)} jobs", {"total": len(all_jobs)})

    # Step 3: Filter + Log
    good_jobs = filter_jobs(all_jobs, threshold=match_threshold)
    emit(3, "filter_done", f"{len(good_jobs)} jobs passed the {match_threshold:.0%} threshold",
         {"passed": len(good_jobs), "total": len(all_jobs)})
    logged_count = log_jobs(good_jobs)
    dest = "Google Sheets & local database" if is_sheets_configured() else "local database (Google Sheets not configured)"
    emit(3, "log_done", f"Logged {logged_count} jobs to {dest}", {"logged": logged_count})

    # Step 4: Email digest for high scoring jobs
    high_score_jobs = [j for j in good_jobs if j.match_score >= auto_apply_threshold]
    send_daily_digest(high_score_jobs)
    emit(4, "notify_done", f"Email digest sent for {len(high_score_jobs)} priority jobs",
         {"notified": len(high_score_jobs)})

    summary = {
        "finished_at": datetime.now().isoformat(),
        "total_scraped": len(all_jobs),
        "score_failures": score_failures,
        "total_logged": len(good_jobs),
        "notified": len(high_score_jobs),
        "location": location,
        "resume_source": resume_source,
        "jobs": [
            {
                "id": j.id,
                "title": j.title,
                "company": j.company,
                "score": round(j.match_score, 4),
                "recommendation": j.match_meta.get("recommendation", ""),
            }
            for j in good_jobs
        ],
    }
    emit(4, "pipeline_complete", "Pipeline complete", summary)
    return summary
