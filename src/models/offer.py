from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean
from sqlalchemy.orm import relationship
from typing import List
from datetime import datetime
import json
from src.database.base_model import BaseModel

class Offer(BaseModel):
    __tablename__ = 'offers'

    title = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    size = Column(Float)
    rooms = Column(Integer)
    floor = Column(Integer)
    street = Column(String(255))
    city = Column(String(255))
    province = Column(String(255))
    listed_date = Column(DateTime)
    description = Column(String)
    district = Column(String(255))
    url = Column(String(255), unique=True)
    images = Column(String)  # Stored as a JSON string
    source = Column(String(50))  # Added source column

    # New fields added based on data from the OLX scraper
    rent = Column(Float, default=0.0)
    building_type = Column(String(100))
    has_elevator = Column(Boolean, default=False)
    parking = Column(String(50))


    def __init__(self, title: str, price: float, size: float, rooms: int, floor: int,
                 street: str, listed_date: datetime, description: str, district: str,
                 url: str, source: str, images: List[str], province: str,
                 rent: float = 0.0, building_type: str = "", has_elevator: bool = False, parking: str = ""):
        super().__init__()
        self.title = title
        self.price = price
        self.size = size
        self.rooms = rooms
        self.floor = floor
        self.street = street
        self.listed_date = listed_date
        self.description = description
        self.district = district
        self.url = url
        self.source = source
        self.images = json.dumps(images) if images else "[]"
        self.province = province
        self.rent = rent
        self.building_type = building_type
        self.has_elevator = has_elevator
        self.parking = parking

    def __repr__(self) -> str:
        return f"<Offer(title='{self.title}', price={self.price}, street='{self.street}', rent={self.rent}, building_type='{self.building_type}', has_elevator={self.has_elevator}, parking='{self.parking}')>"
