from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import APIRouter, UploadFile, Response, Query, Depends, HTTPException, status
from app.services import user_service
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base, engine, SessionLocal
from app.models.user import UserSignin, UserLogin, UserUpdate, UserUpdateByAdmin
from sqlalchemy.dialects.postgresql import UUID
import uuid
import json
from app.utils import auth
from app.schemas import get_schema
router = APIRouter()

async def get_db():
    async with SessionLocal() as session:
        yield session



@router.post("/signin")
async def user_signin(data: UserSignin, db: AsyncSession = Depends(get_db)):
    result = await user_service.create(email=data.email,
                                       username=data.username,
                                       password=data.password,
                                       db=db)
    if not result:
        raise HTTPException(status_code=400, detail="Incorrect email or password!")
    return result


@router.post("/login")
async def user_login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await user_service.login(email=data.email,
                                       password=data.password,
                                       db=db)
    if not result:
        raise HTTPException(status_code=400, detail="Wrong email or password!")
    return result

@router.get("/get-by-email/{email}")
async def user_login(email: str, db: AsyncSession = Depends(get_db)):
    result = await user_service.get_user_by_email(email=email, db=db)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result


@router.patch("/update")
async def user_login(data: UserUpdate, 
                     db: AsyncSession = Depends(get_db),
                     user_id: str = Depends(auth.verify_token_user)):
    try:
        result = await user_service.update_user(user_id=user_id, data=data, db=db)
        return {'status':'success', 'data': result}
    except HTTPException as ex:
        return ex
    
@router.patch("/update-by-admin/{user_id}")
async def user_login(data: UserUpdateByAdmin, 
                     user_id: str,
                     db: AsyncSession = Depends(get_db),
                     has_role: bool = Depends(auth.has_role('ADMIN'))
                     ):
    try:
        result = await user_service.update_user_by_admin(user_id=user_id, data=data, db=db)
        return {'status':'success', 'data': result}
    except HTTPException as ex:
        return ex
    

@router.post("/get")
async def get_users(data: get_schema.GetSchema, db: AsyncSession = Depends(get_db), has_role: bool = Depends(auth.has_role("ADMIN"))):
    try:
        result = await user_service.get_all_users(filters=data, db=db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )