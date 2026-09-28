from dataclasses import dataclass, field
import hashlib

@dataclass
class Job:
    title: str
    company: str
    location: str
    url: str
    description: str
    source: str
    scraped_at: str
    match_score: float = 0.0
    status: str = "new"
    match_meta: dict = field(default_factory=dict)
    id: str = field(init=False)

    def __post_init__(self):
        self.id = hashlib.md5(self.url.encode()).hexdigest()[:10]