from app.utils import auth
import uuid
from datetime import datetime, timedelta
from pydantic import BaseModel
from app.models.bookings import BookingsPublic


class PackPayload(BaseModel):
    pack: str

def get_total_amount(price: int, passengers: list[dict]):
    total = 0
    for p in passengers:
        if p.age_type == 'Adult':
            total+=price
        elif p.age_type == 'Children':
            total+=(price*0.8)
    return total
        
def create_order_token(booking_id:str, a:int, user_id: str):
    return  auth.create_access_token(data={
        "booking_id": booking_id,
        "amount": a,
        "user_id": user_id
    }, expires_delta=timedelta(minutes=5))
