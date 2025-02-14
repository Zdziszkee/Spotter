import asyncio
from src.database.database import db
from src.repository.offers_repository import OffersRepository
from src.scrapers.olx_scraper import OLXScraper
from src.scrapers.scrapers import Scrapers
import logging

# Add this at the start of your main script
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to see all logs
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler()  # This sends output to terminal
    ]
)
async def main():
    print("Starting server loop. Press Ctrl+C to exit.")

    db.create_all()

    try:
        while True:
            print("Server is running...")
            with db.session() as session:
                scrapers_instance = Scrapers()

                olx_url = (
                "https://www.olx.pl/nieruchomosci/mieszkania/wynajem/krakow/?search%5Border%5D=created_at:desc&search%5Bfilter_float_price:to%5D=3500&search%5Bfilter_enum_rooms%5D%5B0%5D=three&search%5Bfilter_enum_rooms%5D%5B1%5D=two"
                )
                scrapers_instance.add_scraper(OLXScraper(olx_url))
                offers = await scrapers_instance.scrape_all()

                offers_repository = OffersRepository(session)
                new_offers = 0
                for offer in offers:
                    existing_offer = offers_repository.get_offer_by_url(str(offer.url))
                    if not existing_offer:
                        offers_repository.create_offer(offer)
                        new_offers += 1

                print(f"Scraped {len(offers)} offers, {new_offers} new.")

            await asyncio.sleep(60)  # Wait 60 seconds before next iteration

    except KeyboardInterrupt:
        print("Server loop interrupted. Shutting down.")
    except Exception as e:
        print(f"An error occurred: {e}")
        raise
    finally:
        print("Cleanup completed.")

if __name__ == "__main__":
    asyncio.run(main())
