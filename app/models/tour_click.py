from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid


class TourClicks(Base):
    __tablename__ = "tour_clicks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tour_id = Column(UUID(as_uuid=True), ForeignKey("tours.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    referrer = Column(String(500), nullable=True)
    clicked_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    session_id = Column(String(100), nullable=True)
    tour = relationship("Tours", backref="clicks")
    user = relationship("Users", backref="tour_clicks")

class TourClickCreate(BaseModel):
    tour_id: str
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    referrer: Optional[str] = None
    session_id: Optional[str] = None

class TourClickResponse(BaseModel):
    id: str
    tour_id: str
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    clicked_at: datetime
    
    class Config:
        from_attributes = True
        orm_mode = True