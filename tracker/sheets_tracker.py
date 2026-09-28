import gspread
from google.oauth2.service_account import Credentials
from config import GOOGLE_SHEET_NAME
from tracker.models import Job

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

HEADERS = [
    "ID", "Title", "Company", "Location", "URL",
    "Source", "Match Score", "Recommendation",
    "Matched Skills", "Missing Skills", "Status", "Scraped At"
]

def get_sheet():
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    gc = gspread.authorize(creds)
    return gc.open(GOOGLE_SHEET_NAME).sheet1


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