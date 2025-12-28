
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
        <div style="width: 100%; min-height: 500px; display: flex; justify-content: center; align-items: center; font-family: Arial, sans-serif; background-color: #f5f7fa;">
    <div style="margin: 0 auto; max-width: 400px; padding: 30px; border-radius: 12px; 
                background-color: white; color: #333; text-align: center; 
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);">
        <!-- Logo/Header -->
        <div style="margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 32px; color: #2E86C1; font-weight: bold;">TravelV</h1>
            <p style="margin: 5px 0 0 0; font-size: 14px; color: #7F8C8D;">Explore the world with us</p>
        </div>
        
        <!-- Content -->
        <div style="margin-bottom: 30px;">
            <h3 style="margin-bottom: 15px; font-size: 22px; color: #2C3E50;">Verify Your Email Address</h3>
            <p style="margin-bottom: 10px; line-height: 1.5; color: #5D6D7E;">
                Thank you for signing up with TravelV. To complete your registration and start exploring amazing destinations, please verify your email address by clicking the button below.
            </p>
        </div>
        
        <!-- Verification Button -->
        <a href="http://localhost:3000/travelv-landingpage/auth/verify-email/{auth.create_access_token(data={'name':'verify', 'email': email}, expires_delta=timedelta(minutes=15))}" 
           style="display: inline-block; text-decoration: none; text-align: center;
                  width: 180px; padding: 12px 0; 
                  color: white; background-color: #3498DB; border-radius: 6px; 
                  font-weight: bold; font-size: 16px; cursor: pointer;
                  box-shadow: 0 2px 4px rgba(52, 152, 219, 0.3); transition: background-color 0.3s;">
            Verify Email
        </a>
        
        <!-- Footer -->
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ECF0F1;">
            <p style="margin: 0; font-size: 12px; color: #95A5A6;">
                If you did not create an account with TravelV, please ignore this email.
            </p>
        </div>
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