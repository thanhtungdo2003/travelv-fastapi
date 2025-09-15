from app.models import order, user
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils import auth
from fastapi import HTTPException, status
from sqlalchemy.future import select
from datetime import datetime, timedelta

async def create(pay_token: str, 
        db: AsyncSession):
    """
    """
    order_data = auth.verify_token(token=pay_token)
    if not order_data or not isinstance(order_data, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token: decode failed or empty payload"
        )
    try:

        new_order = order.Orders(id=order_data["order_id"],
                                user_id=order_data["user_id"],
                                pack=order_data["pack"],
                                amount=order_data["amount"],
                                status="PAID")
        db.add(new_order)

        raw_user = await db.execute(select(user.Users).where(user.Users.id == order_data["user_id"]))
        payer = raw_user.scalar_one_or_none()
        if not payer:
            raise HTTPException(status_code=404, detail="User not found")
        days = 0
        if order_data["pack"] == "month":
            days = 30
        elif order_data["pack"] == "year":
            days = 365
        elif order_data["pack"] == "life":
            days = 1000000

        if not payer.premium_ex or payer.premium_ex < datetime.utcnow():
            payer.premium_ex = datetime.utcnow() + timedelta(days=days)
        else:
            payer.premium_ex = payer.premium_ex + timedelta(days=days)

        await db.commit()
        await db.refresh(new_order)
    except Exception as ex:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(ex)}"
        )
    
    return {"status":"success", "data":new_order}
