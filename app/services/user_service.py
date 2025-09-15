from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base, engine, SessionLocal
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import UUID
import uuid
from fastapi import Depends, HTTPException, status
from datetime import datetime, timedelta
from app.models.user import Users, UserSignin, UserUpdate
from passlib.context import CryptContext
from app.utils import auth
from sqlalchemy.exc import IntegrityError
import string
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)



async def create(
        email: str,
        username: str, 
        password: str, 
        db: AsyncSession):
    """
    """
    try:
        new_user = Users(email=email, 
                            username=username, 
                            password=hash_password(password=password))
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        payload = {
            'user_id': str(new_user.id)
        }
        token = auth.create_access_token(data=payload, expires_delta=timedelta(days=15))

        return {"access_token": token, 
                "token_type": "bearer",
                "user_id": new_user.id,
                "user_name": new_user.username,
                "email": new_user.email}
    except IntegrityError:
        await db.rollback()
        return {"error": "Email already used"}
    
async def login(
        email: str,
        password: str, 
        db: AsyncSession):
    """
    """
    result = await db.execute(select(Users).where(Users.email == email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found!")
    if not verify_password(plain_password=password, hashed_password=user.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    payload = {
        'user_id': str(user.id)
    }
    token = auth.create_access_token(data=payload, expires_delta=timedelta(days=15))

    return {"access_token": token, 
            "token_type": "bearer",
            "user_id": user.id,
            "user_name": user.username,
            "email": user.email}

async def get_user_by_email(email:str, db: AsyncSession) -> UserSignin:
    result = await db.execute(select(Users).where(Users.email == email))
    user = result.scalars().first()
    if not user:
        return None
    del user.password
    del user.id
    return user

async def update_user(user_id:str, data: UserUpdate, db: AsyncSession):
    result = await db.execute(select(Users).where(Users.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if data.email:
        user.email = data.email
    if data.username:
        user.username = data.username
    if data.password:
        user.password = hash_password(data.password)

    await db.commit()
    await db.refresh(user)
    del user.password
    return user    

def get_email_username(email: str) -> str | None:
    if not isinstance(email, str) or "@" not in email:
        return None
    return email.split("@")[0]

def generate_random_password(length: int = 12) -> str:
    if length < 4:
        raise ValueError("Password length should be at least 4")
    chars = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(chars) for _ in range(length))
    return password