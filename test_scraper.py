from scraper.linkedin_scraper import LinkedInScraper

scraper = LinkedInScraper(keywords=["AI Engineer"], location="Bengaluru")
jobs = scraper.scrape(max_jobs=5)

for j in jobs:
    print(f"{j.title} | {j.company} | {j.location} | {j.url}")
    print(f"  Description preview: {j.description[:150]!r}")
    print()

print(f"Total jobs scraped: {len(jobs)}")