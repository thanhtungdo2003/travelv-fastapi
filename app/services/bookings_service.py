from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base, engine, SessionLocal
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import UUID
import uuid
from fastapi import Depends, HTTPException, status
from datetime import datetime, timedelta
from app.models import bookings, passengers
from app.schemas import get_schema
from app.utils import payment
from passlib.context import CryptContext
from app.utils import auth
from sqlalchemy.exc import IntegrityError
import string
import secrets
from sqlalchemy.orm import selectinload
import math

async def create(data: bookings.BookingsCreation, db: AsyncSession):
    try:
        passengers_data = data.passengers
        booking_dict = data.model_dump(exclude={"passengers"})
        
        new_item = bookings.Bookings(**booking_dict)
        new_item.passengers = [passengers.Passengers(**p.dict()) for p in passengers_data]

        db.add(new_item)
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
                selectinload(bookings.Bookings.tour)  
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Booking not found")
        item.total_amount = payment.get_total_amount(price=item.tour.price, passengers=item.passengers)
        return item
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
            .options(selectinload(bookings.Bookings.tour), selectinload(bookings.Bookings.passengers))
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

    
async def get(filters: get_schema.GetSchema, db: AsyncSession):
    try:
        stmt = select(bookings.Bookings)
        stmt = stmt.options(
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