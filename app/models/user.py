from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Users(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, index=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    orders = relationship("Orders", back_populates="user")
    blogs = relationship("Blogs", back_populates="user")
    bookings = relationship("Bookings", back_populates="user")

class UserSignin(BaseModel):
    email: str
    username: str
    password: str
    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
