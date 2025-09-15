from sqlalchemy import Column, Integer, String, DateTime, func, Enum as SQLEnum, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from enum import Enum

class BookingsStatusEnum(str, Enum):
    PAID = 'Paid'
    UNPAID = 'Unpaid'
    CANCELED = 'Canceled'

class Bookings(Base):
    __tablename__ = "bookings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fullname = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    status = Column(SQLEnum(BookingsStatusEnum, name="bookings-status"), nullable=False, default=BookingsStatusEnum.UNPAID)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    tour_id = Column(UUID(as_uuid=True), ForeignKey("tours.id"))
    province = Column(String, nullable=False)
    ward = Column(String, nullable=False)
    specific_address = Column(String, nullable=False)
    pickup_lat = Column(Float)
    pickup_lng = Column(Float)
    diparture_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    user = relationship("Users", back_populates="bookings")
    tour = relationship("Tours", back_populates="bookings")
    passengers = relationship("Passengers", back_populates="booking", cascade="all, delete-orphan")

class PassengerCreation(BaseModel):
    fullname: str
    age_type: str
    bookings_id: str
    birth_day: datetime

class BookingsCreation(BaseModel):
    fullname: str
    email: str
    phone: str
    user_id: str
    tour_id: str
    province: str
    ward: str
    specific_address: str
    pickup_lat: Optional[float] = None
    pickup_lng: Optional[float] = None
    diparture_at: datetime
    passengers: list[PassengerCreation]


