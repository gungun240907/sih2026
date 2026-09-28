import resend
import os
from dotenv import load_dotenv
from config import GMAIL_ADDRESS
from tracker.models import Job

load_dotenv()
resend.api_key = os.getenv("RESEND_API_KEY")


def send_daily_digest(jobs: list[Job]):
    if not jobs:
        print("No high-scoring jobs to notify about.")
        return

    subject = f"🤖 Job Agent — {len(jobs)} jobs need your review today"
    body = _build_email_body(jobs)

    try:
        resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": [GMAIL_ADDRESS],
            "subject": subject,
            "html": body,
        })
        print(f"Email sent — {len(jobs)} jobs in digest")
    except Exception as e:
        print(f"Email failed: {e}")


def _build_email_body(jobs: list[Job]) -> str:
    rows = ""
    for job in jobs:
        rec     = job.match_meta.get("recommendation", "").upper()
        score   = f"{job.match_score:.0%}"
        matched = ", ".join(job.match_meta.get("matched_skills", []))
        missing = ", ".join(job.match_meta.get("missing_skills", []))
        color   = "#4caf82" if rec == "APPLY" else "#f0a500"

        rows += f"""
        <tr>
            <td style="padding:12px;border-bottom:1px solid #eee;">
                <strong>{job.title}</strong><br>
                <span style="color:#666;">{job.company} · {job.location}</span>
            </td>
            <td style="padding:12px;border-bottom:1px solid #eee;text-align:center;">
                <span style="color:{color};font-weight:700;font-size:1.2rem;">{score}</span>
            </td>
            <td style="padding:12px;border-bottom:1px solid #eee;text-align:center;">
                <span style="background:{color};color:white;padding:3px 10px;
                      border-radius:12px;font-size:0.8rem;">{rec}</span>
            </td>
            <td style="padding:12px;border-bottom:1px solid #eee;font-size:0.85rem;">
                ✅ {matched}<br>❌ {missing}
            </td>
            <td style="padding:12px;border-bottom:1px solid #eee;">
                <a href="{job.url}" style="background:#7c83ff;color:white;
                   padding:6px 14px;border-radius:6px;text-decoration:none;
                   font-size:0.85rem;">View Job</a>
            </td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial,sans-serif;max-width:900px;margin:0 auto;padding:20px;">
        <div style="background:linear-gradient(135deg,#1e2130,#252840);
                    border-radius:12px;padding:24px;margin-bottom:24px;">
            <h1 style="color:#ffffff;margin:0;">🤖 Job Application Agent</h1>
            <p style="color:#9098b1;margin:8px 0 0;">
                Daily digest — {len(jobs)} jobs scored above your threshold
            </p>
        </div>
        <table style="width:100%;border-collapse:collapse;background:#fff;
                      border-radius:12px;overflow:hidden;
                      box-shadow:0 2px 8px rgba(0,0,0,0.1);">
            <thead>
                <tr style="background:#f8f9fa;">
                    <th style="padding:12px;text-align:left;color:#444;">Job</th>
                    <th style="padding:12px;text-align:center;color:#444;">Score</th>
                    <th style="padding:12px;text-align:center;color:#444;">Decision</th>
                    <th style="padding:12px;text-align:left;color:#444;">Skills</th>
                    <th style="padding:12px;text-align:left;color:#444;">Link</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        <div style="margin-top:24px;padding:16px;background:#f8f9fa;
                    border-radius:8px;text-align:center;">
            <p style="color:#666;font-size:0.85rem;margin:0;">
                Sent by your Job Application Agent ·
                Update application status in your
                <a href="http://localhost:8501" style="color:#7c83ff;">dashboard</a>
            </p>
        </div>
    </body>
    </html>
    """