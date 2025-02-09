import json
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import Optional

from pypika import Query

from models.offer import Offer, ScrapedOffer
from util.database import offers_table  # <== Import the shared table


class OffersRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        """
        Initialize the repository with an active SQLite connection.
        """
        self.connection = connection
        self.table = offers_table  # use the imported table

    def create_offer(self, offer: ScrapedOffer) -> Optional[int]:
        """
        Inserts a new offer record into the database.

        Args:
            offer (Offer): The offer to be inserted.

        Returns:
            Optional[int]: The ID of the newly inserted offer or None if insertion failed.
        """
        query = (
            Query.into(self.table)
            .columns(
                "title",
                "price",
                "size",
                "location",
                "listed_date",
                "description",
                "url",
                "website",
                "images",
            )
            .insert(
                offer.title,
                offer.price,
                offer.size,
                offer.location,
                offer.listed_date.isoformat(),  # Convert datetime to string.
                offer.description,
                offer.url,
                offer.website,
                json.dumps(offer.images),  # Serialize list to JSON string.
            )
        )
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(str(query))
            self.connection.commit()
            return cursor.lastrowid

    def get_offer_by_url(self, url: str) -> Optional[Offer]:
        """
        Retrieves a single offer by its URL.

        Args:
            url (str): The URL of the offer.

        Returns:
            Optional[Offer]: The retrieved offer object or None if not found.
        """
        query = Query.from_(self.table).select("*").where(self.table.url == url)
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(str(query))
            row = cursor.fetchone()

        if row is None:
            return None

        return Offer(
            id=row[0],
            title=row[1],
            price=row[2],
            size=row[3],
            location=row[4],
            listed_date=datetime.fromisoformat(row[5]),
            description=row[6],
            url=row[7],
            website=row[8],
            images=json.loads(row[9]) if row[9] else [],
        )

    def get_offer(self, offer_id: int) -> Optional[Offer]:
        """
        Retrieves a single offer by its ID.

        Args:
            offer_id (int): The unique identifier for the offer.

        Returns:
            Optional[Offer]: The retrieved offer object or None if not found.
        """
        query = Query.from_(self.table).select("*").where(self.table.id == offer_id)
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(str(query))
            row = cursor.fetchone()

        if row is None:
            return None

        # Expecting the following order of fields:
        # id, title, price, size, location, listed_date, description, url, website, images
        return Offer(
            id=row[0],
            title=row[1],
            price=row[2],
            size=row[3],
            location=row[4],
            listed_date=datetime.fromisoformat(row[5]),
            description=row[6],
            url=row[7],
            website=row[8],
            images=json.loads(row[9]) if row[9] else [],
        )

    def update_offer(self, offer: Offer) -> bool:
        """
        Updates an existing offer record.

        Args:
            offer (Offer): The offer object with updated data. Its 'id' must exist in the database.

        Returns:
            bool: True if at least one row was updated, else False.
        """
        q = (
            Query.update(self.table)
            .set("title", offer.title)
            .set("price", offer.price)
            .set("size", offer.size)
            .set("location", offer.location)
            .set("listed_date", offer.listed_date.isoformat())
            .set("description", offer.description)
            .set("url", offer.url)
            .set("website", offer.website)
            .set("images", json.dumps(offer.images))
            .where(self.table.id == offer.id)
        )

        with closing(self.connection.cursor()) as cursor:
            cursor.execute(str(q))
            self.connection.commit()
            return cursor.rowcount > 0

    def delete_offer(self, offer_id: int) -> bool:
        """
        Deletes an offer record from the database.

        Args:
            offer_id (int): The unique identifier for the offer to delete.

        Returns:
            bool: True if at least one row was deleted, else False.
        """
        q = Query.from_(self.table).delete().where(self.table.id == offer_id)
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(str(q))
            self.connection.commit()
            return cursor.rowcount > 0
