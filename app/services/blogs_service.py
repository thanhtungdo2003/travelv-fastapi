from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base, engine, SessionLocal
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import UUID
import uuid
from fastapi import Depends, HTTPException, status
from datetime import datetime, timedelta
from app.models import blogs
from app.schemas import get_schema
from passlib.context import CryptContext
from app.utils import auth
from sqlalchemy.exc import IntegrityError
import string
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create(user_id:str, title:str, imageURL:str, content:str, tag:str, db: AsyncSession):
    """
    """
    try:
        new_blog = blogs.Blogs(user_id=user_id, title=title, imageURL=imageURL, tag=tag, content=content)
        db.add(new_blog)
        await db.commit()
        await db.refresh(new_blog)
        return new_blog
    except Exception as ex:
        await db.rollback()
        return {"error": f"{str(ex)}"}
    
async def get(get_schem: get_schema.GetSchema, db: AsyncSession):
    """
    Lấy dữ liệu blog:
    - Nếu có id -> trả về blog theo id
    - Nếu có page & row -> trả về dữ liệu phân trang
    - Nếu không truyền gì -> trả về toàn bộ dữ liệu
    """
    try:
        if get_schem.id:
            dt = await db.execute(
                select(blogs.Blogs).where(blogs.Blogs.id == get_schem.id)
            )
            exist_blog = dt.scalars().first()
            if not exist_blog:
                raise HTTPException(status_code=404, detail="Blog not found!")
            return exist_blog

        if get_schem.page is not None and get_schem.row is not None:
            offset_value = (get_schem.page - 1) * get_schem.row
            dt = await db.execute(
                select(blogs.Blogs)
                .offset(offset_value)
                .limit(get_schem.row)
            )
            paged_blogs = dt.scalars().all()
            return paged_blogs

        dt = await db.execute(select(blogs.Blogs))
        all_blog = dt.scalars().all()
        return all_blog

    except HTTPException:
        raise
    except Exception as ex:
        await db.rollback()
        return {"error": str(ex)}