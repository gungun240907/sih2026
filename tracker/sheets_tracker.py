import os
import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
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
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

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
            creds.to_json(f)
        print(f"Token saved to {TOKEN_FILE} — future runs reuse it.")

    return creds

def get_sheet():
    gc = gspread.authorize(get_credentials())
    try:
        return gc.open(GOOGLE_SHEET_NAME).sheet1
    except gspread.SpreadsheetNotFound:
        raise gspread.SpreadsheetNotFound(
            f"No spreadsheet named '{GOOGLE_SHEET_NAME}' is visible to this Google "
            "account. Create a sheet with that exact name in your Drive, or set "
            "GOOGLE_SHEET_NAME in .env to an existing one."
        )


def setup_headers():
    sheet = get_sheet()
    first_row = sheet.row_values(1)
    if first_row != HEADERS:
        sheet.insert_row(HEADERS, 1)
        print("Headers added to sheet.")

def get_existing_ids() -> set:
    sheet = get_sheet()
    ids = sheet.col_values(1)[1:]  # skip header
    return set(ids)

def log_jobs(jobs: list[Job]):
    setup_headers()
    sheet = get_sheet()  # one single connection for all jobs
    
    # get all existing IDs in one call
    existing_ids = set(sheet.col_values(1)[1:])
    
    rows_to_add = []
    for job in jobs:
        if job.id in existing_ids:
            print(f"  Skipping duplicate: {job.title} at {job.company}")
            continue
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
    setup_headers()
    print("Sheet cleared and headers reset.")

def update_job_status(job_id: str, new_status: str):
    sheet = get_sheet()
    cell = sheet.find(job_id)
    if cell:
        status_col = HEADERS.index("Status") + 1
        sheet.update_cell(cell.row, status_col, new_status)
        print(f"Updated {job_id} to '{new_status}'")
    else:
        print(f"Job ID {job_id} not found in sheet")