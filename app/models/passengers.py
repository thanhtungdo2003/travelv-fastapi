from sqlalchemy import Column, Integer, String, DateTime, func, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from enum import Enum

class PassengerAgeEnum(str, Enum):
    ADULT = 'Adult'
    CHILDREN = 'Children'
    BABY = 'Baby'

class Passengers(Base):
    __tablename__ = "passengers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fullname = Column(String, nullable=False)
    age_type = Column(SQLEnum(PassengerAgeEnum, name="passenger-age-type"), nullable=False, default=PassengerAgeEnum.ADULT)
    bookings_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"))
    birth_day = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    booking = relationship("Bookings", back_populates="passengers")

