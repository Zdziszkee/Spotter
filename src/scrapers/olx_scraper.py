from datetime import datetime
from src.scrapers.scrapers import Scraper
from src.models.offer import Offer
import aiohttp
from bs4 import BeautifulSoup, Tag
import logging
import re
import asyncio
import random
from typing import Optional

logger = logging.getLogger(__name__)

class OLXScraper(Scraper):
    def __init__(self, url: str):
        super().__init__(url)
        self.street_prefixes = ['ul.', 'ulica', 'na ulicy', 'przy ulicy', 'al.', 'aleja']
        self.max_concurrent_tasks = 12
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.max_retries = 3
        self.retry_delay = 1
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]

    async def _fetch_with_retry(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        for attempt in range(self.max_retries):
            try:
                async with session.get(
                    url,
                    timeout=self.timeout,
                    headers={'User-Agent': random.choice(self.user_agents)}
                ) as response:
                    if response.status == 200:
                        return await response.text()
                    logger.warning(f"Attempt {attempt + 1} failed with status {response.status} for {url}")
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed with error: {str(e)} for {url}")

            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))

        return None

    def _parse_price(self, price_tag: Optional[Tag]) -> float:
        if not price_tag:
            return 0.0
        try:
            raw_price = price_tag.text.strip()
            raw_price = raw_price.replace(' zł', '').replace(' ', '').replace(',', '.')
            return float(raw_price)
        except ValueError:
            logger.warning(f"Could not parse price from: {price_tag.text if price_tag else 'None'}")
            return 0.0

    def _parse_polish_date(self, date_str: str) -> datetime:
        months = {
            "stycznia": 1, "lutego": 2, "marca": 3, "kwietnia": 4,
            "maja": 5, "czerwca": 6, "lipca": 7, "sierpnia": 8,
            "września": 9, "października": 10, "listopada": 11, "grudnia": 12,
        }
        try:
            if date_str.startswith('Dzisiaj'):
                time_parts = date_str.split('o')[1].strip().split(':')
                today = datetime.now()
                return today.replace(hour=int(time_parts[0]), minute=int(time_parts[1]), second=0, microsecond=0)

            parts = date_str.strip().split()
            if len(parts) == 3:
                day = int(parts[0])
                month = months.get(parts[1].lower(), 0)
                year = int(parts[2])
                if month:
                    return datetime(year, month, day)
        except Exception as e:
            logger.error(f"Error parsing date '{date_str}': {str(e)}")
        return datetime.now()

    async def _process_single_offer(self, session: aiohttp.ClientSession, link: Tag) -> Optional[Offer]:
        full_url = "unknown"  # Initialize with default value
        try:
            if not (h4 := link.find('h4', attrs={'class': 'css-1sq4ur2'})):
                return None

            url = link.get('href', '')
            title = h4.text.strip()
            logger.debug(f"Processing offer: {title}")

            if url and "otodom.pl" in url:
                logger.debug(f"Skipping otodom offer: {url}")
                return None

            full_url = f"https://www.olx.pl{url}"
            if "www.olx.plhttps:443" in full_url:
                logger.warning(f"Skipping invalid URL: {full_url}")
                return None

            logger.debug(f"Fetching offer details from: {full_url}")
            offer_html = await self._fetch_with_retry(session, full_url)
            if not offer_html:
                return None

            offer_soup = BeautifulSoup(offer_html, 'html.parser')

            # Extract offer details
            desc_tag = offer_soup.find('div', class_='css-1o924a9')
            description = desc_tag.text.strip() if desc_tag else ""

            price_tag = offer_soup.find('h3', class_='css-fqcbii')
            if isinstance(price_tag, Tag):
                price = self._parse_price(price_tag)
            else:
                price = 0.0

            # Initialize offer parameters
            rooms = size = rent = floor = 0
            building_type = ""
            has_elevator = False
            parking = ""

            # Process offer details
            for info_tag in offer_soup.find_all('p', class_='css-1wgiva2'):
                info_text = info_tag.text.strip()
                try:
                    if "Liczba pokoi:" in info_text:
                        rooms = int(info_text.split("Liczba pokoi:")[1].strip().split()[0])
                    elif "Powierzchnia:" in info_text:
                        size = float(info_text.split("Powierzchnia:")[1].strip().split()[0].replace(',', '.'))
                    elif "Czynsz (dodatkowo):" in info_text:
                        rent = float(info_text.split("Czynsz (dodatkowo):")[1].strip().split()[0].replace(',', '.'))
                    elif "Poziom:" in info_text:
                        floor_text = info_text.split("Poziom:")[1].strip().split()[0]
                        floor = 0 if floor_text.lower() == "parter" else int(floor_text)
                    elif "Rodzaj zabudowy:" in info_text:
                        building_type = info_text.split("Rodzaj zabudowy:")[1].strip()
                    elif "Winda:" in info_text:
                        has_elevator = info_text.split("Winda:")[1].strip().lower() == "tak"
                    elif "Parking:" in info_text:
                        parking = info_text.split("Parking:")[1].strip()
                except Exception as e:
                    logger.warning(f"Error parsing info: {str(e)}")

            # Extract listing date
            listed_date = datetime.now()
            date_container = offer_soup.find('span', class_='css-1eaxltp')
            if isinstance(date_container, Tag):
                date_span = date_container.find('span', attrs={'data-cy': 'ad-posted-at'})
                if isinstance(date_span, Tag):
                    listed_date = self._parse_polish_date(date_span.text.strip())
                    # Extract street information
                    full_text = f"{title} {description}"
                    street = ""
                    for prefix in self.street_prefixes:
                        if match := re.search(f"{prefix}\\s+([A-Za-zżźćńółęąśŻŹĆĄŚĘŁÓŃ]+)", full_text, re.IGNORECASE):
                            street = match.group(1)
                            break

                    return Offer(
                        title=title,
                        price=price,
                        size=size,
                        rooms=rooms,
                        floor=floor,
                        street=street,
                        listed_date=listed_date,
                        description=description,
                        district="",
                        url=str(full_url),
                        source="olx",
                        images=[],
                        rent=rent,
                        building_type=building_type,
                        has_elevator=has_elevator,
                        parking=parking,
                        province=""
                    )

        except Exception as e:
            logger.error(f"Error processing offer {full_url}: {str(e)}")
            return None

    async def scrape(self) -> list[Offer]:
        logger.info(f"Starting OLX scraping from URL: {self.url}")
        offers = []

        conn = aiohttp.TCPConnector(
            ssl=False,
            limit=self.max_concurrent_tasks,
            force_close=True
        )

        session_timeout = aiohttp.ClientTimeout(total=60)

        async with aiohttp.ClientSession(
            connector=conn,
            timeout=session_timeout,
            headers={'User-Agent': random.choice(self.user_agents)}
        ) as session:
            try:
                logger.info("Fetching main listing page...")
                main_page_html = await self._fetch_with_retry(session, self.url)
                if not main_page_html:
                    logger.error("Failed to fetch main page")
                    return offers

                soup = BeautifulSoup(main_page_html, 'html.parser')
                links = soup.find_all('a', attrs={'class': 'css-qo0cxu'})
                logger.info(f"Found {len(links)} offer links on the page")

                semaphore = asyncio.Semaphore(self.max_concurrent_tasks)

                async def process_with_semaphore(link):
                    try:
                        async with semaphore:
                            return await self._process_single_offer(session, link)
                    except Exception as e:
                        logger.error(f"Error in process_with_semaphore: {str(e)}")
                        return None

                tasks = [
                    process_with_semaphore(link)
                    for link in links
                    if isinstance(link, Tag)
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)
                offers.extend([
                    offer for offer in results
                    if offer is not None and not isinstance(offer, Exception)
                ])

            except Exception as e:
                logger.error(f"Error during scraping: {str(e)}")

        logger.info(f"Scraping completed. Found {len(offers)} offers")
        return offers
