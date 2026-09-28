"""Background pipeline runner.

Playwright's sync API cannot run inside the asyncio event loop, so the
pipeline runs in a dedicated daemon thread. State is kept in memory and
exposed via snapshot() for the status endpoint and the SSE stream.
"""

import threading
import uuid
from datetime import datetime
from typing import Any

from app.core.pipeline import run_pipeline

_IDLE: dict[str, Any] = {
    "run_id": None,
    "state": "idle",
    "step": 0,
    "total_steps": 4,
    "event": None,
    "message": None,
    "started_at": None,
    "finished_at": None,
    "counters": {},
    "recent_jobs": [],
    "summary": None,
    "error": None,
}


class PipelineAlreadyRunningError(RuntimeError):
    pass


class RunManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._state: dict[str, Any] = dict(_IDLE, counters={})
        self._thread: threading.Thread | None = None

    def start(self, params: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            if self._state["state"] == "running":
                raise PipelineAlreadyRunningError("A pipeline run is already in progress")
            run_id = uuid.uuid4().hex[:12]
            self._state = {
                "run_id": run_id,
                "state": "running",
                "step": 0,
                "total_steps": 4,
                "event": "accepted",
                "message": "Pipeline run accepted",
                "started_at": datetime.now().isoformat(),
                "finished_at": None,
                "counters": {},
                "recent_jobs": [],
                "summary": None,
                "error": None,
            }
            self._thread = threading.Thread(
                target=self._run, args=(run_id, params), daemon=True
            )
        self._thread.start()
        return {"run_id": run_id, "state": "running", "message": "Pipeline started"}

    def _run(self, run_id: str, params: dict[str, Any]):
        def progress(event: dict[str, Any]):
            data = event.get("data", {}) or {}
            counters_update = {}
            if "found" in data:
                source = data.get("source")
                if source:
                    counters_update[f"found_{source}"] = data["found"]
            if "total" in data:
                counters_update["total_scraped"] = data["total"]
            if "done" in data and "total" in data and event["event"] == "score_progress":
                counters_update["jobs_scored"] = data["done"]
                counters_update["jobs_to_score"] = data["total"]
            if "failed" in data:
                counters_update["score_failures"] = data["failed"]
            if "logged" in data:
                counters_update["logged"] = data["logged"]
            if "notified" in data:
                counters_update["notified"] = data["notified"]

            with self._lock:
                if self._state["run_id"] != run_id:
                    return
                self._state.update({
                    "step": event.get("step", self._state["step"]),
                    "event": event.get("event"),
                    "message": event.get("message"),
                })
                self._state["counters"].update(counters_update)
                # live per-job feed for the /live page (LinkedIn vs Naukri panels)
                if event.get("event") == "scrape_job" and data.get("job_title"):
                    feed = self._state.setdefault("recent_jobs", [])
                    feed.append({
                        "source": data.get("source"),
                        "title": data.get("job_title"),
                        "company": data.get("job_company"),
                        "url": data.get("job_url"),
                        "message": event.get("message"),
                    })
                    del feed[:-30]

        try:
            summary = run_pipeline(progress, **params)
            with self._lock:
                if self._state["run_id"] == run_id:
                    # surface the pipeline's own closing note (e.g. the
                    # "no jobs in this city" message) instead of a generic one
                    closing = summary.get("note") or "Pipeline complete"
                    self._state.update({
                        "state": "completed",
                        "event": "pipeline_complete",
                        "message": closing,
                        "finished_at": datetime.now().isoformat(),
                        "summary": summary,
                    })
        except Exception as e:  # surface any failure to the UI
            with self._lock:
                if self._state["run_id"] == run_id:
                    self._state.update({
                        "state": "failed",
                        "event": "pipeline_failed",
                        "message": f"Pipeline failed: {e}",
                        "error": str(e),
                        "finished_at": datetime.now().isoformat(),
                    })

    def reset(self) -> None:
        with self._lock:
            if self._state["state"] != "running":
                self._state = dict(_IDLE, counters={})

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            # Auto-reset completed/failed state back to idle after 8s so UI settles cleanly
            if self._state["state"] in ("completed", "failed") and self._state.get("finished_at"):
                try:
                    fin = datetime.fromisoformat(self._state["finished_at"])
                    if (datetime.now() - fin).total_seconds() > 8:
                        self._state = dict(_IDLE, counters={})
                except Exception:
                    pass
            return {
                **self._state,
                "counters": dict(self._state["counters"]),
                "recent_jobs": list(self._state.get("recent_jobs", [])),
            }


run_manager = RunManager()
