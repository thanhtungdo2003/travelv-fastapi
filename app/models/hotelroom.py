from sqlalchemy import Column, Integer, String, DateTime, func, Enum as SQLEnum, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime, date
from pydantic import BaseModel
from typing import Optional

from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from enum import Enum

class RoomStatusEnum(str, Enum):
    DELETED = 'DELETED'
    CLEANING = 'CLEANING'
    AVAILABLE = 'AVAILABLE'
    OCCUPIED = "OCCUPIED"
    RESERVED = "RESERVED"

class HotelStatusEnum(str, Enum):
    DELETED = 'DELETED'
    MAINTENANCE = 'MAINTENANCE'
    OPEN = "OPEN"
    CLOSE = "CLOSE"

class RoomTypeEnum(str, Enum):
    SINGLE = "SINGLE"
    DOUBLE = "DOUBLE"
    TWIN = "TWIN"
    TRIPLE = "TRIPLE"
    FAMILY = "FAMILY"
    DELUXE = "DELUXE"
    SUITE = "SUITE"
    STANDARD = "STANDARD"
    VIP = "VIP"
    
class Hotels(Base):
    __tablename__ = "hotels"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    title = Column(String, nullable=False)
    status = Column(SQLEnum(HotelStatusEnum, name="hotel_status"), nullable=False, default=HotelStatusEnum.MAINTENANCE)
    rating = Column(Integer, default=0)
    lat = Column(Float)
    lng = Column(Float)
    address = Column(String)
    description = Column(String)
    thumbnailURL = Column(String)
    imageURLs = Column(String)
    views = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    rooms = relationship("HotelRooms", back_populates="hotel")
    user = relationship("Users", back_populates="hotels")


class HotelRooms(Base):
    __tablename__ = "hotel_rooms"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hotel_id = Column(UUID(as_uuid=True), ForeignKey("hotels.id"))
    title = Column(String, nullable=False)
    status = Column(SQLEnum(RoomStatusEnum, name="room_status"), nullable=False, default=RoomStatusEnum.CLEANING)
    type = Column(SQLEnum(RoomTypeEnum, name="room_type"), nullable=False, default=RoomTypeEnum.STANDARD)
    price = Column(Integer, nullable=False)
    lat = Column(Float)
    lng = Column(Float)
    address = Column(String)
    description = Column(String)
    thumbnailURL = Column(String)
    imageURLs = Column(String)
    views = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    tour_rooms = relationship("TourRooms", back_populates="rooms")
    hotel = relationship("Hotels", back_populates="rooms")
    booking_rooms = relationship("BookingRooms", back_populates="room")

class TourRooms(Base):
    __tablename__ = "tour_rooms"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tour_id = Column(UUID(as_uuid=True), ForeignKey("tours.id"))
    room_id = Column(UUID(as_uuid=True), ForeignKey("hotel_rooms.id"))
    created_at = Column(DateTime, server_default=func.now())

    tour = relationship("Tours", back_populates="tour_rooms")
    rooms = relationship("HotelRooms", back_populates="tour_rooms")

class BookingRooms(Base):
    __tablename__ = "booking_rooms"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"))
    room_id = Column(UUID(as_uuid=True), ForeignKey("hotel_rooms.id"))
    check_in = Column(DateTime, nullable=True)
    check_out = Column(DateTime, nullable=True)
    price_per_night = Column(Integer, nullable=True)
    total_room_price = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    room = relationship("HotelRooms", back_populates="booking_rooms")
    booking = relationship("Bookings", back_populates="booking_rooms")

class RoomCreation(BaseModel):
    title: str
    price: int
    type: RoomTypeEnum = RoomTypeEnum.STANDARD
    status: RoomStatusEnum = RoomStatusEnum.CLEANING
    lat: float
    lng: float
    address: str
    description: Optional[str] = None
    thumbnailURL: Optional[str] = None
    imageURLs: Optional[str] = None
    hotel_id: Optional[str] = None

class RoomUpdate(BaseModel):
    title: Optional[str] = None
    price: Optional[int] = None
    type: Optional[RoomTypeEnum] = None
    status: Optional[RoomStatusEnum] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    address: Optional[str] = None
    description: Optional[str] = None
    thumbnailURL: Optional[str] = None
    imageURLs: Optional[str] = None

class BookingRoomCreation(BaseModel):
    booking_id: str
    room_id: str
    check_in: datetime
    check_out: datetime
    price_per_night: int
    total_room_price: Optional[int] = None

    class Config:
        orm_mode = True


class HotelCreate(BaseModel):
    title: str
    rating: int = 0
    status: HotelStatusEnum = HotelStatusEnum.MAINTENANCE
    lat: float
    lng: float
    address: str
    description: Optional[str] = None
    thumbnailURL: Optional[str] = None
    imageURLs: Optional[str] = None


class HotelUpdate(BaseModel):
    title: Optional[str] = None
    rating: Optional[int] = None
    status: Optional[HotelStatusEnum] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    address: Optional[str] = None
    description: Optional[str] = None
    thumbnailURL: Optional[str] = None
    imageURLs: Optional[str] = None