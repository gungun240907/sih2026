from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.cities import normalize_city

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
    resume_id: str | None = None
    resume_text: str | None = Field(default=None, max_length=50000)

    @field_validator("location")
    @classmethod
    def _validate_location(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return normalize_city(v)  # raises ValueError -> 422 on unsupported cities


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


class ResumeOut(BaseModel):
    text: str
    char_count: int
    source: str = "resume.txt"


class ResumeUpdate(BaseModel):
    text: str = Field(min_length=1, max_length=50000)


class ResumeUploadOut(BaseModel):
    resume_id: str
    filename: str
    char_count: int
    text_preview: str
    warning: str | None = None


class ResumeAnalysisOut(BaseModel):
    resume_id: str | None = None
    skills: list[str] = []
    roles: list[str] = []
    years_experience: int = 0
    suggested_keywords: list[str] = []
    suggested_location: str = "Bengaluru"
    ats_score: int = 0
    strengths: list[str] = []
    gaps: list[str] = []
    summary: str = ""
    fallback_used: bool = False


class ResumeAnalyzeRequest(BaseModel):
    resume_id: str | None = None
    text: str | None = Field(default=None, max_length=50000)


class ActiveResumeRequest(BaseModel):
    resume_id: str
