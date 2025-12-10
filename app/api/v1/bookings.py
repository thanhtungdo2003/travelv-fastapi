from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import APIRouter, UploadFile, Response, Query, Depends, HTTPException, status
from app.services import bookings_service
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base, engine, SessionLocal
from app.schemas import get_schema
from app.models import bookings, passengers
from sqlalchemy.dialects.postgresql import UUID
import uuid
import json
from app.utils import auth
router = APIRouter()

async def get_db():
    async with SessionLocal() as session:
        yield session



@router.post("/create")
async def booking_create(
    data: bookings.BookingsCreation, 
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(auth.verify_token_user)
):
    try:
        result = await bookings_service.create(user_id=user_id,data=data,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
@router.get("/get/{id}")
async def get_booking(
    id: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await bookings_service.get_by_id(id=id, db=db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
@router.post("/user")
async def get_bookings_by_user(
    filters: get_schema.GetSchema,
    user_id: str = Depends(auth.verify_token_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await bookings_service.get_by_user_id(id=user_id,filters=filters, db=db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/get")
async def get_bookings(
    filters: get_schema.GetSchema,
    db: AsyncSession = Depends(get_db),
    has_role: bool = Depends(auth.has_role("ADMIN"))
):
    if not has_role:
        raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not permisstion!"
    )
    result = await bookings_service.get(filters=filters, db=db)
    return result

@router.post("/get-booking-rooms/{booking_id}")
async def get(
    booking_id: str,
    filters: get_schema.GetSchema,
    db: AsyncSession = Depends(get_db),
):
    result = await bookings_service.get_booking_room(booking_id=booking_id, filters=filters, db=db)
    return result


@router.post("/paid/{pay_token}")
async def paid_booking(pay_token: str, db: AsyncSession = Depends(get_db)):
    res = await bookings_service.paid(pay_token=pay_token, db=db)
    return res


@router.put("/cancel/{booking_id}")
async def paid_booking(booking_id: str, user_id: str = Depends(auth.verify_token_user), db: AsyncSession = Depends(get_db)):
    res = await bookings_service.cancel(booking_id=booking_id, user_id=user_id, db=db)
    return res
