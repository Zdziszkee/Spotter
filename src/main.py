#!/usr/bin/env python

import asyncio
import os
import pickle
from email.message import EmailMessage
import base64
import logging

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

from src.database.database import db
from src.repository.offers_repository import OffersRepository
from src.scrapers.olx_scraper import OLXScraper
from src.scrapers.scrapers import Scrapers

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to see all logs
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler()  # This sends output to terminal
    ]
)

# The scopes required for Gmail send API.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
# Path to your credentials file for an installed application.
CREDENTIALS_FILE = os.path.join('google-credentials.json')
# Token file to store the user's access and refresh tokens.
TOKEN_FILE = 'token.pickle'


def get_credentials():
    """Obtains valid user credentials from storage or runs an OAuth flow."""
    creds = None
    # Check if token file exists.
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials are available, start the installed flow.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(request=None)
            except Exception as e:
                logging.error("Could not refresh credentials: %s", e)
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for future runs.
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    return creds


def load_streetnames(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file.readlines()]


def gmail_send_message(content):
    """Create and send an email message with the given content.
    Prints the returned message id.
    Returns: Message object, including message id.
    """
    # Get credentials using our helper.
    creds = get_credentials()

    try:
        service = build("gmail", "v1", credentials=creds)
        message = EmailMessage()
        message.set_content(content)
        message["To"] = "mieszkania091@gmail.com"
        message["From"] = "mieszkania091@gmail.com"
        message["Subject"] = "New Offers Found"

        # Encode message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {"raw": encoded_message}

        # pylint: disable=E1101
        send_message = (
            service.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        )
        print(f'Message Id: {send_message["id"]}')
    except HttpError as error:
        print(f"An error occurred: {error}")
        send_message = None

    return send_message


async def main():
    print("Starting server loop. Press Ctrl+C to exit.")
    db.create_all()

    # Load street names from a file.
    streetnames = load_streetnames('street_names_krakow')

    try:
        while True:
            print("Server is running...")
            with db.session() as session:
                scrapers_instance = Scrapers()
                olx_url = ("https://www.olx.pl/nieruchomosci/stancje-pokoje/krakow/?search%5Border%5D=created_at:desc&search%5Bfilter_float_price:to%5D=1500")
                scrapers_instance.add_scraper(OLXScraper(olx_url, streetnames))
                #scrapers_instance.add_scraper(FacebookScraper("https://www.facebook.com/groups/",streetnames))
                offers = await scrapers_instance.scrape_all()

                offers_repository = OffersRepository(session)
                new_offers = 0
                new_offer_details = []
                for offer in offers:
                    existing_offer = offers_repository.get_offer_by_url(str(offer.url))
                    if not existing_offer:
                        offers_repository.create_offer(offer)
                        new_offers += 1
                        new_offer_details.append(f"Offer URL: {offer.url}")

                print(f"Scraped {len(offers)} offers, {new_offers} new.")
                if new_offers > 0:
                    email_content = "New offers found:\n" + "\n".join(new_offer_details)
                    gmail_send_message(email_content)

            await asyncio.sleep(5)  # Wait 60 seconds before next iteration

    except KeyboardInterrupt:
        print("Server loop interrupted. Shutting down.")
    except Exception as e:
        print(f"An error occurred: {e}")
        raise
    finally:
        print("Cleanup completed.")

if __name__ == "__main__":
    asyncio.run(main())
