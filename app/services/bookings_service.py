from sqlalchemy import func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base, engine, SessionLocal
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import UUID
import uuid
from fastapi import Depends, HTTPException, status
from datetime import datetime, timedelta
from app.models import bookings, passengers, hotelroom
from app.schemas import get_schema
from app.utils import payment
from passlib.context import CryptContext
from app.utils import auth
from sqlalchemy.exc import IntegrityError
import string
import secrets
from sqlalchemy.orm import selectinload
import math

async def create(user_id: str, data: bookings.BookingsCreation, db: AsyncSession):
    try:
        passengers_data = data.passengers
        booking_dict = data.model_dump(exclude={"passengers", "selected_rooms"})
        selected_rooms = data.selected_rooms
        new_item = bookings.Bookings(**booking_dict)
        new_item.user_id = user_id
        new_item.passengers = [passengers.Passengers(**p.dict()) for p in passengers_data]
        db.add(new_item)
        await db.flush() 
        rooms = (
            await db.execute(
                select(hotelroom.HotelRooms).where(hotelroom.HotelRooms.id.in_(selected_rooms))
            )
        ).scalars().all()

        for room in rooms:
            new_booking_room = hotelroom.BookingRooms(
                booking_id=new_item.id,
                room_id=room.id,
                price_per_night=room.price,
                total_room_price=0,
            )
            db.add(new_booking_room)
        await db.commit()
        await db.refresh(new_item)
        return new_item

    except IntegrityError:
        await db.rollback()
        raise

async def get_by_id(id: str, db: AsyncSession):
    try:
        result = await db.execute(
            select(bookings.Bookings)
            .where(bookings.Bookings.id == id)
            .options(
                selectinload(bookings.Bookings.passengers),  
                selectinload(bookings.Bookings.tour),
                selectinload(bookings.Bookings.booking_rooms)
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Booking not found")
        item.total_amount = payment.get_total_amount(price=item.tour.price, passengers=item.passengers)
        return item
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
async def get_booking_room(booking_id: str, filters: get_schema.GetSchema, db: AsyncSession):
    try:
        stmt = select(hotelroom.BookingRooms)
        stmt = stmt.filter(hotelroom.BookingRooms.booking_id == booking_id).options(
            selectinload(hotelroom.BookingRooms.booking),  
            selectinload(hotelroom.BookingRooms.room)  
        )

        if filters.id:
            stmt = stmt.filter(hotelroom.BookingRooms.id == filters.id)
        if filters.searchKeyword:
            keyword = f"%{filters.searchKeyword.strip()}%"
            stmt = stmt.where(
                (hotelroom.BookingRooms.price_per_night.ilike(keyword))
            )
        stmt = stmt.order_by(desc(hotelroom.BookingRooms.created_at))
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_by_user_id(id: str, filters: get_schema.GetSchema, db: AsyncSession):
    try:
        stmt = select(bookings.Bookings)
        stmt = stmt.filter(bookings.Bookings.user_id == id).options(
                selectinload(bookings.Bookings.passengers),  
                selectinload(bookings.Bookings.tour)  
            )

        if filters.id:
            stmt = stmt.filter(bookings.Bookings.id == filters.id)
        if filters.searchKeyword:
            keyword = f"%{filters.searchKeyword.strip()}%"
            stmt = stmt.where(
                (bookings.Bookings.fullname.ilike(keyword))
            )
        stmt = stmt.order_by(desc(bookings.Bookings.created_at))
        page = filters.page if filters.page and filters.page > 0 else 1
        row = min(filters.row if filters.row and filters.row > 0 else 10, 100)
        offset = (page - 1) * row
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar()
        result = await db.execute(stmt.offset(offset).limit(row))
        data = result.scalars().all()
        max_page = math.ceil(total / row) if row > 0 else 1

        for booking in data:
            booking.total_amount = payment.get_total_amount(price=booking.tour.price, passengers=booking.passengers)

        return {
            "total": total,
            "page": page,
            "row": row,
            "max_page": max_page,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

async def paid(pay_token: str, db: AsyncSession):
    try:
        pay_payload = auth.verify_token(pay_token)

        result = await db.execute(
            select(bookings.Bookings)
            .where(bookings.Bookings.id == pay_payload['booking_id'])
            .options(selectinload(bookings.Bookings.tour), selectinload(bookings.Bookings.passengers), 
            selectinload(bookings.Bookings.booking_rooms))
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Booking not found")
        item.status = 'Paid'
        item.total_amount = payment.get_total_amount(price=item.tour.price, passengers=item.passengers)

        await db.commit()
        await db.refresh(item)

        return item

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
async def cancel(booking_id: str, user_id: str,  db: AsyncSession):
    try:
        result = await db.execute(
            select(bookings.Bookings)
            .where(bookings.Bookings.id == booking_id)
            .options(selectinload(bookings.Bookings.tour), selectinload(bookings.Bookings.passengers), 
            selectinload(bookings.Bookings.booking_rooms))
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Booking not found")
        if (str(item.user_id) != user_id):
            raise HTTPException(status_code=404, detail="Booking not found")

        item.status = bookings.BookingsStatusEnum.CANCELED
        item.total_amount = payment.get_total_amount(price=item.tour.price, passengers=item.passengers)

        await db.commit()
        await db.refresh(item)

        return item

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    
async def get(filters: get_schema.GetSchema, db: AsyncSession):
    try:
        stmt = select(bookings.Bookings)
        stmt = stmt.options(
                selectinload(bookings.Bookings.passengers),  
                selectinload(bookings.Bookings.tour)  
            )
        stmt = stmt.order_by(desc(bookings.Bookings.created_at))

        if filters.id:
            stmt = stmt.filter(bookings.Bookings.id == filters.id)
        if filters.searchKeyword:
            keyword = f"%{filters.searchKeyword.strip()}%"
            stmt = stmt.where(
                (bookings.Bookings.fullname.ilike(keyword))
            )
        page = filters.page if filters.page and filters.page > 0 else 1
        row = min(filters.row if filters.row and filters.row > 0 else 10, 100)
        offset = (page - 1) * row
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar()
        result = await db.execute(stmt.offset(offset).limit(row))
        data = result.scalars().all()
        max_page = math.ceil(total / row) if row > 0 else 1

        for booking in data:
            booking.total_amount = payment.get_total_amount(price=booking.tour.price, passengers=booking.passengers)

        return {
            "total": total,
            "page": page,
            "row": row,
            "max_page": max_page,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))