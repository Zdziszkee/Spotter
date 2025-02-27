import logging
import re
import requests
from datetime import datetime
from src.scrapers.scrapers import Scraper
from src.models.offer import Offer
from src.util.street_extractor import extract_street

# Initialize the logger at the module level
logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)

class FacebookScraper(Scraper):
    def __init__(self, url: str, streetnames: list[str], access_token: str):
        super().__init__(url)
        self.streetnames = streetnames
        self.access_token = access_token

    def _extract_price(self, text: str) -> float:
        match = re.search(r'Cena:\s*([\d\s]+) PLN', text)
        if match:
            return float(match.group(1).replace(' ', ''))
        return 0.0

    def _extract_size(self, text: str) -> float:
        match = re.search(r'Powierzchnia:\s*([\d,]+) m2', text)
        if match:
            return float(match.group(1).replace(',', '.'))
        return 0.0

    def _extract_floor(self, text: str) -> int:
        match = re.search(r'Piętro:\s*(\d+)', text)
        if match:
            return int(match.group(1))
        return 0

    def _extract_rooms(self, text: str) -> int:
        match = re.search(r'Pomieszczenia:\s*(\d+)', text)
        if match:
            return int(match.group(1))
        return 0

    async def scrape(self) -> list[Offer]:
        offers = []
        try:
            url = "https://graph.facebook.com/v12.0/373495383005249/feed"
            params = {
                'access_token': self.access_token,
                'fields': 'message,created_time,permalink_url,attachments{media}'
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            for post in data.get('data', []):
                logger.debug(f"Processing post: {post}")
                text = post.get('message', '')
                if not text:
                    logger.warning("Post text is missing")
                    continue

                title = text.split('\n')[0]
                price = self._extract_price(text)
                size = self._extract_size(text)
                floor = self._extract_floor(text)
                rooms = self._extract_rooms(text)
                street = extract_street(text, self.streetnames) or ""
                listed_date = datetime.strptime(post.get('created_time'), '%Y-%m-%dT%H:%M:%S%z')

                images = []
                if 'attachments' in post:
                    for attachment in post['attachments']['data']:
                        if 'media' in attachment:
                            images.append(attachment['media']['image']['src'])

                offer = Offer(
                    title=title,
                    price=price,
                    size=size,
                    rooms=rooms,
                    floor=floor,
                    street=street,
                    city="Kraków",
                    listed_date=listed_date,
                    description=text,
                    district="",
                    subdistrict="",
                    url=post.get('permalink_url', ''),
                    source="facebook",
                    images=images,
                    rent=0.0,
                    building_type="",
                    has_elevator=False,
                    parking="",
                    province="Małopolska"
                )
                offers.append(offer)
        except Exception as e:
            logger.error(f"Error in scrape: {str(e)}", exc_info=True)
        return offers
