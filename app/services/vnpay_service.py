import hashlib
import hmac
from fastapi import FastAPI, Request
from urllib.parse import urlencode
from datetime import datetime
from app.utils import auth
import uuid
from datetime import datetime, timedelta
VNP_URL = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
VNP_TMN_CODE = "YOUR_TMN_CODE"
VNP_HASH_SECRET = "YOUR_SECRET"
VNP_RETURN_URL = "https://yourdomain.com/payment_return"

def create_payment(pack: str, user_id: str):
    oid = uuid.uuid4()
    a = 0
    if pack == 'month':
        a = 12906
    elif pack == 'year':
        a = 134597
    elif pack == 'life':
        a = 790200
        
    token = auth.create_access_token(data={
        "order_id": str(oid),
        "pack" : pack,
        "amount": a,
        "user_id": user_id
    }, expires_delta=timedelta(minutes=5))



    vnp_version = "2.1.0"
    vnp_command = "pay"
    vnp_order_info = "Thanh toan don hang test"
    vnp_order_type = "other"
    vnp_txn_ref = datetime.now().strftime("%Y%m%d%H%M%S")
    vnp_ip_addr = "127.0.0.1"
    vnp_create_date = datetime.now().strftime("%Y%m%d%H%M%S")

    input_data = {
        "vnp_Version": vnp_version,
        "vnp_Command": vnp_command,
        "vnp_TmnCode": VNP_TMN_CODE,
        "vnp_Amount": str(a * 100),  # nhân 100 theo chuẩn VNPAY
        "vnp_CurrCode": "VND",
        "vnp_TxnRef": vnp_txn_ref,
        "vnp_OrderInfo": vnp_order_info,
        "vnp_OrderType": vnp_order_type,
        "vnp_Locale": "vn",
        "vnp_ReturnUrl": VNP_RETURN_URL,
        "vnp_IpAddr": vnp_ip_addr,
        "vnp_CreateDate": vnp_create_date
    }

    # sort param
    sorted_keys = sorted(input_data)
    query_string = urlencode({k: input_data[k] for k in sorted_keys})
    # hash
    hash_data = hmac.new(VNP_HASH_SECRET.encode(), query_string.encode(), hashlib.sha512).hexdigest()
    payment_url = f"{VNP_URL}?{query_string}&vnp_SecureHash={hash_data}"

    return {"payment_url": payment_url}
