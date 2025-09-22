from app.core import momo
from fastapi import APIRouter, Depends, HTTPException, status 
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base, engine, SessionLocal
from app.utils import auth, payment
from app.services import paypal_service, oder_service, bookings_service

router = APIRouter()

async def get_db():
    async with SessionLocal() as session:
        yield session


@router.post("/momo/create/{booking_id}")
async def momo_create(booking_id:str, user_id: str = Depends(auth.verify_token_user), db: AsyncSession=Depends(get_db)):
    try:     
        booking = await bookings_service.get_by_id(id=booking_id, db=db)
        momo_res = momo.create(booking_id=booking_id, a=int(booking.total_amount), user_id=user_id)
        return momo_res
    except HTTPException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )


@router.post("/paypal/create/{booking_id}")
async def paypal_create(booking_id: str, user_id: str = Depends(auth.verify_token_user), db: AsyncSession=Depends(get_db)):
    res = await paypal_service.create_order(booking_id=booking_id, user_id=user_id, db=db)
    return res

@router.post("/paypal/capture")
async def paypal_capture(order_id: str, pay_token:str, db: AsyncSession=Depends(get_db)):
    res = await paypal_service.capture_order(order_id=order_id)
    if res["status"] == 'COMPLETED':
       booking = await bookings_service.paid(pay_token=pay_token, db=db)
       return booking
    return res

