from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class GetSchema(BaseModel):
    id: Optional[str] = None
    searchKeyword: Optional[str] = None
    page: Optional[int] = None
    row: Optional[int] = None

class GetRoomSchema(BaseModel):
    id: Optional[str] = None
    owner_id: Optional[str] = None
    searchKeyword: Optional[str] = None
    page: Optional[int] = None
    row: Optional[int] = None
    status: Optional[str] = None
    priceFrom: Optional[int] = 0
    priceTo: Optional[int] = 1000000000

class GetTourRoomSchema(BaseModel):
    id: Optional[str] = None
    tour_id: Optional[str] = None
    room_id: Optional[str] = None
    owner_id: Optional[str] = None
    searchKeyword: Optional[str] = None
    page: Optional[int] = None
    row: Optional[int] = None
    status: Optional[str] = None
class GetHotelSchema(BaseModel):
    id: Optional[str] = None
    searchKeyword: Optional[str] = None
    page: Optional[int] = None
    row: Optional[int] = None
    status: Optional[str] = None

class ToursGetSchema(BaseModel):
    id: Optional[str] = None
    searchKeyword: Optional[str] = None
    page: Optional[int] = None
    row: Optional[int] = None
    priceFrom: Optional[int] = 0
    priceTo: Optional[int] = 1000000000