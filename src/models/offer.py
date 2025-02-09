from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class ScrapedOffer:
    title: str
    price: float
    size: float
    location: str
    listed_date: datetime
    description: str
    url: str
    website: str         # Name or identifier of the website
    images: List[str]


@dataclass
class Offer(ScrapedOffer):
    id: int             # Automatically incremented by database
