from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import APIRouter, UploadFile, Response, Query, Depends, HTTPException, status
from app.services import destinations_service
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base, engine, SessionLocal
from app.schemas import get_schema
from app.models.destinations import DestinationCreation, DestinationUpdate
from sqlalchemy.dialects.postgresql import UUID
import uuid
import json
from app.utils import auth
router = APIRouter()

async def get_db():
    async with SessionLocal() as session:
        yield session



@router.post("/create")
async def destination_create(
    data: DestinationCreation, 
    db: AsyncSession = Depends(get_db),
    has_role: bool = Depends(auth.has_role("ADMIN"))

):
    try:
        result = await destinations_service.create(
            title=data.title, 
            description=data.description, 
            thumbnailURL=data.thumbnailURL,
            lat=data.lat, 
            lng=data.lng,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    

@router.post("/update/{id}")
async def destination_create(
    id: str,
    data: DestinationUpdate,
    db: AsyncSession = Depends(get_db),
    has_role: bool = Depends(auth.has_role("ADMIN"))

):
    try:
        result = await destinations_service.update(
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
async def get_destinations(data: get_schema.GetSchema, db: AsyncSession = Depends(get_db)):
    try:
        result = await destinations_service.get_destinations(filters=data, db=db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
@router.post("/get-disableds")
async def get_destinations(data: get_schema.GetSchema, db: AsyncSession = Depends(get_db), has_role: bool = Depends(auth.has_role('ADMIN'))):
    try:
        result = await destinations_service.get_disable_destinations(filters=data, db=db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )