from typing import Literal

from pydantic import BaseModel, Field

JobStatus = Literal["new", "applied", "interview", "offer", "rejected"]
Recommendation = Literal["apply", "maybe", "skip", ""]


class JobOut(BaseModel):
    id: str
    title: str
    company: str
    location: str
    url: str
    source: str
    match_score: float          # 0.0 – 1.0
    recommendation: str
    matched_skills: list[str]
    missing_skills: list[str]
    status: str
    scraped_at: str


class StatsOut(BaseModel):
    total: int
    apply_count: int
    maybe_count: int
    skip_count: int
    avg_score: float
    top_score: float
    score_bins: dict[str, int] = Field(
        description="Counts per range key: 0-50, 50-60, 60-70, 70-80, 80-90, 90-100"
    )
    recommendations: dict[str, int]


class StatusUpdate(BaseModel):
    status: JobStatus


class PipelineRunRequest(BaseModel):
    keywords: list[str] | None = None
    location: str | None = None
    match_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    auto_apply_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    max_jobs_per_portal: int | None = Field(default=None, ge=1, le=50)


class RunStartOut(BaseModel):
    run_id: str
    state: str
    message: str


class RunStatusOut(BaseModel):
    run_id: str | None
    state: Literal["idle", "running", "completed", "failed"]
    step: int
    total_steps: int
    event: str | None
    message: str | None
    started_at: str | None
    finished_at: str | None
    counters: dict[str, int]
    recent_jobs: list[dict] = []
    summary: dict | None
    error: str | None
