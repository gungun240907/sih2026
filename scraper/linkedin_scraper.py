import time
import random
from datetime import datetime
from urllib.parse import quote
from playwright.sync_api import sync_playwright
from scraper.base_scraper import BaseScraper
from config import HEADLESS
from tracker.models import Job

class LinkedInScraper(BaseScraper):
    BASE_URL = "https://www.linkedin.com/jobs/search/"

    def scrape(self, max_jobs: int = 15, headless: bool | None = None, position: str | None = None, on_event=None) -> list[Job]:
        jobs = []
        keyword_query = "%20".join(self.keywords)
        url = f"{self.BASE_URL}?keywords={keyword_query}&location={quote(self.location)}"
        show = HEADLESS if headless is None else headless
        args = []
        if not show and position == "left":
            args = ["--window-position=0,0", "--window-size=960,1040"]
        elif not show and position == "right":
            args = ["--window-position=960,0", "--window-size=960,1040"]

        def emit(msg, job=None):
            print(msg)
            if on_event:
                try:
                    on_event("linkedin", msg, job)
                except Exception:
                    pass

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=show, args=args, slow_mo=250 if not show else 0)
            try:
                page = browser.new_page()
                emit(f"LinkedIn: opening {url}")
                page.goto(url, timeout=60000)
                page.wait_for_timeout(3000)

                cards = page.query_selector_all(".base-card")
                emit(f"LinkedIn: found {len(cards)} job cards")

                for card in cards[:max_jobs]:
                    try:
                        title_el = card.query_selector(".base-search-card__title")
                        company_el = card.query_selector(".base-search-card__subtitle")
                        location_el = card.query_selector(".job-search-card__location")
                        link_el = card.query_selector("a.base-card__full-link")

                        if not (title_el and company_el and link_el):
                            continue

                        title = title_el.inner_text().strip()
                        company = company_el.inner_text().strip()
                        location = location_el.inner_text().strip() if location_el else ""
                        link = link_el.get_attribute("href").split("?")[0]

                        job = Job(
                            title=title,
                            company=company,
                            location=location,
                            url=link,
                            description="",
                            source="linkedin",
                            scraped_at=datetime.now().isoformat(),
                        )
                        jobs.append(job)
                        emit(f"LinkedIn: {title} @ {company}", job)
                        time.sleep(random.uniform(0.5, 1.5))
                    except Exception as e:
                        emit(f"LinkedIn: skipped a card ({e})")
                        continue
                for job in jobs:
                    job.description = self.get_description(page, job.url)
                    emit(f"LinkedIn: description ({len(job.description)} chars) for {job.title}", job)
                    time.sleep(random.uniform(1, 2))
                emit(f"LinkedIn: done, {len(jobs)} jobs")
            finally:
                # always close — otherwise the headed Chrome window stays on the desktop
                try:
                    browser.close()
                except Exception:
                    pass

        return self._dedupe(jobs)

    def get_description(self, page, url: str) -> str:
        try:
            page.goto(url, timeout=30000)
            page.wait_for_timeout(2000)
            try:
                close_btn = page.query_selector("button[aria-label='Dismiss']")
                if close_btn:
                    close_btn.click(timeout=3000)
                    page.wait_for_timeout(800)
            except Exception:
                pass
            desc_el = page.query_selector(".show-more-less-html__markup")
            if not desc_el:
                desc_el = page.query_selector(".description__text")
            if desc_el:
                return desc_el.inner_text().strip()
            return ""
        except Exception as e:
            print(f"Could not fetch description for {url}: {e}")
            return ""