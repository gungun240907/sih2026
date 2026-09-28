from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import CORS_ORIGINS
from app.routers import jobs, pipeline, resume, sheet, stats

app = FastAPI(
    title="Job Application Agent API",
    version="2.0.0",
    description="FastAPI backend for the job scraping / LLM scoring / tracking agent",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router)
app.include_router(pipeline.router)
app.include_router(resume.router)
app.include_router(sheet.router)
app.include_router(stats.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# ── Production: serve the built React app if present ─────────
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    return JSONResponse(status_code=500, content={"detail": str(exc)})
