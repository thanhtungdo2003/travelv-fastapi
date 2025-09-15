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
        
        if updateItem.title:
            item.title = updateItem.title
        if updateItem.description:
            item.description = updateItem.description
        if updateItem.thumbnailURL:
            item.thumbnailURL = updateItem.thumbnailURL
        if updateItem.lat:
            item.lat = updateItem.lat
        if updateItem.lng:
            item.lng = updateItem.lng
        if updateItem.views:
            item.views = updateItem.views

        await db.commit()
        await db.refresh(item)
        return item
    except IntegrityError:
        await db.rollback()
        raise
    

    


async def get_destinations(filters: get_schema.GetSchema, db: AsyncSession):
    stmt = select(destinations.Destinations)

    if filters.id:
        stmt = stmt.where(destinations.Destinations.id == filters.id)

    if filters.searchKeyword:
        keyword = f"%{filters.searchKeyword}%"
        stmt = stmt.where(
            (destinations.Destinations.title.ilike(keyword)) |
            (destinations.Destinations.description.ilike(keyword))
        )

    # Phân trang
    page = filters.page if filters.page and filters.page > 0 else 1
    row = filters.row if filters.row and filters.row > 0 else 10
    offset = (page - 1) * row

    total = (await db.execute(select(func.count()).select_from(destinations.Destinations))).scalar()

    result = await db.execute(stmt.offset(offset).limit(row))
    data = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "row": row,
        "data": data
    }