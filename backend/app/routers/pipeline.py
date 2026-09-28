from fastapi import APIRouter, HTTPException, Query

from app import schemas
from app.run_manager import PipelineAlreadyRunningError, run_manager
from app.config import (
    DEFAULT_AUTO_APPLY_THRESHOLD,
    DEFAULT_KEYWORDS,
    DEFAULT_LOCATION,
    DEFAULT_MATCH_THRESHOLD,
    DEFAULT_MAX_JOBS_PER_PORTAL,
)

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@router.post("/run", response_model=schemas.RunStartOut)
def start_run(req: schemas.PipelineRunRequest):
    params = {
        "keywords": req.keywords or DEFAULT_KEYWORDS,
        "location": req.location or DEFAULT_LOCATION,
        "match_threshold": req.match_threshold if req.match_threshold is not None else DEFAULT_MATCH_THRESHOLD,
        "auto_apply_threshold": req.auto_apply_threshold if req.auto_apply_threshold is not None else DEFAULT_AUTO_APPLY_THRESHOLD,
        "max_jobs_per_portal": req.max_jobs_per_portal or DEFAULT_MAX_JOBS_PER_PORTAL,
    }
    try:
        return run_manager.start(params)
    except PipelineAlreadyRunningError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/status", response_model=schemas.RunStatusOut)
def run_status():
    return run_manager.snapshot()


@router.get("/stream")
async def run_stream():
    """SSE stream of pipeline run state. Polls the in-memory snapshot every second."""
    import asyncio
    import json

    from fastapi.responses import StreamingResponse

    async def event_gen():
        last_payload = None
        idle_heartbeats = 0
        while True:
            snap = run_manager.snapshot()
            payload = {
                "state": snap["state"],
                "step": snap["step"],
                "total_steps": snap["total_steps"],
                "event": snap["event"],
                "message": snap["message"],
                "started_at": snap["started_at"],
                "finished_at": snap["finished_at"],
                "counters": snap["counters"],
                "recent_jobs": snap.get("recent_jobs", []),
                "error": snap["error"],
            }
            if payload != last_payload:
                last_payload = payload
                idle_heartbeats = 0
                yield f"data: {json.dumps(payload)}\n\n"
            else:
                idle_heartbeats += 1
                if idle_heartbeats % 15 == 0:  # keep the connection alive
                    yield ": keep-alive\n\n"

            if snap["state"] in ("completed", "failed"):
                # send final state, then a terminal summary frame and stop
                final = {**payload, "summary": snap["summary"]}
                yield f"data: {json.dumps(final)}\n\n"
                yield "event: end\ndata: {}\n\n"
                return
            await asyncio.sleep(1.0)

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
