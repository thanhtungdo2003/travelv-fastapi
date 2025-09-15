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
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await bookings_service.create(data=data,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    