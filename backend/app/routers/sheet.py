from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.core.tracker import sheets_tracker

router = APIRouter(prefix="/api/sheet", tags=["sheet"])


@router.get("/url")
def sheet_url():
    """Direct browser link to the Google Sheet (opens a new tab in the UI)."""
    url = sheets_tracker.get_sheet_url()
    if not url:
        raise HTTPException(status_code=404, detail="Google Sheet is not configured or unreachable.")
    return {"url": url}


@router.get("/export")
def export_sheet(fmt: str = Query(default="csv", pattern="^(csv|xlsx)$")):
    """Download the Google Sheet as CSV or XLSX."""
    try:
        data, filename, media_type = sheets_tracker.export_sheet_bytes(fmt)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")
    return Response(content=data, media_type=media_type, headers={
        "Content-Disposition": f'attachment; filename="{filename}"',
    })
