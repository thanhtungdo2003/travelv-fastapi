from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, Enum as SQLAEnum
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import Optional
from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from enum import Enum

class BlogStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"

class BlogTags(str, Enum):
    FUN = "FUN"
    FACT = "FACT"
    SHARE = "SHARE"
    RECRUITMENT = "RECRUITMENT"
    NOTIFICATION = "NOTIFICATION"

class Blogs(Base):
    __tablename__ = "blogs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    imageURL = Column(String)
    tag = Column(SQLAEnum(BlogTags, name="blog_tags"), nullable=False, default=BlogTags.SHARE)
    title = Column(String)
    content = Column(String)
    status = Column(SQLAEnum(BlogStatus, name="blog_status"), nullable=False, default=BlogStatus.DRAFT)
    created_at = Column(DateTime, server_default=func.now())
    user = relationship("Users", back_populates="blogs")

class BlogCreate(BaseModel):
    title: Optional[str]
    tag: Optional[str]
    imageURL: Optional[str]
    content: Optional[str]
