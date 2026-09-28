import time
import random
from datetime import datetime
from playwright.sync_api import sync_playwright

from app.config import HEADLESS
from app.core.scraper.base_scraper import BaseScraper
from app.core.tracker.models import Job


class NaukriScraper(BaseScraper):

    def _build_url(self) -> str:
        keyword = "-".join(self.keywords[0].lower().split())
        location = self.location.lower()
        return f"https://www.naukri.com/{keyword}-jobs-in-{location}"

    def scrape(self, max_jobs: int = 15, headless: bool | None = None, position: str | None = None, on_event=None) -> list[Job]:
        jobs = []
        url = self._build_url()
        show = HEADLESS if headless is None else headless
        args = []
        if not show and position == "left":
            args = ["--window-position=0,0", "--window-size=960,1040"]
        elif not show and position == "right":
            args = ["--window-position=960,0", "--window-size=960,1040"]

        def emit(msg, job=None):
            print(msg, flush=True)
            if on_event:
                try:
                    on_event("naukri", msg, job)
                except Exception:
                    pass

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=show, channel="chrome", args=args, slow_mo=250 if not show else 0)
            page = browser.new_page()

            # Set user agent to avoid detection
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0.0.0 Safari/537.36"
            })

            emit(f"Naukri: opening {url}")
            response = page.goto(url, timeout=60000)
            page.wait_for_timeout(3000)

            # Naukri sits behind Akamai, which answers 403 "Access Denied" to
            # headless sessions before any HTML is served. Detect that explicitly,
            # otherwise a blocked run is indistinguishable from "no jobs today".
            status = response.status if response else None
            title = (page.title() or "").lower()
            if status == 403 or "access denied" in title or "forbidden" in title:
                print(
                    "Naukri: BLOCKED (HTTP %s, title=%r). Their CDN rejects this "
                    "client before HTML loads - returning 0 jobs. LinkedIn results "
                    "are unaffected." % (status, page.title())
                )
                browser.close()
                return []

            # Dismiss any popups
            try:
                close = page.query_selector("button.close-btn")
                if close and close.is_visible():
                    close.click()
                    page.wait_for_timeout(500)
            except Exception:
                pass

            cards = page.query_selector_all(".srp-jobtuple-wrapper")
            emit(f"Naukri: found {len(cards)} job cards")
            if not cards:
                print(
                    "Naukri: 0 cards despite a %s response - the CSS selectors "
                    "(.srp-jobtuple-wrapper) are likely stale and need updating."
                    % status
                )

            for card in cards[:max_jobs]:
                try:
                    title_el   = card.query_selector(".title")
                    company_el = card.query_selector(".comp-name")
                    location_el = card.query_selector(".locWdth")
                    link_el    = card.query_selector("a.title")

                    if not (title_el and company_el and link_el):
                        continue

                    title    = title_el.inner_text().strip()
                    company  = company_el.inner_text().strip()
                    location = location_el.inner_text().strip() if location_el else self.location
                    link     = link_el.get_attribute("href")

                    if not link:
                        continue

                    job = Job(
                        title=title,
                        company=company,
                        location=location,
                        url=link,
                        description="",
                        source="naukri",
                        scraped_at=datetime.now().isoformat(),
                    )
                    jobs.append(job)
                    emit(f"Naukri: {title} @ {company}", job)
                    time.sleep(random.uniform(0.3, 0.8))

                except Exception as e:
                    emit(f"Naukri: skipped card ({e})")
                    continue

            # Fetch descriptions
            for job in jobs:
                job.description = self._get_description(page, job.url)
                emit(f"Naukri: description ({len(job.description)} chars) for {job.title}", job)
                time.sleep(random.uniform(1, 2))

            browser.close()
            emit(f"Naukri: done, {len(jobs)} jobs")

        return self._dedupe(jobs)

    def _get_description(self, page, url: str) -> str:
        try:
            page.goto(url, timeout=30000)
            page.wait_for_timeout(2000)

            desc_el = page.query_selector(".styles_JDC__dang-inner-html__h0K4t")
            if not desc_el:
                desc_el = page.query_selector(".job-desc")
            if not desc_el:
                desc_el = page.query_selector("#job-desc")
            if desc_el:
                return desc_el.inner_text().strip()
            return ""
        except Exception as e:
            print(f"Naukri: Could not fetch description — {e}")
            return ""