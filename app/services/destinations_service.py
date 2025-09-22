from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base, engine, SessionLocal
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import UUID
import uuid
from fastapi import Depends, HTTPException, status
from datetime import datetime, timedelta
from app.models import destinations
from app.schemas import get_schema
from passlib.context import CryptContext
from app.utils import auth
from sqlalchemy.exc import IntegrityError
import string
import secrets
import math

async def create(
        title: string,
        description: string,
        thumbnailURL: string,
        lat: int,
        lng: int,
        db: AsyncSession
):
    """
    """
    try:
        new_item = destinations.Destinations(title=title, 
                            description=description, lat=lat, lng=lng,
                            thumbnailURL=thumbnailURL)
        db.add(new_item)
        await db.commit()
        await db.refresh(new_item)
        return new_item
    except IntegrityError:
        await db.rollback()
        raise


async def update(id:str, updateItem: destinations.DestinationUpdate,
        db: AsyncSession
):
    """
    """
    try:
        existed_items = await db.execute(select(destinations.Destinations).where(destinations.Destinations.id == id))
        item = existed_items.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Destination not found")
        
        update_data = updateItem.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(item, key, value)


        await db.commit()
        await db.refresh(item)
        return item
    except IntegrityError:
        await db.rollback()
        raise
    

    


async def get_destinations(filters: get_schema.GetSchema, db: AsyncSession):
    stmt = select(destinations.Destinations).where(destinations.Destinations.status == destinations.DestinationEnum.DEFAULT)

    if filters.id:
        stmt = stmt.where(destinations.Destinations.id == filters.id)

    if filters.searchKeyword:
        keyword = f"%{filters.searchKeyword.strip()}%"
        stmt = stmt.where(
            (destinations.Destinations.title.ilike(keyword)) |
            (destinations.Destinations.description.ilike(keyword))
        )

    page = filters.page if filters.page and filters.page > 0 else 1
    row = min(filters.row if filters.row and filters.row > 0 else 10, 100)
    offset = (page - 1) * row
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar()

    result = await db.execute(stmt.offset(offset).limit(row))
    data = result.scalars().all()
    max_page = math.ceil(total / row) if row > 0 else 1

    return {
        "total": total,
        "page": page,
        "row": row,
        "max_page": max_page,
        "data": data
    }



async def get_disable_destinations(filters: get_schema.GetSchema, db: AsyncSession):
    stmt = select(destinations.Destinations).where(destinations.Destinations.status == destinations.DestinationEnum.DELETED)

    if filters.id:
        stmt = stmt.where(destinations.Destinations.id == filters.id)

    if filters.searchKeyword:
        keyword = f"%{filters.searchKeyword.strip()}%"
        stmt = stmt.where(
            (destinations.Destinations.title.ilike(keyword)) |
            (destinations.Destinations.description.ilike(keyword))
        )

    page = filters.page if filters.page and filters.page > 0 else 1
    row = min(filters.row if filters.row and filters.row > 0 else 10, 100)
    offset = (page - 1) * row
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar()

    result = await db.execute(stmt.offset(offset).limit(row))
    data = result.scalars().all()
    max_page = math.ceil(total / row) if row > 0 else 1

    return {
        "total": total,
        "page": page,
        "row": row,
        "max_page": max_page,
        "data": data
    }