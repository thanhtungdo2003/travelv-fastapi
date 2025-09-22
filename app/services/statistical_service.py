from sqlalchemy import func, extract, case, desc, cast
from sqlalchemy.types import Numeric

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base, engine, SessionLocal
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import UUID
import uuid
from fastapi import Depends, HTTPException, status
from datetime import datetime, timedelta
from app.models import destinations, bookings, passengers, tours
from app.schemas import get_schema
from passlib.context import CryptContext
from app.utils import auth
from sqlalchemy.exc import IntegrityError
import string
import secrets
import math
import calendar

async def get_revenue_by_month(year: int, db: AsyncSession):
    stmt = (
        select(
            extract("month", bookings.Bookings.created_at).label("month"),
            func.sum(bookings.Bookings.total_amount).label("total_revenue"),
            func.sum(
                case(
                    (bookings.Bookings.status == bookings.BookingsStatusEnum.PAID, bookings.Bookings.total_amount),
                    else_=0
                )
            ).label("paid_revenue"),
        )
        .where(extract("year", bookings.Bookings.created_at) == year)
        .group_by("month")
        .order_by("month")
    )

    result = await db.execute(stmt)
    rows = result.all()
    revenue_map = {
        int(month): {
            "total_revenue": float(total) if total else 0,
            "paid_revenue": float(paid) if paid else 0
        }
        for month, total, paid in rows
    }

    current_year = datetime.now().year
    current_month = datetime.now().month
    last_month = current_month if year == current_year else 12

    data = [
        {
            "month_num": m,
            "month": calendar.month_abbr[m],
            "total_revenue": revenue_map.get(m, {}).get("total_revenue", 0.0),
            "paid_revenue": revenue_map.get(m, {}).get("paid_revenue", 0.0),
        }
        for m in range(1, last_month + 1)
    ]

    return data


async def get_top_tours_by_year(db: AsyncSession, n: int, year: int):
    stmt = (
        select(
            tours.Tours.id,
            tours.Tours.title,
            func.count(bookings.Bookings.id).label("bookings_count"),
            func.coalesce(func.sum(bookings.Bookings.total_amount), 0).label("total_revenue"),
            destinations.Destinations.title.label("destination_title")
        )
        .join(bookings.Bookings, bookings.Bookings.tour_id == tours.Tours.id)
        .join(destinations.Destinations, destinations.Destinations.id == tours.Tours.destination_id)
        .where(extract("year", bookings.Bookings.created_at) == year)
        .group_by(tours.Tours.id, tours.Tours.title, destinations.Destinations.title)
        .order_by(desc("total_revenue"))
        .limit(n)
    )

    result = await db.execute(stmt)
    rows = result.all()

    stmt_total = (
        select(func.coalesce(func.sum(bookings.Bookings.total_amount), 0))
        .where(extract("year", bookings.Bookings.created_at) == year)
    )
    total_result = await db.execute(stmt_total)
    total_revenue = total_result.scalar() or 0

    return [
        {
            "id": row.id,
            "title": row.title,
            "destination_title": row.destination_title,
            "bookings_count": row.bookings_count,
            "total_revenue": float(row.total_revenue),
            "percent": round((float(row.total_revenue) / float(total_revenue) * 100), 2) if total_revenue else 0.0
        }
        for row in rows
    ]