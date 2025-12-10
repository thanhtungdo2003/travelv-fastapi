from sqlalchemy import Column, Integer, String, DateTime, func, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship, deferred
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid

from enum import Enum

class UserRoleEnum(str, Enum):
    ADMIN = 'ADMIN'
    MOD = 'MOD'
    TM = 'TM'
    DM = 'DM'
    SM = 'SM'
    DEFAULT = 'DEFAULT'

class UserStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    BANNED = "BANNED"
class GenderEnum(str, Enum):
    MALE = "MALE"
    FEMALE = "MALE"
    OTHER = "OTHER"
    
class Users(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, index=False)
    role = Column(SQLEnum(UserRoleEnum, name="role-type"), nullable=False, default=UserRoleEnum.DEFAULT, index=True)
    password = deferred(Column(String, nullable=False))
    created_at = Column(DateTime, server_default=func.now())

    user_info = relationship("UserInfos", back_populates="user", uselist=False)
    orders = relationship("Orders", back_populates="user")
    blogs = relationship("Blogs", back_populates="user")
    bookings = relationship("Bookings", back_populates="user", uselist=False)
    hotels = relationship("Hotels", back_populates="user")


class UserInfos(Base):
    __tablename__ = "user_infos"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    fullname = Column(String(100), nullable=False)
    phone = Column(String(15), unique=True, nullable=False)
    provice = Column(String(50), nullable=True)
    ward = Column(String(50), nullable=True)
    address = Column(String(255), nullable=True)
    birthday = Column(DateTime, nullable=True)
    gender = Column(SQLEnum(GenderEnum, name="gender-type"), nullable=True)
    nationality = Column(String(50), nullable=True)
    id_card_number = Column(String(20), unique=True, nullable=True)
    status = Column(SQLEnum(UserStatusEnum, name="user-status"), nullable=False, default=UserStatusEnum.ACTIVE)
    created_at = Column(DateTime, server_default=func.now())
    update_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    user = relationship("Users", back_populates="user_info")


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

class UserUpdateByAdmin(BaseModel):
    role: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None