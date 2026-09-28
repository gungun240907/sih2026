"""Single access layer for job data (Google Sheets with local JSON fallback)."""

from typing import Any

from fastapi import HTTPException

from app.core.tracker.sheets_tracker import (
    HEADERS,
    clear_sheet,
    get_sheet,
    load_local_jobs,
    update_job_status,
)
from app.schemas import JobOut, StatsOut

STATUS_VALUES = ["new", "applied", "interview", "offer", "rejected"]


def _get_sheet_or_none():
    """Return the sheet, or None when credentials/sheet are not configured yet."""
    try:
        return get_sheet()
    except Exception:
        return None


def _parse_score(raw: Any) -> float:
    """Sheet stores '85%'; return 0.85."""
    if raw is None or raw == "":
        return 0.0
    text = str(raw).replace("%", "").strip()
    try:
        value = float(text)
    except ValueError:
        return 0.0
    return value / 100.0 if value > 1.0 else value


def _split_skills(raw: Any) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(s).strip() for s in raw if str(s).strip()]
    return [s.strip() for s in str(raw).split(",") if s.strip()]


def get_jobs() -> list[JobOut]:
    sheet = _get_sheet_or_none()
    if sheet is not None:
        try:
            records: list[dict[str, Any]] = sheet.get_all_records(expected_headers=HEADERS)
            jobs = []
            for r in records:
                if not r.get("ID"):
                    continue
                jobs.append(JobOut(
                    id=str(r.get("ID", "")),
                    title=str(r.get("Title", "")),
                    company=str(r.get("Company", "")),
                    location=str(r.get("Location", "")),
                    url=str(r.get("URL", "")),
                    source=str(r.get("Source", "")),
                    match_score=_parse_score(r.get("Match Score")),
                    recommendation=str(r.get("Recommendation", "")).lower(),
                    matched_skills=_split_skills(r.get("Matched Skills")),
                    missing_skills=_split_skills(r.get("Missing Skills")),
                    status=str(r.get("Status", "new")).lower(),
                    scraped_at=str(r.get("Scraped At", "")),
                ))
            if jobs:
                return jobs
        except Exception as e:
            print(f"Reading from Google Sheets failed ({e}), falling back to local storage")

    # Fallback to local storage (jobs.json)
    local_records = load_local_jobs()
    jobs = []
    for r in local_records:
        if not r.get("id"):
            continue
        jobs.append(JobOut(
            id=str(r.get("id", "")),
            title=str(r.get("title", "")),
            company=str(r.get("company", "")),
            location=str(r.get("location", "")),
            url=str(r.get("url", "")),
            source=str(r.get("source", "")),
            match_score=float(r.get("match_score", 0.0)),
            recommendation=str(r.get("recommendation", "")).lower(),
            matched_skills=_split_skills(r.get("matched_skills")),
            missing_skills=_split_skills(r.get("missing_skills")),
            status=str(r.get("status", "new")).lower(),
            scraped_at=str(r.get("scraped_at", "")),
        ))
    return jobs


def get_stats(jobs: list[JobOut]) -> StatsOut:
    total = len(jobs)
    scores = [j.match_score for j in jobs]
    bins = {"0-50": 0, "50-60": 0, "60-70": 0, "70-80": 0, "80-90": 0, "90-100": 0}
    for s in scores:
        pct = s * 100
        if pct < 50:
            bins["0-50"] += 1
        elif pct < 60:
            bins["50-60"] += 1
        elif pct < 70:
            bins["60-70"] += 1
        elif pct < 80:
            bins["70-80"] += 1
        elif pct < 90:
            bins["80-90"] += 1
        else:
            bins["90-100"] += 1

    recs = {"apply": 0, "maybe": 0, "skip": 0}
    for j in jobs:
        if j.recommendation in recs:
            recs[j.recommendation] += 1

    return StatsOut(
        total=total,
        apply_count=recs["apply"],
        maybe_count=recs["maybe"],
        skip_count=recs["skip"],
        avg_score=(sum(scores) / total) if total else 0.0,
        top_score=max(scores) if scores else 0.0,
        score_bins=bins,
        recommendations=recs,
    )


def set_status(job_id: str, status: str) -> None:
    if status not in STATUS_VALUES:
        raise HTTPException(status_code=422, detail=f"Invalid status '{status}'")
    update_job_status(job_id, status)


def clear() -> None:
    clear_sheet()

