from sqlalchemy import Column, Integer, String, DateTime, func, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from enum import Enum

 
class VehiclesEnum(str, Enum):
    PLANE = 'Plane'
    CAR = 'Car'
class TourTagsEnum(str, Enum):
    SAVEMONEY = 'SAVE MONNEY'


class Tours(Base):
    __tablename__ = "tours"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    destination_id = Column(UUID(as_uuid=True), ForeignKey("destinations.id"))
    title = Column(String, unique=True, nullable=False)
    vehicle = Column(SQLEnum(VehiclesEnum, name="vehicles"), nullable=False, default=VehiclesEnum.CAR)
    tag = Column(SQLEnum(TourTagsEnum, name="tour-tags"), nullable=False, default=TourTagsEnum.SAVEMONEY)
    price = Column(Integer, nullable=False)
    slots = Column(Integer, default=1)
    first_location = Column(String)
    start_location = Column(String)
    estimated_time = Column(String)
    description = Column(String)
    thumbnailURL = Column(String)
    imageURLs = Column(String)
    views = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    destination = relationship("Destinations", back_populates="tours")
    bookings = relationship("Bookings", back_populates="tour")


class TourCreation(BaseModel):
    title: str
    destination_id: str
    vehicle: str
    tag: str
    price: int
    slots: int
    first_location: str
    start_location: str
    estimated_time: str
    description: str
    thumbnailURL: str
    imageURLs: Optional[str] = None


class TourUpdate(BaseModel):
    title: Optional[str] = None
    destination_id: Optional[str] = None
    vehicle: Optional[str] = None
    tag: Optional[str] = None
    price: Optional[int] = None
    slots: Optional[int] = None
    first_location: Optional[str] = None
    start_location: Optional[str] = None
    estimated_time: Optional[str] = None
    description: Optional[str] = None
    thumbnailURL: Optional[str] = None
    imageURLs: Optional[str] = None
