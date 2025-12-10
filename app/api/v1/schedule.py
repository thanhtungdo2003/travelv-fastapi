# app/routers/schedules.py
from fastapi import APIRouter, Depends
from app.models.tours import ScheduleCreate, ScheduleUpdate
from backend.app.services import schedules_service
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base, engine, SessionLocal

router = APIRouter()

async def get_db():
    async with SessionLocal() as session:
        yield session

@router.post("/")
async def create_schedule(data: ScheduleCreate, db: AsyncSession = Depends(get_db)):
    return await schedules_service.create_schedule(data, db)

@router.put("/{id}")
async def update_schedule(id: str, data: ScheduleUpdate, db: AsyncSession = Depends(get_db)):
    return await schedules_service.update_schedule(id, data, db)

@router.get("/tour/{tour_id}")
async def get_schedules_by_tour(tour_id: str, db: AsyncSession = Depends(get_db)):
    return await schedules_service.get_schedules_by_tour(tour_id, db=db)

@router.delete("/{id}")
async def delete_schedule(id: str, db: AsyncSession = Depends(get_db)):
    return await schedules_service.delete_schedule(id, db)
