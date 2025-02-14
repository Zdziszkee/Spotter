from typing import Optional, cast
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.models.offer import Offer  # Changed from 'models.offer'


class OffersRepository:
    def __init__(self, session: Session) -> None:
        """
        Initialize the repository with an active SQLAlchemy session.
        """
        self.session = session

    def create_offer(self, offer: Offer) -> Optional[int]:
        """
        Inserts a new offer record into the database.

        Args:
            offer (Offer): The offer to be inserted.

        Returns:
            Optional[int]: The ID of the newly inserted offer or None if insertion failed.
        """
        self.session.add(offer)
        self.session.commit()
        return cast(Optional[int], offer.id)

    def get_offer_by_url(self, url: str) -> Optional[Offer]:
        """
        Retrieves a single offer by its URL.

        Args:
            url (str): The URL of the offer.

        Returns:
            Optional[Offer]: The retrieved offer object or None if not found.
        """
        result = self.session.execute(
            select(Offer).filter(Offer.url == url)
        )
        return result.scalar_one_or_none()

    def get_offer(self, offer_id: int) -> Optional[Offer]:
        """
        Retrieves a single offer by its ID.

        Args:
            offer_id (int): The unique identifier for the offer.

        Returns:
            Optional[Offer]: The retrieved offer object or None if not found.
        """
        result = self.session.execute(
            select(Offer).filter(Offer.id == offer_id)
        )
        return result.scalar_one_or_none()

    def update_offer(self, offer: Offer) -> bool:
        """
        Updates an existing offer record.

        Args:
            offer (Offer): The offer object with updated data. Its 'id' must exist in the database.

        Returns:
            bool: True if at least one row was updated, else False.
        """
        result = self.session.execute(
            select(Offer).filter(Offer.id == offer.id)
        )
        existing_offer = result.scalar_one_or_none()
        if not existing_offer:
            return False

        existing_offer.title = offer.title
        existing_offer.price = offer.price
        existing_offer.size = offer.size
        existing_offer.rooms = offer.rooms
        existing_offer.floor = offer.floor
        existing_offer.street = offer.street
        existing_offer.city = offer.city
        existing_offer.province = offer.province
        existing_offer.listed_date = offer.listed_date
        existing_offer.description = offer.description
        existing_offer.district = offer.district
        existing_offer.url = offer.url
        existing_offer.images = offer.images
        existing_offer.source = offer.source
        existing_offer.rent = offer.rent
        existing_offer.building_type = offer.building_type
        existing_offer.has_elevator = offer.has_elevator
        existing_offer.parking = offer.parking

        self.session.commit()
        return True

    def delete_offer(self, offer_id: int) -> bool:
        """
        Deletes an offer record from the database.

        Args:
            offer_id (int): The unique identifier for the offer to delete.

        Returns:
            bool: True if at least one row was deleted, else False.
        """
        result = self.session.execute(
            select(Offer).filter(Offer.id == offer_id)
        )
        offer = result.scalar_one_or_none()
        if offer is None:
            return False

        self.session.delete(offer)
        self.session.commit()
        return True
