from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base, engine, SessionLocal
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import UUID
import uuid
from fastapi import Depends, HTTPException, status
from datetime import datetime, timedelta
from app.models import hotelroom, user
from app.schemas import get_schema
from passlib.context import CryptContext
from app.utils import auth
from sqlalchemy.exc import IntegrityError
import string
import secrets
from sqlalchemy.orm import selectinload
import math
from app.services import schedules_service

async def check_owner(owner_id:str, hotel_id:str, db: AsyncSession):
    hotel = (await db.execute(select(hotelroom.Hotels).where(id == hotel_id))).scalar_one_or_none()
    if str(hotel.user_id) != str(owner_id):
        raise HTTPException(status_code=404, detail="Not permission")
    else:
        return True

async def increase_view(id: str, db: AsyncSession):
    existed_items = await db.execute(select(hotelroom.Hotels).where(hotelroom.Hotels.id == id))
    item = existed_items.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Hotel not found")
    item.views = item.views+1
    await db.commit()
    await db.refresh(item)

async def create(owner_id:str, data: hotelroom.HotelCreate,
        db: AsyncSession
):
    """
    """
    try:
        new_item = hotelroom.Hotels(**data.model_dump())
        new_item.user_id = owner_id
        db.add(new_item)
        await db.commit()
        await db.refresh(new_item)
        return new_item
    except IntegrityError:
        await db.rollback()
        raise

async def update(owner_id:str, id:str, updateItem: hotelroom.HotelUpdate,
        db: AsyncSession
):
    """
    """
    try:
        existed_items = await db.execute(select(hotelroom.Hotels).where(hotelroom.Hotels.id == id))
        item = existed_items.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Hotel not found")
        await check_owner(owner_id=owner_id, hotel_id=item.id, db=db)

        update_data = updateItem.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(item, key, value)

        await db.commit()
        await db.refresh(item)
        
        return item
    except IntegrityError:
        await db.rollback()
        raise
    


async def get_hotelroom(filters: get_schema.GetHotelSchema, db: AsyncSession):
    stmt = select(hotelroom.Hotels)
    if filters.status:
        stmt = stmt.where(hotelroom.Hotels.status == filters.status)
    if filters.id:
        stmt = stmt.where(hotelroom.Hotels.id == filters.id)
        await increase_view(filters.id, db)

    if filters.searchKeyword:
        keyword = f"%{filters.searchKeyword}%"
        stmt = stmt.where(
            (hotelroom.Hotels.title.ilike(keyword)) |
            (hotelroom.Hotels.description.ilike(keyword)) |
            (hotelroom.Hotels.address.ilike(keyword))
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
        "max_page": max_page,
        "row": row,
        "data": data
    }

async def get_hotel_by_user_id(user_id: str, filters: get_schema.GetHotelSchema, db: AsyncSession):
    base_stmt = (
        select(hotelroom.Hotels)
        .join(user.Users, user.Users.id == hotelroom.Hotels.user_id)
        .where(hotelroom.Hotels.user_id == user_id)
    )
    if filters.status:
        base_stmt = base_stmt.where(hotelroom.Hotels.status == filters.status)
    if filters.id:
        base_stmt = base_stmt.where(hotelroom.Hotels.id == filters.id)
        await increase_view(filters.id, db)

    if filters.searchKeyword:
        keyword = f"%{filters.searchKeyword}%"
        base_stmt = base_stmt.where(
            (hotelroom.Hotels.title.ilike(keyword)) |
            (hotelroom.Hotels.description.ilike(keyword))
        )

    page = filters.page if filters.page and filters.page > 0 else 1
    row = min(filters.row if filters.row and filters.row > 0 else 10, 100)
    offset = (page - 1) * row
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await db.execute(count_stmt)).scalar()
    stmt = base_stmt.options(selectinload(hotelroom.Hotels.rooms))
    result = await db.execute(stmt.offset(offset).limit(row))
    data = result.unique().scalars().all()

    max_page = math.ceil(total / row) if row > 0 else 1

    return {
        "total": total,
        "page": page,
        "max_page": max_page,
        "row": row,
        "data": data
    }