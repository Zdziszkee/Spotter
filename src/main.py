import asyncio
from src.database.database import db
from repository.offers_repository import OffersRepository

async def main():
    print("Starting server loop. Press Ctrl+C to exit.")
    from scrapers.scrapers import OLXScraper, Scrapers

    scrapers_instance = Scrapers()
    scrapers_instance.add_scraper(OLXScraper("https://www.olx.pl/nieruchomosci/mieszkania/wynajem/krakow/?search%5Border%5D=created_at:desc&search%5Bfilter_float_price:to%5D=3500&search%5Bfilter_enum_rooms%5D%5B0%5D=three&search%5Bfilter_enum_rooms%5D%5B1%5D=two"))

    try:
        while True:
            print("Server is running...")
            offers = await scrapers_instance.scrape_all()

            # Use the session context manager
            with db.session() as session:
                offers_repository = OffersRepository(session)
                new_offers = 0
                for offer in offers:
                    existing_offer = offers_repository.get_offer_by_url(str(offer.url))
                    if not existing_offer:
                        offers_repository.create_offer(offer)
                        new_offers += 1

            print(f"Scraped {len(offers)} offers, {new_offers} new.")
            await asyncio.sleep(5)
    except KeyboardInterrupt:
        print("Server loop interrupted. Shutting down.")
    except Exception as e:
        print(f"An error occurred: {e}")
        raise
    finally:
        print("Cleanup completed.")


if __name__ == "__main__":
    asyncio.run(main())
