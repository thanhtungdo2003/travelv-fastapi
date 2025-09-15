from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Orders(Base):
    __tablename__ = "orders"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(String)
    amount = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    pack = Column(String)
    user = relationship("Users", back_populates="orders")