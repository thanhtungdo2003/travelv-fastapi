
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import APIRouter, UploadFile, Response, Query, Depends, HTTPException
from app.services import blogs_service
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base, engine, SessionLocal
from app.models import blogs
from app.schemas import get_schema
from sqlalchemy.dialects.postgresql import UUID
import uuid
import json
from app.utils import auth
router = APIRouter()

async def get_db():
    async with SessionLocal() as session:
        yield session


@router.post("/create")
async def blog_create(data: blogs.BlogCreate, db: AsyncSession = Depends(get_db), user_id: str = Depends(auth.verify_token_user)):
    result = await blogs_service.create(title=data.title,
                                        content=data.content,
                                        imageURL=data.imageURL,
                                        tag=data.tag,
                                        user_id=user_id,
                                       db=db)
    if not result:
        raise HTTPException(status_code=400, detail="Error while creation new blog!")
    return result

@router.post("/get")
async def blog_get(get_schem: get_schema.GetSchema, db: AsyncSession = Depends(get_db)):
    result = await blogs_service.get(get_schem=get_schem, db=db)
    return result