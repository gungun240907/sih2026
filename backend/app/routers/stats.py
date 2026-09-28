from fastapi import APIRouter

from app.schemas import StatsOut
from app.services import job_service

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("", response_model=StatsOut)
def stats():
    jobs = job_service.get_jobs()
    return job_service.get_stats(jobs)
