"""Disk store for uploaded resumes (gitignored uploads/ dir)."""

import json
import uuid
from datetime import datetime
from pathlib import Path

from app.config import BASE_DIR

UPLOAD_DIR = BASE_DIR / "uploads"
ACTIVE_FILE = UPLOAD_DIR / "active.json"


def _ensure() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def save_upload(text: str, orig_filename: str) -> dict:
    _ensure()
    rid = uuid.uuid4().hex[:12]
    (UPLOAD_DIR / f"{rid}.txt").write_text(text, encoding="utf-8")
    meta = {
        "resume_id": rid,
        "filename": orig_filename,
        "char_count": len(text),
        "created_at": datetime.now().isoformat(),
    }
    (UPLOAD_DIR / f"{rid}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {"resume_id": rid, **meta, "text_preview": text[:500]}


def get_text(resume_id: str) -> str:
    _ensure()
    path = UPLOAD_DIR / f"{resume_id}.txt"
    if not path.is_file():
        raise FileNotFoundError(f"Unknown resume_id {resume_id!r}")
    return path.read_text(encoding="utf-8")


def list_uploads() -> list[dict]:
    _ensure()
    out = []
    for meta_path in sorted(UPLOAD_DIR.glob("*.json"), reverse=True):
        if meta_path.name == "active.json":
            continue
        try:
            out.append(json.loads(meta_path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return out


def set_active(resume_id: str) -> dict:
    get_text(resume_id)  # validates existence
    _ensure()
    ACTIVE_FILE.write_text(json.dumps({"resume_id": resume_id}), encoding="utf-8")
    return {"resume_id": resume_id}


def get_active_id() -> str | None:
    if not ACTIVE_FILE.is_file():
        return None
    try:
        return json.loads(ACTIVE_FILE.read_text(encoding="utf-8")).get("resume_id")
    except Exception:
        return None


def resolve_text(resume_id: str | None, resume_text: str | None) -> tuple[str, str]:
    """Priority: explicit text > resume_id > active upload > resume.txt."""
    if resume_text and resume_text.strip():
        return resume_text.strip(), "request-text"
    if resume_id:
        return get_text(resume_id), f"upload:{resume_id}"
    active = get_active_id()
    if active:
        try:
            return get_text(active), f"upload:{active}"
        except FileNotFoundError:
            pass
    from app.core.pipeline import load_resume  # deferred to avoid circular import

    return load_resume(), "resume.txt"
