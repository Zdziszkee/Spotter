from typing import Optional, cast

from sqlalchemy.orm import Session

from models.offer import Offer


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
        offer = self.session.query(Offer).filter(Offer.url == url).first()
        return offer

    def get_offer(self, offer_id: int) -> Optional[Offer]:
        """
        Retrieves a single offer by its ID.

        Args:
            offer_id (int): The unique identifier for the offer.

        Returns:
            Optional[Offer]: The retrieved offer object or None if not found.
        """
        offer = self.session.query(Offer).filter(Offer.id == offer_id).first()
        return offer

    def update_offer(self, offer: Offer) -> bool:
        """
        Updates an existing offer record.

        Args:
            offer (Offer): The offer object with updated data. Its 'id' must exist in the database.

        Returns:
            bool: True if at least one row was updated, else False.
        """
        existing_offer = self.session.query(Offer).filter(Offer.id == offer.id).first()
        if not existing_offer:
            return False

        existing_offer.title = offer.title
        existing_offer.price = offer.price
        existing_offer.size = offer.size
        existing_offer.rooms = offer.rooms
        existing_offer.floor = offer.floor
        existing_offer.location = offer.location
        existing_offer.listed_date = offer.listed_date
        existing_offer.description = offer.description
        existing_offer.url = offer.url
        existing_offer.website = offer.website
        existing_offer.images = offer.images

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
        offer = self.session.query(Offer).filter(Offer.id == offer_id).first()
        if offer is None:
            return False

        self.session.delete(offer)
        self.session.commit()
        return True
