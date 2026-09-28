# Job Application Agent

An autonomous job search assistant that scrapes listings from LinkedIn and Naukri,
scores them against your resume with an LLM, and tracks everything in Google Sheets.

```
LinkedIn + Naukri            Groq LLM               Google Sheets
(Playwright scraper)  →  (Resume matcher)  →  (Live job tracker)
                                ↓
                         Resend email digest
```

1. **Scraper** — Playwright (Chromium) opens LinkedIn and Naukri, searches for AI/ML
   jobs, and extracts title, company, location, URL, and full job description
2. **Matcher** — sends each job description plus your resume to Groq's
   `llama-3.3-70b-versatile`, which returns a match score (0–1), matched skills,
   missing skills, and a recommendation (`apply` / `maybe` / `skip`)
3. **Filter** — jobs scoring below `MATCH_THRESHOLD` are discarded, and so are jobs
   requiring more than 2 years of experience. Jobs above `AUTO_APPLY_THRESHOLD` are
   flagged as priority
4. **Tracker** — passes surviving jobs to Google Sheets in one batch write, with
   deduplication on job ID
5. **Notifier** — emails a digest of the priority jobs via Resend
6. **Auth** — Google OAuth runs on first use only; the token is cached in `token.json`

## Project Structure

```
sih2026/
├── main.py                    # pipeline orchestrator (CLI entry point)
├── config.py                  # env config + search keywords/thresholds
├── resume.txt                 # your resume, plain text
├── requirements.txt
├── scraper/
│   ├── base_scraper.py        # shared base class + dedupe helper
│   ├── linkedin_scraper.py    # Playwright LinkedIn scraper
│   └── naukri_scraper.py      # Playwright Naukri scraper
├── matcher/
│   └── resume_matcher.py      # Groq LLM scoring + filtering
├── notifier/
│   └── email_notifier.py      # Resend HTML digest
└── tracker/
    ├── models.py              # Job dataclass
    └── sheets_tracker.py      # Google Sheets read/write
```

## Tech Stack

| Layer | Technology |
|---|---|
| Browser automation | Playwright (Chromium) |
| LLM scoring | Groq API — `llama-3.3-70b-versatile` via the OpenAI SDK |
| Job tracking | Google Sheets API (gspread) |
| Email digest | Resend |

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

### 2. Environment variables

Create a `.env` file in the repo root (gitignored):

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b
GMAIL_ADDRESS=you@gmail.com
RESEND_API_KEY=your_resend_api_key
GOOGLE_SHEET_NAME=Job Applications
HEADLESS=true
```

`GROQ_MODEL` must be a model your Groq plan actually has access to — check
`GET https://api.groq.com/openai/v1/models` with your key. `HEADLESS=true`
(secret, no visible browser) is the default; set `HEADLESS=false` to watch the
scraper work in a visible Chromium window.

### 3. Google Sheets

`sheets_tracker.py` authenticates **as your own Google account** via OAuth, so the
target sheet lives in your own Drive.

1. In [Google Cloud Console](https://console.cloud.google.com) for your project, open
   **APIs & Services → Credentials**
2. **Create credentials → OAuth client ID → Desktop app**
3. Download the JSON and save it in the repo root as `oauth_client.json`
4. Create a Google Sheet whose name matches `GOOGLE_SHEET_NAME`
   (default `Job Applications`)

On the first run a browser opens for Google sign-in. The resulting token is cached in
`token.json`, so this happens only once. Both files are gitignored.

If your app is still in the Google **Testing** publishing state, add
`devfeedmail@gmail.com` under **OAuth consent screen → Test users** — otherwise Google
returns `access_denied`. On the consent warning page choose
**Advanced → Go to (unsafe)**.

### 4. Resume

Put your resume in `resume.txt` as plain text.

## Usage

```bash
python main.py
```

## Agent Decision Logic

```
Match score >= 85%  →  LOG with priority flag (apply immediately)
Match score 65–84%  →  LOG to sheet (review manually)
Match score < 65%   →  DISCARD (not a good fit)
Requires > 2 yrs    →  DISCARD regardless of score
```

## Notes

- `main.py` reconfigures stdout/stderr to UTF-8 on startup, so the `→` separators print
  correctly in the default Windows console. If characters still look garbled, run
  `chcp 65001` first.
- The `test_*.py` files are standalone smoke tests for each stage, run individually with
  `python test_scraper.py`, `python test_matcher.py`, etc.
- Naukri's markup is unstable and it rate-limits anonymous scraping, so `naukri_scraper`
  can intermittently return zero jobs. LinkedIn is the more reliable of the two.
