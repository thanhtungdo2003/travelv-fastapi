from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import APIRouter, UploadFile, Response, Query, Depends, HTTPException, status
from app.services import room_service
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base, engine, SessionLocal
from app.schemas import get_schema
from app.models import hotelroom
from sqlalchemy.dialects.postgresql import UUID
import uuid
import json
from app.utils import auth
router = APIRouter()

async def get_db():
    async with SessionLocal() as session:
        yield session

@router.post("/create")
async def create_hotel_room(
    room_data: hotelroom.RoomCreation,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(auth.verify_token_user)
):
    try:
        new_room = await room_service.create(owner_id, room_data, db)
        return new_room
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/create-tour-room")
async def create_link(
    tour_id: str,
    room_id: str,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(auth.verify_token_user)
):
    try:
        res = await room_service.set_tour_room(owner_id=owner_id, tour_id=tour_id, room_id=room_id, db=db)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.delete("/delete-tour-room")
async def delete_link(
    id: str,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(auth.verify_token_user)
):
    try:
        res = await room_service.delete_tour_room(owner_id=owner_id, id=id, db=db)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{room_id}", response_model=hotelroom.RoomUpdate)
async def update_hotel_room(
    room_id: str,
    room_data: hotelroom.RoomUpdate,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(auth.verify_token_user)
):
    try:
        updated_room = await room_service.update(owner_id, room_id, room_data, db)
        return updated_room
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/get", status_code=status.HTTP_200_OK)
async def get_all_hotel_rooms(
    filters: get_schema.GetRoomSchema,
    db: AsyncSession = Depends(get_db),
):
    result = await room_service.get_hotelroom(filters, db)
    return result

@router.post("/get-tour-rooms")
async def get_tourrooms(
    filters: get_schema.GetTourRoomSchema,
    db: AsyncSession = Depends(get_db),
):
    result = await room_service.get_tour_room(filters, db)
    return result

@router.post("/get-by-tour/{tour_id}", status_code=status.HTTP_200_OK)
async def get_hotel_rooms_by_tour_id(
    tour_id: str,
    filters: get_schema.GetRoomSchema,
    db: AsyncSession = Depends(get_db),
):
    result = await room_service.get_hotelroom_by_tour_id(tour_id, filters, db)
    return result

@router.post("/get-by-hotel/{hotel_id}", status_code=status.HTTP_200_OK)
async def get_hotel_rooms_by_hotel_id(
    hotel_id: str,
    filters: get_schema.GetRoomSchema,
    db: AsyncSession = Depends(get_db),
):
    result = await room_service.get_hotelroom_by_hotel_id(hotel_id, filters, db)
    return result