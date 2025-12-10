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
import math
from app.services import schedules_service
async def increase_view(id: str, db: AsyncSession):
    existed_items = await db.execute(select(tours.Tours).where(tours.Tours.id == id))
    item = existed_items.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Tour not found")
    item.views = item.views+1
    await db.commit()
    await db.refresh(item)


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
        await schedules_service.auto_generate_schedules(new_item.id, datetime.now(), db=db)
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
    stmt = select(tours.Tours).options(
        selectinload(tours.Tours.destination),
        selectinload(tours.Tours.schedules)
    ).where(tours.Tours.status == tours.TourStatusEnum.DEFAULT)

    if filters.id:
        stmt = stmt.where(tours.Tours.id == filters.id)
        await schedules_service.ensure_future_schedules(tour_id=filters.id, db=db)
        await increase_view(filters.id, db)

    if filters.searchKeyword:
        keyword = f"%{filters.searchKeyword}%"
        stmt = stmt.where(
            (tours.Tours.title.ilike(keyword)) |
            (tours.Tours.description.ilike(keyword))
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

async def get_disable_tours(filters: get_schema.GetSchema, db: AsyncSession):
    stmt = select(tours.Tours).options(
        selectinload(tours.Tours.destination),
        selectinload(tours.Tours.schedules)
    ).where(tours.Tours.status == tours.TourStatusEnum.DELETED)
    if filters.id:
        stmt = stmt.where(tours.Tours.id == filters.id)

    if filters.searchKeyword:
        keyword = f"%{filters.searchKeyword}%"
        stmt = stmt.where(
            (tours.Tours.title.ilike(keyword)) |
            (tours.Tours.description.ilike(keyword))
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


async def get_tours_by_destination_id(destination_id: int, filters: get_schema.ToursGetSchema, db: AsyncSession):
    base_stmt = select(tours.Tours).where(tours.Tours.destination_id == destination_id).where(
        tours.Tours.price.between(filters.priceFrom, filters.priceTo)
    ).where(tours.Tours.status == tours.TourStatusEnum.DEFAULT).options(
        selectinload(tours.Tours.schedules)
    )

    if filters.id:
        base_stmt = base_stmt.where(tours.Tours.id == filters.id)
        await increase_view(filters.id, db)

    if filters.searchKeyword:
        keyword = f"%{filters.searchKeyword}%"
        base_stmt = base_stmt.where(
            (tours.Tours.title.ilike(keyword)) |
            (tours.Tours.description.ilike(keyword))
        )

    page = filters.page if filters.page and filters.page > 0 else 1
    row = min(filters.row if filters.row and filters.row > 0 else 10, 100)
    offset = (page - 1) * row
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await db.execute(count_stmt)).scalar()
    stmt = base_stmt.options(selectinload(tours.Tours.destination))
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