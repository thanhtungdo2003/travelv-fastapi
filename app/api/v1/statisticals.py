from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import APIRouter, UploadFile, Response, Query, Depends, HTTPException, status
from app.services import statistical_service
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


@router.get("/get_revenue_by_month/{year}")
async def get_tours(year: int, db: AsyncSession = Depends(get_db), has_role: bool = Depends(auth.has_role("ADMIN"))):
    try:
        result = await statistical_service.get_revenue_by_month(year=year, db=db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
@router.get("/get_best_tour")
async def get_tours(top: int,year: int, db: AsyncSession = Depends(get_db), has_role: bool = Depends(auth.has_role("ADMIN"))):
    try:
        result = await statistical_service.get_top_tours_by_year(n=top, year=year, db=db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    