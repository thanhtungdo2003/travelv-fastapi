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
from passlib.context import CryptContext
from app.utils import auth
from sqlalchemy.exc import IntegrityError
import string
import secrets
from sqlalchemy.orm import selectinload

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
