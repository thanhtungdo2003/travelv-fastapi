from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import get_schema
from app.models import hotelroom
from app.services import room_service, hotel_service
from app.utils import auth
from typing import Any
from app.core.database import Base, engine, SessionLocal

router = APIRouter()

async def get_db():
    async with SessionLocal() as session:
        yield session

@router.post("/create")
async def create_hotel(
    data: hotelroom.HotelCreate,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(auth.verify_token_user)
):
    return await hotel_service.create(owner_id, data, db)

@router.put("/update/{id}")
async def update_hotel(
    id: str,
    data: hotelroom.HotelUpdate,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(auth.verify_token_user)
):
    return await hotel_service.update(owner_id, id, data, db)


@router.post("/get")
async def get_hotels(
    filters: get_schema.GetHotelSchema,
    db: AsyncSession = Depends(get_db)
):
    return await hotel_service.get_hotelroom(filters, db)


@router.post("/user/{user_id}")
async def get_hotel_by_user_id(
    user_id: str,
    filters: get_schema.GetHotelSchema,
    db: AsyncSession = Depends(get_db)
):
    return await hotel_service.get_hotel_by_user_id(user_id, filters, db)

