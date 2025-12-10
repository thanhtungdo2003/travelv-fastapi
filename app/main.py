from fastapi import FastAPI
from app.api.v1 import user, email, payment, order, blog, destinations, tours, bookings, statisticals, room, hotels
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine, SessionLocal
from app.models.user import Users
from app.models.order import Orders
from app.models.blogs import Blogs
from app.models.destinations import Destinations
from app.models.tours import Tours
from app.models.bookings import Bookings
from app.models.hotelroom import BookingRooms, TourRooms, HotelRooms, Hotels
from app.models.passengers import Passengers
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel, EmailStr

import os
import uvicorn


app = FastAPI()

async def get_db():
    async with SessionLocal() as session:
        yield session

# Khởi tạo DB (chạy 1 lần lúc start)
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

origins = [
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "http://localhost:4000",
    "http://127.0.0.1:4000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://thanhtungdo2003.github.io",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router, prefix="/api/v1/user", tags=["Users"])
app.include_router(email.router, prefix="/api/v1/email", tags=["Email"])
app.include_router(payment.router, prefix="/api/v1/payment", tags=["Payment"])
app.include_router(order.router, prefix="/api/v1/order", tags=["Order"])
app.include_router(blog.router, prefix="/api/v1/blog", tags=["Blog"])
app.include_router(destinations.router, prefix="/api/v1/destinations", tags=["Destinations"])
app.include_router(tours.router, prefix="/api/v1/tours", tags=["Tours"])
app.include_router(bookings.router, prefix="/api/v1/bookings", tags=["Bookings"])
app.include_router(statisticals.router, prefix="/api/v1/statisticals", tags=["Statisticals"])
app.include_router(room.router, prefix="/api/v1/rooms", tags=["Rooms"])
app.include_router(hotels.router, prefix="/api/v1/hotels", tags=["Hotels"])

@app.get("/")
def root():
    return {"msg": "AI backend is running"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)