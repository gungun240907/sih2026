from fastapi import APIRouter, HTTPException, Query

from app.schemas import JobOut, StatusUpdate
from app.services import job_service

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=list[JobOut])
def list_jobs(
    recommendation: list[str] | None = Query(default=None),
    status: list[str] | None = Query(default=None),
    min_score: float = Query(default=0.0, ge=0.0, le=1.0),
    sort: str = Query(default="score_desc", pattern="^(score_desc|score_asc|recent)$"),
):
    jobs = job_service.get_jobs()

    if recommendation:
        jobs = [j for j in jobs if j.recommendation in recommendation]
    if status:
        jobs = [j for j in jobs if j.status in status]
    jobs = [j for j in jobs if j.match_score >= min_score]

    if sort == "score_desc":
        jobs.sort(key=lambda j: j.match_score, reverse=True)
    elif sort == "score_asc":
        jobs.sort(key=lambda j: j.match_score)
    elif sort == "recent":
        jobs.sort(key=lambda j: j.scraped_at, reverse=True)
    return jobs


@router.patch("/{job_id}/status", response_model=JobOut)
def update_status(job_id: str, body: StatusUpdate):
    jobs = job_service.get_jobs()
    job = next((j for j in jobs if j.id == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    job_service.set_status(job_id, body.status)
    job.status = body.status
    return job


@router.delete("", response_model=dict)
def clear_all():
    job_service.clear()
    return {"ok": True, "message": "Sheet cleared"}
