from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base, engine, SessionLocal
from app.utils import auth
from app.services import oder_service

router = APIRouter()

async def get_db():
    async with SessionLocal() as session:
        yield session


@router.post("/create/{pay_token}")
async def create(pay_token: str, db: AsyncSession = Depends(get_db)):
    res = await oder_service.create(pay_token=pay_token, db=db)
    return res
