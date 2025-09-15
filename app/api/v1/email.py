
from fastapi import FastAPI, BackgroundTasks, APIRouter, Depends
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel, EmailStr
from app.schemas.email import EmailSchema
from app.utils import auth
from app.core.email import settings
from datetime import datetime, timedelta
from app.services import user_service
from app.core.database import Base, engine, SessionLocal
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db():
    async with SessionLocal() as session:
        yield session

email_conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
)
router = APIRouter()

@router.post("/verify-mail/{token}")
async def verify(token: str, db: AsyncSession=Depends(get_db)):
    payload = auth.verify_token(token)
    if not payload:
        return {"status": "failed", "error": "Unauthorize token!"}
    exist_user = await user_service.get_user_by_email(email=payload["email"], db=db)
    if exist_user:
        return {"status": "failed", "error": "Email has exist!"}
    new_user_encode = await user_service.create(email=payload["email"], 
                                          username=user_service.get_email_username(email=payload["email"]), 
                                          password=user_service.generate_random_password(12), db=db)
    
    return {"status": "success", "message": "Verify successffully!", 'data': new_user_encode}


@router.post("/send-verify-mail/{email}")
async def send_email(email: str, background_tasks: BackgroundTasks, db: AsyncSession=Depends(get_db)):
    exist_user = await user_service.get_user_by_email(email=email, db=db)
    if exist_user:
        return {"status": "failed", "error": "Email has exist!"}
    message = MessageSchema(
        subject="Alex - Verify your email",
        recipients=[email],
        body = f"""
        <div style="width: 100%; height: 500px; display: flex; justify-content: center; align-items: center;">
            <div style="margin: 0 auto; width: 400px; padding: 20px; border-radius: 10px; 
                        background-color: black; justify-content: center; 
                        align-items: center; color: white; text-align: center; border: 8px solid #CB2F30">
                <h3 style="margin-bottom: 10px; font-size: 80px; color: #CB2F30">Alex</h3><br/>
                <p style="margin-bottom: 20px;">Click this button to go back to Alex tools</p><br/>
                <a href="http://localhost:3000/auth/verify-email/{auth.create_access_token(data={"name":"verify", 'email': email}, expires_delta=timedelta(minutes=15))}" 
                style="display: inline-block; text-decoration: none; text-align: center;
                        width: 100px; height: 40px; line-height: 40px; 
                        color: white; background-color: #CE3435; border-radius: 3px; cursor: pointer">
                    Verify
                </a>
            </div>
        </div>
        """,

        subtype="html"
    )

    fm = FastMail(email_conf)
    try:
        await fm.send_message(message)
        return {"status": "success"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}