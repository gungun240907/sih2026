import json
import os
from pathlib import Path
from typing import Any
import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as OAuthCredentials
from google.oauth2.service_account import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from app.config import BASE_DIR, CREDENTIALS_FILE, GOOGLE_SHEET_NAME
from app.core.tracker.models import Job

OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
OAUTH_CLIENT_FILE = Path(os.getenv("OAUTH_CLIENT_FILE", BASE_DIR / "oauth_client.json"))
OAUTH_TOKEN_FILE = Path(os.getenv("OAUTH_TOKEN_FILE", BASE_DIR / "token.json"))
OAUTH_PORT = int(os.getenv("OAUTH_PORT", "8765"))

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

HEADERS = [
    "ID", "Title", "Company", "Location", "URL",
    "Source", "Match Score", "Recommendation",
    "Matched Skills", "Missing Skills", "Status", "Scraped At"
]

LOCAL_STORAGE_FILE = BASE_DIR / "jobs.json"


def load_local_jobs() -> list[dict[str, Any]]:
    """Load cached jobs from local JSON file."""
    if not LOCAL_STORAGE_FILE.is_file():
        return []
    try:
        with open(LOCAL_STORAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Warning: could not read {LOCAL_STORAGE_FILE}: {e}")
        return []


def save_local_jobs(jobs: list[dict[str, Any]]) -> None:
    """Persist jobs list to local JSON file."""
    try:
        with open(LOCAL_STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: could not write to {LOCAL_STORAGE_FILE}: {e}")


def is_sheets_configured() -> bool:
    """Check if credentials.json is present on disk."""
    return bool(CREDENTIALS_FILE and Path(CREDENTIALS_FILE).is_file())


def get_oauth_credentials():
    """User-OAuth credentials (Desktop app flow, token cached in backend/token.json)."""
    creds = None
    if OAUTH_TOKEN_FILE.is_file():
        try:
            creds = OAuthCredentials.from_authorized_user_file(str(OAUTH_TOKEN_FILE), OAUTH_SCOPES)
        except Exception as e:
            print(f"Saved OAuth token unreadable ({e}) - re-authenticating.")
            creds = None
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as e:
            print(f"OAuth token refresh failed ({e}) - re-authenticating.")
            creds = None
    if not creds or not creds.valid:
        if not OAUTH_CLIENT_FILE.is_file():
            return None
        print("No valid OAuth token - opening browser for Google sign-in...")
        flow = InstalledAppFlow.from_client_secrets_file(str(OAUTH_CLIENT_FILE), OAUTH_SCOPES)
        creds = flow.run_local_server(port=OAUTH_PORT)
        with open(OAUTH_TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
        print(f"OAuth token saved to {OAUTH_TOKEN_FILE}.")
    return creds


def get_spreadsheet():
    """Return the gspread Spreadsheet object (for URL / export)."""
    # 1) User OAuth (Desktop app)
    try:
        creds = get_oauth_credentials()
        if creds:
            gc = gspread.authorize(creds)
            return gc.open(GOOGLE_SHEET_NAME)
    except Exception as e:
        print(f"OAuth Sheets unavailable ({e}). Trying service account...")
    # 2) Service account
    if CREDENTIALS_FILE and Path(CREDENTIALS_FILE).is_file():
        try:
            creds = Credentials.from_service_account_file(str(CREDENTIALS_FILE), scopes=SCOPES)
            gc = gspread.authorize(creds)
            return gc.open(GOOGLE_SHEET_NAME)
        except Exception as e:
            print(f"Google Sheets unavailable ({e}).")
    return None


def get_sheet_url() -> str | None:
    """Direct browser link to the Google Sheet, or None if unavailable."""
    try:
        ss = get_spreadsheet()
        return ss.url if ss else None
    except Exception as e:
        print(f"Could not get sheet URL: {e}")
        return None


def export_sheet_bytes(fmt: str = "csv") -> tuple[bytes, str, str]:
    """Export the sheet; returns (data, filename, media_type)."""
    from gspread.utils import ExportFormat
    ss = get_spreadsheet()
    if ss is None:
        raise FileNotFoundError("Google Sheet is not configured or unreachable.")
    if fmt == "xlsx":
        data = ss.export(format=ExportFormat.EXCEL)
        return bytes(data), "job_applications.xlsx", \
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    data = ss.export(format=ExportFormat.CSV)
    return bytes(data), "job_applications.csv", "text/csv"


def get_sheet():
    """Return gspread Sheet object or None if not configured.

    Tries user-OAuth first (verified working), then service account,
    then None (local JSON storage fallback).
    """
    # 1) User OAuth (Desktop app)
    try:
        creds = get_oauth_credentials()
        if creds:
            gc = gspread.authorize(creds)
            return gc.open(GOOGLE_SHEET_NAME).sheet1
    except Exception as e:
        print(f"OAuth Sheets unavailable ({e}). Trying service account...")
    # 2) Service account
    if not is_sheets_configured():
        return None
    try:
        creds = Credentials.from_service_account_file(str(CREDENTIALS_FILE), scopes=SCOPES)
        gc = gspread.authorize(creds)
        return gc.open(GOOGLE_SHEET_NAME).sheet1
    except Exception as e:
        print(f"Google Sheets unavailable ({e}). Using local storage fallback.")
        return None


def setup_headers():
    sheet = get_sheet()
    if not sheet:
        return
    try:
        first_row = [c.strip() for c in sheet.row_values(1)]
        if first_row != HEADERS:
            if first_row:
                print("Header row did not match - rewriting row 1 in place.")
            sheet.update([HEADERS], "A1")
            print("Headers added to sheet.")
    except Exception as e:
        print(f"Could not setup sheet headers: {e}")


def get_existing_ids() -> set[str]:
    ids: set[str] = set()
    # Check local store
    for j in load_local_jobs():
        if j.get("id"):
            ids.add(str(j["id"]))

    # Also check Google Sheets if configured
    sheet = get_sheet()
    if sheet:
        try:
            sheet_ids = sheet.col_values(1)[1:]  # skip header
            ids.update(sheet_ids)
        except Exception:
            pass
    return ids


def log_jobs(jobs: list[Job]) -> int:
    existing_ids = get_existing_ids()
    local_jobs = load_local_jobs()

    new_local: list[dict[str, Any]] = []
    rows_to_add: list[list[Any]] = []

    for job in jobs:
        if job.id in existing_ids:
            print(f"  Skipping duplicate: {job.title} at {job.company}")
            continue
        existing_ids.add(job.id)

        job_dict = {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "url": job.url,
            "source": job.source,
            "match_score": job.match_score,
            "recommendation": job.match_meta.get("recommendation", ""),
            "matched_skills": job.match_meta.get("matched_skills", []),
            "missing_skills": job.match_meta.get("missing_skills", []),
            "status": job.status,
            "scraped_at": job.scraped_at,
        }
        new_local.append(job_dict)

        rows_to_add.append([
            job.id,
            job.title,
            job.company,
            job.location,
            job.url,
            job.source,
            f"{job.match_score:.0%}",
            job.match_meta.get("recommendation", ""),
            ", ".join(job.match_meta.get("matched_skills", [])),
            ", ".join(job.match_meta.get("missing_skills", [])),
            job.status,
            job.scraped_at,
        ])
        print(f"  Logged: {job.title} at {job.company}")

    # Always persist locally
    if new_local:
        local_jobs.extend(new_local)
        save_local_jobs(local_jobs)
        print(f"  Wrote {len(new_local)} jobs to local storage ({LOCAL_STORAGE_FILE.name})")

    # Sync with Google Sheets if configured
    sheet = get_sheet()
    if sheet and rows_to_add:
        try:
            setup_headers()
            sheet.append_rows(rows_to_add)
            print(f"  Wrote {len(rows_to_add)} rows to Google Sheet in one batch")
        except Exception as e:
            print(f"  Failed writing to Google Sheet: {e} (saved locally)")
    elif not sheet:
        print("  (Google Sheets not configured - jobs safely stored in local database)")

    return len(new_local)


def log_job(job: Job):
    log_jobs([job])


def clear_sheet():
    # Clear local storage
    save_local_jobs([])
    print("Local jobs storage cleared.")

    # Clear Google Sheets if configured
    sheet = get_sheet()
    if sheet:
        try:
            sheet.clear()
            setup_headers()
            print("Google Sheet cleared and headers reset.")
        except Exception as e:
            print(f"Failed clearing Google Sheet: {e}")


def update_job_status(job_id: str, new_status: str):
    # Update local storage
    local_jobs = load_local_jobs()
    updated = False
    for j in local_jobs:
        if j.get("id") == job_id:
            j["status"] = new_status
            updated = True
            break
    if updated:
        save_local_jobs(local_jobs)
        print(f"Updated {job_id} to '{new_status}' in local storage")

    # Update Google Sheets if configured
    sheet = get_sheet()
    if sheet:
        try:
            cell = sheet.find(job_id)
            if cell:
                status_col = HEADERS.index("Status") + 1
                sheet.update_cell(cell.row, status_col, new_status)
                print(f"Updated {job_id} to '{new_status}' in Google Sheet")
            else:
                print(f"Job ID {job_id} not found in sheet")
        except Exception as e:
            print(f"Failed updating Google Sheet: {e}")