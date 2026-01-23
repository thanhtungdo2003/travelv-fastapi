from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base, engine, SessionLocal
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import UUID
import uuid
from fastapi import Depends, HTTPException, status
from datetime import datetime, timedelta
from app.models import hotelroom, tours
from app.schemas import get_schema
from passlib.context import CryptContext
from app.utils import auth
from sqlalchemy.exc import IntegrityError
import string
import secrets
from sqlalchemy.orm import selectinload
import math
from app.services import schedules_service

async def check_owner(owner_id:str , hotel_id:str , db: AsyncSession):
    hotel = (await db.execute(select(hotelroom.Hotels).where(hotelroom.Hotels.id == hotel_id))).scalar_one_or_none()
    if str(hotel.user_id) != str(owner_id):
        raise HTTPException(status_code=404, detail="Not permission")
    else:
        return True

async def increase_view(id: str, db: AsyncSession):
    existed_items = await db.execute(select(hotelroom.HotelRooms).where(hotelroom.HotelRooms.id == id))
    item = existed_items.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Room not found")
    item.views = item.views+1
    await db.commit()
    await db.refresh(item)

async def create(owner_id:str ,data: hotelroom.RoomCreation,
        db: AsyncSession
):
    """
    """
    try:
        new_item = hotelroom.HotelRooms(**data.model_dump())
        await check_owner(owner_id=owner_id, hotel_id=new_item.hotel_id, db=db)
        db.add(new_item)
        await db.commit()
        await db.refresh(new_item)
        return new_item
    except IntegrityError:
        await db.rollback()
        raise

async def set_tour_room(owner_id:str, tour_id: str, room_id: str, db: AsyncSession):
    try:
        new_item = hotelroom.TourRooms(tour_id=tour_id, room_id=room_id)
        room = (await db.execute(select(hotelroom.HotelRooms).where(hotelroom.HotelRooms.id == room_id))).scalar_one_or_none()
        await check_owner(owner_id=owner_id, hotel_id=room.hotel_id, db=db)
        db.add(new_item)
        await db.commit()
        await db.refresh(new_item)
        return {
            "status": 200,
            "detail": "Tour room linked successfully",
            "data": {
                "id": str(new_item.id),
                "tour_id": str(new_item.tour_id),
                "room_id": str(new_item.room_id)
            }
        }
    except IntegrityError as e:
        await db.rollback()
        error_msg = str(e.orig).lower()
        if "foreign key" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="Invalid tour_id or room_id (foreign key constraint failed)"
            )
        elif "unique" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="This room is already linked to the tour"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Database integrity error"
            )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
async def delete_tour_room(owner_id:str ,id: str,
        db: AsyncSession
):
    """
    """
    try:
        existed_item = await db.execute(select(hotelroom.TourRooms).where(hotelroom.TourRooms.id == id))
        item = existed_item.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Room not found")
        room = (await db.execute(select(hotelroom.HotelRooms).where(hotelroom.HotelRooms.id == item.room_id))).scalar_one_or_none()
        await check_owner(owner_id=owner_id, hotel_id=room.hotel_id, db=db)
        await db.delete(item)
        await db.commit()
        return {"status": 200, "detail": "Tour room deleted successfully"}
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete: data is referenced by another record. ({str(e)})"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

async def update(owner_id:str, id:str, updateItem: hotelroom.RoomUpdate,
        db: AsyncSession
):
    """
    """
    try:
        existed_items = await db.execute(select(hotelroom.HotelRooms).where(hotelroom.HotelRooms.id == id))
        item = existed_items.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Room not found")
        update_data = updateItem.model_dump(exclude_unset=True)
        await check_owner(owner_id=owner_id, hotel_id=item.hotel_id, db=db)
        for key, value in update_data.items():
            setattr(item, key, value)

        await db.commit()
        await db.refresh(item)
        
        return item
    except IntegrityError:
        await db.rollback()
        raise
    

async def get_tour_room(filters: get_schema.GetTourRoomSchema, db: AsyncSession):
    stmt = select(hotelroom.TourRooms).options(
        selectinload(hotelroom.TourRooms.rooms),
        selectinload(hotelroom.TourRooms.tour),
    )
    if filters.room_id:
        stmt = (stmt.join(hotelroom.HotelRooms, hotelroom.HotelRooms.id == hotelroom.TourRooms.room_id)
        .where(hotelroom.HotelRooms.id == filters.room_id))
    if filters.tour_id:
        stmt = (stmt.join(tours.Tours, tours.Tours.id == hotelroom.TourRooms.tour_id)
        .where(tours.Tours.id == filters.tour_id))
    if filters.owner_id:
        stmt = (stmt.join(hotelroom.Hotels, hotelroom.Hotels.id == hotelroom.HotelRooms.hotel_id)
        .where(hotelroom.Hotels.user_id == filters.owner_id))
    if filters.status:
        stmt = stmt.where(hotelroom.HotelRooms.status == filters.status)
    if filters.id:
        stmt = stmt.where(hotelroom.HotelRooms.id == filters.id)
        await increase_view(filters.id, db)

    if filters.searchKeyword:
        keyword = f"%{filters.searchKeyword}%"
        stmt = stmt.where(
            (hotelroom.HotelRooms.title.ilike(keyword)) |
            (hotelroom.HotelRooms.description.ilike(keyword)) |
            (hotelroom.HotelRooms.address.ilike(keyword))
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

async def get_hotelroom(filters: get_schema.GetRoomSchema, db: AsyncSession):
    stmt = select(hotelroom.HotelRooms)
    if filters.owner_id:
        stmt = (stmt.join(hotelroom.Hotels, hotelroom.Hotels.id == hotelroom.HotelRooms.hotel_id)
        .where(hotelroom.Hotels.user_id == filters.owner_id))
    if filters.status:
        stmt = stmt.where(hotelroom.HotelRooms.status == filters.status)
    if filters.id:
        stmt = stmt.where(hotelroom.HotelRooms.id == filters.id)
        await increase_view(filters.id, db)

    if filters.searchKeyword:
        keyword = f"%{filters.searchKeyword}%"
        stmt = stmt.where(
            (hotelroom.HotelRooms.title.ilike(keyword)) |
            (hotelroom.HotelRooms.description.ilike(keyword)) |
            (hotelroom.HotelRooms.address.ilike(keyword))
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

async def get_hotelroom_by_hotel_id(hotel_id: str, filters: get_schema.GetRoomSchema, db: AsyncSession):
    base_stmt = (
        select(hotelroom.HotelRooms)
        .where(hotelroom.HotelRooms.hotel_id == hotel_id)
        .where(hotelroom.HotelRooms.price.between(filters.priceFrom, filters.priceTo))
    )
    if filters.owner_id:
        base_stmt = (base_stmt.join(hotelroom.Hotels, hotelroom.Hotels.id == hotelroom.HotelRooms.hotel_id)
        .where(hotelroom.Hotels.user_id == filters.owner_id))
    if filters.status:
        base_stmt = base_stmt.where(hotelroom.HotelRooms.status == filters.status)
    if filters.id:
        base_stmt = base_stmt.where(hotelroom.HotelRooms.id == filters.id)
        await increase_view(filters.id, db)

    if filters.searchKeyword:
        keyword = f"%{filters.searchKeyword}%"
        base_stmt = base_stmt.where(
            (hotelroom.HotelRooms.title.ilike(keyword)) |
            (hotelroom.HotelRooms.description.ilike(keyword))
        )

    page = filters.page if filters.page and filters.page > 0 else 1
    row = min(filters.row if filters.row and filters.row > 0 else 10, 100)
    offset = (page - 1) * row
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await db.execute(count_stmt)).scalar()
    stmt = base_stmt.options(selectinload(hotelroom.HotelRooms.hotel))
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


async def get_hotelroom_by_tour_id(tour_id: str, filters: get_schema.GetRoomSchema, db: AsyncSession):
    base_stmt = (
        select(hotelroom.HotelRooms)
        .join(hotelroom.TourRooms, hotelroom.TourRooms.room_id == hotelroom.HotelRooms.id)
        .where(hotelroom.TourRooms.tour_id == tour_id)
        .where(hotelroom.HotelRooms.price.between(filters.priceFrom, filters.priceTo))
    )
    if filters.owner_id:
        base_stmt = (base_stmt.join(hotelroom.Hotels, hotelroom.Hotels.id == hotelroom.HotelRooms.hotel_id)
        .where(hotelroom.Hotels.user_id == filters.owner_id))
    if filters.status:
        base_stmt = base_stmt.where(hotelroom.HotelRooms.status == filters.status)
    if filters.id:
        base_stmt = base_stmt.where(hotelroom.HotelRooms.id == filters.id)
        await increase_view(filters.id, db)

    if filters.searchKeyword:
        keyword = f"%{filters.searchKeyword}%"
        base_stmt = base_stmt.where(
            (hotelroom.HotelRooms.title.ilike(keyword)) |
            (hotelroom.HotelRooms.description.ilike(keyword))
        )

    page = filters.page if filters.page and filters.page > 0 else 1
    row = min(filters.row if filters.row and filters.row > 0 else 10, 100)
    offset = (page - 1) * row
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await db.execute(count_stmt)).scalar()
    stmt = base_stmt.options(selectinload(hotelroom.HotelRooms.hotel))
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