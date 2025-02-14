import asyncio
from abc import ABC, abstractmethod
from src.models.offer import Offer

class Scraper(ABC):
    def __init__(self, url: str):
        self.url = url

    @abstractmethod
    async def scrape(self) -> list[Offer]:
        """Scrape the offer from the given URL provided during object construction.

        Returns:
        list[Offer]: A list of offer objects containing the scraped data.
        """
        pass

class Scrapers:
    def __init__(self):
        self.scrapers = []

    def add_scraper(self, scraper: Scraper):
        self.scrapers.append(scraper)

    async def scrape_all(self) -> list[Offer]:
        all_offers = []
        try:
            tasks = [scraper.scrape() for scraper in self.scrapers]
            results = await asyncio.gather(*tasks)
            for offers in results:
                all_offers.extend(offers)
        except Exception as e:
            print(f"Error in scrape_all: {e}")
        return all_offers
