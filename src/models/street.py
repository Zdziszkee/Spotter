from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from src.database.base_model import BaseModel

class Street(BaseModel):
    __tablename__ = 'streets'

    street_name = Column(String(255), nullable=False, index=True)
    postal_code = Column(String(10), nullable=False, index=True)
    city = Column(String(255), nullable=False)
    district = Column(String(255))
    state = Column(String(255))
    geometry = Column(Text)

    # Use string reference instead of direct class reference
    offers = relationship("Offer", back_populates="street", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Street(id={self.id}, name='{self.street_name}', city='{self.city}')>"
