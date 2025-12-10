from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from app.models.tours import TourSchedules
import math
from sqlalchemy import func
from datetime import datetime, timedelta

async def create_schedule(data, db: AsyncSession):
    try:
        new_item = TourSchedules(**data.model_dump())
        db.add(new_item)
        await db.commit()
        await db.refresh(new_item)
        return new_item
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Failed to create schedule")

async def update_schedule(id: str, update_data, db: AsyncSession):
    result = await db.execute(select(TourSchedules).where(TourSchedules.id == id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(schedule, key, value)

    await db.commit()
    await db.refresh(schedule)
    return schedule

async def delete_schedule(id: str, db: AsyncSession):
    result = await db.execute(select(TourSchedules).where(TourSchedules.id == id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    await db.delete(schedule)
    await db.commit()
    return {"message": "Deleted successfully"}

async def get_schedules_by_tour(tour_id: str, page: int = 1, row: int = 10, db: AsyncSession = None):
    stmt = select(TourSchedules).where(TourSchedules.tour_id == tour_id)
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar()
    offset = (page - 1) * row

    result = await db.execute(stmt.offset(offset).limit(row))
    data = result.scalars().all()

    max_page = math.ceil(total / row) if row > 0 else 1
    return {
        "total": total,
        "page": page,
        "max_page": max_page,
        "row": row,
        "data": data
    }

async def get_all_schedules(db: AsyncSession):
    result = await db.execute(select(TourSchedules).options(selectinload(TourSchedules.tour)))
    return result.scalars().all()


async def auto_generate_schedules(tour_id: str, start_date: datetime, 
                                  estimate_time: int = 3,
                                  repeat_days: int = 7, 
                                  total_rounds: int = 10, 
                                  db=AsyncSession):

    schedules = []
    for i in range(total_rounds):
        s_date = start_date + timedelta(days=i * repeat_days)
        e_date = s_date + timedelta(days=estimate_time)
        schedule = TourSchedules(
            tour_id=tour_id,
            start_date=s_date,
            end_date=e_date,
            available_slots=20
        )
        db.add(schedule)
        schedules.append(schedule)
    await db.commit()
    return schedules

async def ensure_future_schedules(tour_id: str, db: AsyncSession):
    result = await db.execute(
        select(TourSchedules)
        .where(TourSchedules.tour_id == tour_id)
        .order_by(TourSchedules.start_date.desc())
        .limit(1)
    )
    latest_schedule = result.scalar_one_or_none()

    if not latest_schedule:
        await auto_generate_schedules(tour_id=tour_id, start_date=datetime.now(), db=db)
        return
    days_left = (latest_schedule.start_date - datetime.now()).days
    if days_left < 7:
        await auto_generate_schedules(
            tour_id,
            latest_schedule.start_date + timedelta(days=7),
            db,
        )
