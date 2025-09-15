from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base, engine, SessionLocal
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import UUID
import uuid
from fastapi import Depends, HTTPException, status
from datetime import datetime, timedelta
from app.models import tours
from app.schemas import get_schema
from passlib.context import CryptContext
from app.utils import auth
from sqlalchemy.exc import IntegrityError
import string
import secrets
from sqlalchemy.orm import selectinload

async def create(data: tours.TourCreation,
        db: AsyncSession
):
    """
    """
    try:
        new_item = tours.Tours(**data.model_dump())
        db.add(new_item)
        await db.commit()
        await db.refresh(new_item)
        return new_item
    except IntegrityError:
        await db.rollback()
        raise


async def update(id:str, updateItem: tours.TourUpdate,
        db: AsyncSession
):
    """
    """
    try:
        existed_items = await db.execute(select(tours.Tours).where(tours.Tours.id == id))
        item = existed_items.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Tour not found")
        
        update_data = updateItem.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(item, key, value)

        await db.commit()
        await db.refresh(item)
        return item
    except IntegrityError:
        await db.rollback()
        raise
    

    


async def get_tours(filters: get_schema.GetSchema, db: AsyncSession):
    stmt = select(tours.Tours).options(selectinload(tours.Tours.destination))

    if filters.id:
        stmt = stmt.where(tours.Tours.id == filters.id)

    if filters.searchKeyword:
        keyword = f"%{filters.searchKeyword}%"
        stmt = stmt.where(
            (tours.Tours.title.ilike(keyword)) |
            (tours.Tours.description.ilike(keyword))
        )

    page = max(filters.page or 1, 1)
    row = max(filters.row or 10, 1)
    offset = (page - 1) * row

    total_result = await db.execute(stmt.with_only_columns(func.count()).order_by(None))
    total = total_result.scalar()

    result = await db.execute(stmt.offset(offset).limit(row))
    data = result.scalars().unique().all()

    return {
        "total": total,
        "page": page,
        "row": row,
        "data": data
    }