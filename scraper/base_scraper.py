from tracker.models import Job

class BaseScraper:
    def __init__(self, keywords: list[str], location: str):
        self.keywords = keywords
        self.location = location

    def scrape(self) -> list[Job]:
        raise NotImplementedError("Subclasses must implement scrape()")

    def _dedupe(self, jobs: list[Job]) -> list[Job]:
        seen = set()
        unique = []
        for j in jobs:
            if j.id not in seen:
                seen.add(j.id)
                unique.append(j)
        return unique