import sys

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, 'reconfigure'):
        _s.reconfigure(encoding='utf-8', errors='replace')

from scraper.naukri_scraper import NaukriScraper

scraper = NaukriScraper(keywords=["AI Engineer"], location="Bengaluru")
jobs = scraper.scrape(max_jobs=3)

for j in jobs:
    print(f"{j.title} | {j.company} | {j.source}")
    print(f"  Description: {j.description[:100]!r}")
    print()

print(f"Total: {len(jobs)}")