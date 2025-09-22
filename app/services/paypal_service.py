from fastapi import FastAPI, Request
import requests
import base64
import httpx
from fastapi import HTTPException
from app.utils import auth, payment
from app.services import bookings_service
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException


PAYPAL_CLIENT_ID = "AZJM416AJv3dwgYx3N9PK0NADEaYR_Gx0Y2rlP-3Sgrxs3njBp_AI25hsVogBMnsjVGcn24poaH3NusY"
PAYPAL_SECRET = "ELPXKEhIiWPcTeq7Q4k7LeA55Ynude3gzSlTYk9hdtkjDMXZPxi8vOkCx3Yoq2OKKb9mtOYkzzWy7MVk"
PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com"



async def get_access_token():
    auth_str = f"{PAYPAL_CLIENT_ID}:{PAYPAL_SECRET}"
    encoded_auth = base64.b64encode(auth_str.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{PAYPAL_BASE_URL}/v1/oauth2/token", headers=headers, data=data)
            resp.raise_for_status()
            return resp.json()["access_token"]
    except httpx.RequestError as e:
        print(f"PayPal get_access_token failed: {e}")
        raise HTTPException(status_code=503, detail="Cannot connect to PayPal")
    except httpx.HTTPStatusError as e:
        print(f"PayPal get_access_token failed: {e.response.text}")
        raise HTTPException(status_code=503, detail="Cannot connect to PayPal")

async def create_order(booking_id: str, user_id: str, db: AsyncSession):
    try:
        access_token = await get_access_token()
        booking = await bookings_service.get_by_id(id=booking_id, db=db)
        usd_amount = booking.total_amount / 24000
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        body = {
            "intent": "CAPTURE",
            "purchase_units": [{"amount": {"currency_code": "USD", "value": f"{usd_amount:.2f}"}}],
            "application_context": {
                "return_url": f"http://localhost:3000/paypal-success/{payment.create_order_token(booking_id=booking_id, a=booking.total_amount, user_id=user_id)}",
                "cancel_url": "http://localhost:3000/"
            }
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{PAYPAL_BASE_URL}/v2/checkout/orders", headers=headers, json=body)
            resp.raise_for_status()
            order = resp.json()

        approve_url = next(link["href"] for link in order.get("links", []) if link["rel"] == "approve")
        return {"order_id": order["id"], "approve_url": approve_url}

    except httpx.HTTPStatusError as e:
        raise Exception(f"PayPal API error: {e.response.text}")
    except Exception as e:
        raise e
    except requests.exceptions.HTTPError as e:
        try:
            error_data = resp.json()
        except Exception:
            error_data = resp.text
        print(f"PayPal create_order failed: {e}, details: {error_data}")
        raise HTTPException(status_code=400, detail=error_data)

    except requests.exceptions.RequestException as e:
        print(f"PayPal create_order request failed: {e}")
        raise HTTPException(status_code=503, detail="Cannot connect to PayPal")

async def capture_order(order_id: str):
    try:
        access_token = await get_access_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        async with httpx.AsyncClient(timeout=30) as client:
            
            resp = await client.post(
                f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture",
                headers=headers
            )
            resp.raise_for_status()
            return resp.json()

    except httpx.HTTPStatusError as e:
        try:
            error_data = e.response.json()
        except Exception:
            error_data = e.response.text
        print(f"PayPal capture failed: {e}, details: {error_data}")
        return {"status": "FAILURE", "error": str(e), "details": error_data}

    except httpx.RequestError as e:
        print(f"PayPal capture request failed: {e}")
        return {"status": "FAILURE", "error": str(e), "details": "Cannot connect to PayPal"}