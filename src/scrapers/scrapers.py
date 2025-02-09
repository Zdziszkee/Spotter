import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup, Tag
import re
from models.offer import ScrapedOffer
from typing import Pattern, Dict, List, Tuple

LOCATION_PATTERNS: List[Pattern] = [
    re.compile(r'Lokalizacja:\s*(?:ul\.|ulicy)?\s*([^,\.]+)', re.IGNORECASE),
    re.compile(r'(?:located at|przy)\s+(?:ul\.|ulicy)?\s*([^,\.]+)', re.IGNORECASE),
    re.compile(r'(?:ul\.|ulicy)\s*([^,\.]+)', re.IGNORECASE),
    re.compile(r'(?:adres|address):\s*([^,\.]+)', re.IGNORECASE),
    re.compile(r'(?:położony|położona) (?:przy|na)\s+(?:ul\.|ulicy)?\s*([^,\.]+)', re.IGNORECASE),
    re.compile(r'(?:w Krakowie)?\s+(?:przy)?\s+(?:ul\.|ulicy)?\s*\.?\s*([^,\.]+)', re.IGNORECASE),
    re.compile(r'(?:obok przystanku|od)\s+([^,\.]+)', re.IGNORECASE),
    re.compile(r'(?:od|obok)\s+(?:Ronda|Rondo)\s+([^,\.]+)', re.IGNORECASE),
    re.compile(r'komunikacja miejska \(przystanek ([^,\.\)]+)\)', re.IGNORECASE)
]

# Comprehensive dictionary of Kraków districts with variants
KRAKOW_DISTRICTS: Dict[str, List[str]] = {
    # Dzielnica I Stare Miasto
    'Stare Miasto': ['Stare Miasto', 'Старе Място', 'Old Town', 'Downtown'],

    # Dzielnica II Grzegórzki
    'Grzegórzki': ['Grzegórzki', 'Grzegorzki', 'Dąbie', 'Dabie', 'Osiedle Oficerskie'],

    # Dzielnica III Prądnik Czerwony
    'Prądnik Czerwony': ['Prądnik Czerwony', 'Pradnik Czerwony', 'Olsza', 'Rakowice', 'Ugorek', 'Wieczystą'],

    # Dzielnica IV Prądnik Biały
    'Prądnik Biały': ['Prądnik Biały', 'Pradnik Bialy', 'Azory', 'Bronowice Wielkie', 'Górka Narodowa', 'Gorka Narodowa'],

    # Dzielnica V Krowodrza
    'Krowodrza': ['Krowodrza', 'Krowoderska', 'Łobzów', 'Lobzow', 'Młynówka Królewska'],

    # Dzielnica VI Bronowice
    'Bronowice': ['Bronowice', 'Bronowice Małe', 'Bronowice Male', 'Mydlniki'],

    # Dzielnica VII Zwierzyniec
    'Zwierzyniec': ['Zwierzyniec', 'Wola Justowska', 'Półwsie Zwierzynieckie', 'Przegorzały', 'Bielany'],

    # Dzielnica VIII Dębniki
    'Dębniki': ['Dębniki', 'Debniki', 'Zakrzówek', 'Tyniec', 'Kostrze', 'Bodzów', 'Kobierzyn', 'Ruczaj'],

    # Dzielnica IX Łagiewniki-Borek Fałęcki
    'Łagiewniki': ['Łagiewniki', 'Lagiewniki', 'Borek Fałęcki', 'Borek Falecki'],

    # Dzielnica X Swoszowice
    'Swoszowice': ['Swoszowice', 'Wróblowice', 'Wroblowice', 'Rajsko', 'Opatkowice'],

    # Dzielnica XI Podgórze Duchackie
    'Podgórze Duchackie': ['Podgórze Duchackie', 'Podgorze Duchackie', 'Kurdwanów', 'Kurdwanow', 'Piaski Wielkie', 'Wola Duchacka'],

    # Dzielnica XII Bieżanów-Prokocim
    'Bieżanów-Prokocim': ['Bieżanów', 'Biezanow', 'Prokocim', 'Rżąka', 'Rzaka'],

    # Dzielnica XIII Podgórze
    'Podgórze': ['Podgórze', 'Podgorze', 'Płaszów', 'Plaszow', 'Zabłocie', 'Zablocie', 'Bonarka'],

    # Dzielnica XIV Czyżyny
    'Czyżyny': ['Czyżyny', 'Czyzyny', 'Łęg', 'Leg', 'Centralna', 'Rondo Czyżyńskie', 'Czyzynskie'],

    # Dzielnica XV Mistrzejowice
    'Mistrzejowice': ['Mistrzejowice', 'Batowice', 'Osiedle Złotego Wieku', 'Osiedle Tysiaclecia'],

    # Dzielnica XVI Bieńczyce
    'Bieńczyce': ['Bieńczyce', 'Bienczyce', 'Osiedle Przy Arce', 'Osiedle Jagiellońskie'],

    # Dzielnica XVII Wzgórza Krzesławickie
    'Wzgórza Krzesławickie': ['Wzgórza Krzesławickie', 'Wzgorza Krzeslawickie', 'Grębałów', 'Grebalow', 'Kantorowice'],

    # Dzielnica XVIII Nowa Huta
    'Nowa Huta': ['Nowa Huta', 'Mogiła', 'Mogila', 'Pleszów', 'Pleszow', 'Branice'],
}

# Cleanup patterns
CLEANUP_PATTERNS: List[Pattern] = [
    re.compile(r'^(ul\.|ulicy)\s*', re.IGNORECASE),  # Remove ul./ulicy prefix
    re.compile(r'\s+', re.UNICODE),  # Normalize whitespace
]

def extract_location_info(description: str) -> Tuple[str, str]:
    """
    Extract location and street information from description.

    Args:
        description (str): The description text to parse

    Returns:
        Tuple[str, str]: (district, street)
    """
    # Normalize description
    description = ' '.join(description.split())

    # Find street
    street = None
    for pattern in LOCATION_PATTERNS:
        match = pattern.search(description)
        if match:
            street = match.group(1).strip()
            break

    # Find district
    district = None
    for main_district, variants in KRAKOW_DISTRICTS.items():
        if any(variant.lower() in description.lower() for variant in variants):
            district = main_district
            break

    # Clean up street name if found
    if street:
        for pattern in CLEANUP_PATTERNS:
            street = pattern.sub(' ', street)
        street = street.strip()

    return (district or "Unknown", street or "Unknown")

class Scraper(ABC):
    def __init__(self, url: str):
        self.url = url

    @abstractmethod
    async def scrape(self) -> list[ScrapedOffer]:
        """Scrape the offer from the given URL provided during object construction.

        Returns:
            FlatOffer: An offer object containing the scraped data.
        """
        pass

class OLXScraper(Scraper):
    async def scrape(self) -> list[ScrapedOffer]:
        offers = []
        try:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(self.url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')

                            # Find all offer links
                            offer_links = soup.find_all('a', attrs={'class': 'css-qo0cxu'})

                            # Create tasks for all offers
                            tasks = []
                            for link in offer_links:
                                if isinstance(link, Tag):
                                    href = link.get('href')
                                    if href and isinstance(href, str):
                                        # Properly format the URL
                                        if href.startswith('http'):
                                            offer_url = str(href)
                                        else:
                                            offer_url = f"https://www.olx.pl{href}"

                                        # Get title from h4
                                        title_elem = link.find('h4', attrs={'class': 'css-1sq4ur2'})
                                        title = title_elem.text.strip() if title_elem else ""

                                        # Extract price and size from title using regex
                                        price_match = re.search(r'(\d+)\s*PLN', title)
                                        size_match = re.search(r'(\d+)\s*m2', title)

                                        price = float(price_match.group(1)) if price_match else 0.0
                                        size = float(size_match.group(1)) if size_match else 0.0

                                        tasks.append(self.fetch_offer_details(session, offer_url, title, price, size))

                            # Run all tasks concurrently
                            offer_results = await asyncio.gather(*tasks, return_exceptions=True)

                            # Filter out exceptions and add successful results
                            offers.extend([offer for offer in offer_results if isinstance(offer, ScrapedOffer)])

                        else:
                            print(f"Failed to fetch main page. Status code: {response.status}")
                except aiohttp.ClientError as e:
                    print(f"Error accessing main page: {e}")
        except Exception as e:
            print(f"Unexpected error in OLX scraper: {e}")

        return offers

    async def fetch_offer_details(self, session, offer_url, title, price, size) -> ScrapedOffer:
        try:
            async with session.get(str(offer_url)) as offer_response:
                if offer_response.status == 200:
                    offer_html = await offer_response.text()
                    offer_soup = BeautifulSoup(offer_html, 'html.parser')

                    # Get title from h4
                    title_elem = offer_soup.find('h4', attrs={'class': 'css-yde3oc'})
                    if title_elem:
                        title = title_elem.text.strip()

                    # Extract more details
                    desc_elem = offer_soup.find('div', attrs={'class': 'css-1o924a9'})
                    description = desc_elem.text.strip() if desc_elem else ""

                    # Get price from h3
                    price_elem = offer_soup.find('h3', attrs={'class': 'css-fqcbii'})
                    if price_elem:
                        price_text = price_elem.text.strip()
                            # Extract numeric value from "2 900 zł" format
                        price = float(price_text.replace(' zł', '').replace(' ', ''))

                    # Get size from p
                    # Extract area
                    area = size  # Default to size from listing preview
                    area_match = re.search(r'Powierzchnia:\s*(\d+(?:\.\d+)?)\s*m²', offer_html)
                    if area_match:
                        area = float(area_match.group(1))

                    # Extract date
                    date_elem = offer_soup.find('span', attrs={'data-cy': 'ad-posted-at'})
                    listed_date = datetime.now()
                    if date_elem:
                        try:
                            date_text = date_elem.text.strip()
                            listed_date = datetime.strptime(date_text, '%d lutego %Y')
                        except ValueError:
                            pass

                    # Extract images
                    images: list[str] = list()
                    img_elem = offer_soup.find('img', attrs={'class': 'css-1bmvjcs'})
                    if img_elem and isinstance(img_elem, Tag):
                        src = img_elem.get('src')
                        if isinstance(src, str):
                            images.append(src)

                    # Extract location using location_info
                    district, street = extract_location_info(description)
                    location = f"{street}, {district}"

                    return ScrapedOffer(
                        title,
                        price,
                        area,
                        location,
                        listed_date,
                        description,
                        str(offer_url),
                        "olx",
                        images
                    )
                else:
                    return ScrapedOffer(
                        title,
                        price,
                        size,
                        "Unknown",
                        datetime.now(),
                        "",
                        str(offer_url),
                        "olx",
                        []
                    )
        except Exception as e:
            print(f"Error processing individual offer {offer_url}: {e}")
            return ScrapedOffer(
                title,
                price,
                size,
                "Unknown",
                datetime.now(),
                "",
                str(offer_url),
                "olx",
                []
            )


class AllegroScraper(Scraper):
    async def scrape(self) -> list[ScrapedOffer]:
        return [
            ScrapedOffer(
                "Demo Product",
                0.0,
                0.0,
                "Unknown",
                datetime.now(),
                "This is a dummy offer created for demonstration purposes.",
                self.url,
                "allegro",
                []
            )
        ]


class FacebookScraper(Scraper):
    async def scrape(self) -> list[ScrapedOffer]:
        return [
            ScrapedOffer(
                "Demo Product",
                0.0,
                0.0,
                "Unknown",
                datetime.now(),
                "This is a dummy offer created for demonstration purposes.",
                self.url,
                "facebook",
                []
            )
        ]


class OtodomScraper(Scraper):
    async def scrape(self) -> list[ScrapedOffer]:
        return [
            ScrapedOffer(
                "Demo Product",
                0.0,
                0.0,
                "Unknown",
                datetime.now(),
                "This is a dummy offer created for demonstration purposes.",
                self.url,
                "otodom",
                []
            )
        ]


class Scrapers:
    def __init__(self):
        self.scrapers = []

    def add_scraper(self, scraper: Scraper):
        self.scrapers.append(scraper)

    async def scrape_all(self) -> list[ScrapedOffer]:
        all_offers = []
        try:
            tasks = [scraper.scrape() for scraper in self.scrapers]
            results = await asyncio.gather(*tasks)
            for offers in results:
                all_offers.extend(offers)
        except Exception as e:
            print(f"Error in scrape_all: {e}")
        return all_offers
