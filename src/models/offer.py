from sqlalchemy import Column, String, Float, Integer, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from src.database.base_model import BaseModel

class Offer(BaseModel):
    __tablename__ = 'offers'

    title = Column(String(255), nullable=False)
    price = Column(Float, nullable=False, index=True)
    size = Column(Float)
    rooms = Column(Integer)
    floor = Column(Integer)
    location = Column(String(255))
    listed_date = Column(TIMESTAMP, index=True)
    description = Column(Text)
    street_id = Column(Integer, ForeignKey('streets.id'), index=True)
    url = Column(String(255), unique=True)
    website = Column(String(255))
    images = Column(Text)

    # Use string reference instead of direct class reference
    street = relationship("Street", back_populates="offers")

    def __repr__(self) -> str:
        return f"<Offer(id={self.id}, title='{self.title}', price={self.price})>"
