from sqlalchemy import Column, Integer, String, DateTime, func, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from enum import Enum

class DestinationEnum(str, Enum):
    DELETED = 'DELETED'
    HIDEN = 'HIDEN'
    DEFAULT = 'DEFAULT'

class Destinations(Base):
    __tablename__ = "destinations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, unique=True, nullable=False)
    lat = Column(Float)
    lng = Column(Float)
    description = Column(String)
    thumbnailURL = Column(String)
    status = Column(SQLEnum(DestinationEnum, name="destination_status"), nullable=False, default=DestinationEnum.DEFAULT)
    views = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    tours = relationship("Tours", back_populates="destination")

class DestinationCreation(BaseModel):
    title: str
    description: str
    thumbnailURL: str
    lat: float
    lng: float


class DestinationUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    thumbnailURL: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    views: Optional[int] = None