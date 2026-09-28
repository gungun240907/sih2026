import os
import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from gspread.utils import ExportFormat
from config import GOOGLE_SHEET_NAME
from tracker.models import Job

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

CLIENT_SECRETS_FILE = "oauth_client.json"
TOKEN_FILE = "token.json"
OAUTH_PORT = 8765

HEADERS = [
    "ID", "Title", "Company", "Location", "URL",
    "Source", "Match Score", "Recommendation",
    "Matched Skills", "Missing Skills", "Status", "Scraped At"
]

def get_credentials():
    creds = None

    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f"Saved token is unreadable ({e}) — re-authenticating.")
            creds = None

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as e:
            print(f"Token refresh failed ({e}) — re-authenticating.")
            creds = None

    if not creds or not creds.valid:
        if not os.path.exists(CLIENT_SECRETS_FILE):
            raise FileNotFoundError(
                f"Missing {CLIENT_SECRETS_FILE}. In Google Cloud Console go to "
                "APIs & Services > Credentials > Create credentials > "
                "OAuth client ID, choose Desktop app, and download the JSON here."
            )
        print("No valid token found — opening browser for Google sign-in...")
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
        creds = flow.run_local_server(port=OAUTH_PORT)
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
        print(f"Token saved to {TOKEN_FILE} — future runs reuse it.")

    return creds

def get_spreadsheet():
    gc = gspread.authorize(get_credentials())
    try:
        return gc.open(GOOGLE_SHEET_NAME)
    except gspread.SpreadsheetNotFound:
        raise gspread.SpreadsheetNotFound(
            f"No spreadsheet named '{GOOGLE_SHEET_NAME}' is visible to this Google "
            "account. Create a sheet with that exact name in your Drive, or set "
            "GOOGLE_SHEET_NAME in .env to an existing one."
        ) from None


def get_sheet():
    return get_spreadsheet().sheet1


def get_sheet_url() -> str:
    return get_spreadsheet().url


def export_csv(filename: str = "job_applications.csv") -> str:
    data = get_spreadsheet().export(format=ExportFormat.CSV)
    with open(filename, "wb") as f:
        f.write(data)
    return filename


def export_xlsx(filename: str = "job_applications.xlsx") -> str:
    data = get_spreadsheet().export(format=ExportFormat.EXCEL)
    with open(filename, "wb") as f:
        f.write(data)
    return filename


def _header_row(sheet) -> list:
    return [c.strip() for c in sheet.row_values(1)]


def _column_index(sheet, name: str, default: int = None) -> int:
    headers = _header_row(sheet)
    if name in headers:
        return headers.index(name) + 1
    if default is not None:
        return default
    raise KeyError(f"Column '{name}' not found in the sheet's header row")


def setup_headers(sheet=None):
    sheet = sheet or get_sheet()
    if _header_row(sheet) == HEADERS:
        return False
    if sheet.row_values(1):
        print("  Header row did not match — rewriting row 1 in place (no data shifted).")
    sheet.update([HEADERS], "A1")
    print("  Headers set in row 1.")
    return True


def log_jobs(jobs: list[Job]):
    if not jobs:
        print("  No jobs to log.")
        return

    sheet = get_sheet()  # one single connection for all jobs
    setup_headers(sheet)

    # get all existing IDs in one call
    existing_ids = set(sheet.col_values(1)[1:])  # skip header row
    rows_to_add = []
    for job in jobs:
        if job.id in existing_ids:
            print(f"  Skipping duplicate: {job.title} at {job.company}")
            continue
        existing_ids.add(job.id)  # guards against dupes within this batch too
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

    if rows_to_add:
        sheet.append_rows(rows_to_add)  # one batch write instead of N writes
        print(f"  Wrote {len(rows_to_add)} rows in one batch")
    else:
        print("  No new jobs to log")


def log_job(job: Job):
    log_jobs([job])


def clear_sheet():
    sheet = get_sheet()
    sheet.clear()
    setup_headers(sheet)
    print("Sheet cleared and headers reset.")


def update_job_status(job_id: str, new_status: str):
    sheet = get_sheet()
    cell = sheet.find(job_id)
    if not cell:
        print(f"Job ID {job_id} not found in sheet")
        return
    status_col = _column_index(sheet, "Status", default=HEADERS.index("Status") + 1)
    sheet.update_cell(cell.row, status_col, new_status)
    print(f"Updated {job_id} to '{new_status}'")