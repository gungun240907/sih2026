"""Resume endpoints: view/edit resume.txt, upload pdf/image/text, analyze, export."""

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, UploadFile
from fastapi.responses import Response

from app import schemas
from app.config import RESUME_FILE
from app.core.resume import analyzer, exporter, parser, store

router = APIRouter(prefix="/api/resume", tags=["resume"])


def _read_resume() -> tuple[str, Path]:
    path = Path(RESUME_FILE)
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"Resume file not found: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read resume: {e}")
    return text, path


def _write_default_resume(text: str) -> Path:
    """Overwrite resume.txt (the default resume), keeping a timestamped backup."""
    path = Path(RESUME_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        backup = path.with_name(
            f"{path.stem}.bak-{datetime.now().strftime('%Y%m%d-%H%M%S')}{path.suffix}"
        )
        backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.write_text(text, encoding="utf-8")
    return path


@router.get("", response_model=schemas.ResumeOut)
def get_resume():
    text, path = _read_resume()
    return schemas.ResumeOut(text=text, char_count=len(text), source=path.name)


@router.put("", response_model=schemas.ResumeOut)
def update_resume(body: schemas.ResumeUpdate):
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Resume text must not be empty")
    try:
        path = _write_default_resume(text)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save resume: {e}")
    return schemas.ResumeOut(text=text, char_count=len(text), source=path.name)


@router.post("/upload", response_model=schemas.ResumeUploadOut)
async def upload_resume(file: UploadFile):
    data = await file.read()
    try:
        text, warning = parser.extract_text(file.filename or "resume.txt", data)
    except parser.ParseError as e:
        raise HTTPException(status_code=422, detail=str(e))
    try:
        # an upload in any format becomes the new default resume
        _write_default_resume(text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update default resume: {e}")
    saved = store.save_upload(text, file.filename or "resume.txt")
    store.set_active(saved["resume_id"])
    return schemas.ResumeUploadOut(
        resume_id=saved["resume_id"],
        filename=saved["filename"],
        char_count=saved["char_count"],
        text_preview=saved["text_preview"],
        warning=warning,
    )


@router.post("/analyze", response_model=schemas.ResumeAnalysisOut)
def analyze(body: schemas.ResumeAnalyzeRequest):
    try:
        if body.resume_id:
            text = store.get_text(body.resume_id)
            rid = body.resume_id
        elif body.text and body.text.strip():
            text, rid = body.text.strip(), None
        else:
            active = store.get_active_id()
            if active:
                text, rid = store.get_text(active), active
            else:
                text, _ = _read_resume()
                rid = None
        result = analyzer.analyze_resume(text)
        return schemas.ResumeAnalysisOut(resume_id=rid, **{
            k: result.get(k) for k in (
                "skills", "roles", "years_experience", "suggested_keywords",
                "suggested_location", "ats_score", "strengths", "gaps",
                "summary", "fallback_used",
            ) if k in result
        } | {"fallback_used": bool(result.get("fallback_used", False))})
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/uploads")
def list_uploads():
    return {"uploads": store.list_uploads(), "active_id": store.get_active_id()}


@router.get("/active")
def get_active():
    rid = store.get_active_id()
    if not rid:
        text, path = _read_resume()
        return {"resume_id": None, "source": path.name, "char_count": len(text)}
    try:
        text = store.get_text(rid)
    except FileNotFoundError:
        text, path = _read_resume()
        return {"resume_id": None, "source": path.name, "char_count": len(text)}
    return {"resume_id": rid, "source": f"upload:{rid}", "char_count": len(text)}


@router.post("/active")
def set_active(body: schemas.ActiveResumeRequest):
    try:
        return store.set_active(body.resume_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/export")
def export_resume(
    format: str = Query(default="md", pattern="^(md|txt|pdf)$"),
    resume_id: str | None = None,
):
    try:
        if resume_id:
            text, source = store.get_text(resume_id), f"upload:{resume_id}"
        else:
            active = store.get_active_id()
            if active:
                try:
                    text, source = store.get_text(active), f"upload:{active}"
                except FileNotFoundError:
                    text, path = _read_resume()
                    source = path.name
            else:
                text, path = _read_resume()
                source = path.name
        analysis = analyzer.analyze_resume(text)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if format == "pdf":
        return Response(
            content=exporter.to_pdf(text, analysis, source),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=resume-analysis.{format}"},
        )
    body = exporter.to_markdown(text, analysis, source) if format == "md" else exporter.to_txt(text, analysis, source)
    return Response(
        content=body,
        media_type="text/markdown" if format == "md" else "text/plain",
        headers={"Content-Disposition": f"attachment; filename=resume-analysis.{format}"},
    )
