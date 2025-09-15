from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import APIRouter, UploadFile, Response, Query, Depends, HTTPException, status
from app.services import tours_service
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base, engine, SessionLocal
from app.schemas import get_schema
from app.models.tours import TourCreation, TourUpdate
from sqlalchemy.dialects.postgresql import UUID
import uuid
import json
from app.utils import auth
router = APIRouter()

async def get_db():
    async with SessionLocal() as session:
        yield session



@router.post("/create")
async def tour_create(
    data: TourCreation, 
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await tours_service.create(data=data,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    

@router.post("/update/{id}")
async def tour_create(
    id: str,
    data: TourUpdate,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await tours_service.update(
            id=id,
            updateItem=data,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )



@router.post("/get")
async def get_tours(data: get_schema.GetSchema, db: AsyncSession = Depends(get_db)):
    try:
        result = await tours_service.get_tours(filters=data, db=db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )