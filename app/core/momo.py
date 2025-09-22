import json
import uuid
import requests
import hmac
import hashlib
from app.utils import auth, payment
from datetime import datetime, timedelta


def create(booking_id: str, a: int, user_id: str):
    oid = str(uuid.uuid4())
    token = auth.create_access_token(data={
        "booking_id": booking_id,
        "amount": a,
        "user_id": user_id
    }, expires_delta=timedelta(minutes=5))

    print(token)
    endpoint = "https://test-payment.momo.vn/v2/gateway/api/create"
    accessKey = "F8BBA842ECF85"
    secretKey = "K951B6PE1waDMi640xX08PD3vg6EkVlz"
    orderInfo = "pay with MoMo"
    partnerCode = "MOMO"
    redirectUrl = f"http://localhost:3000/pay-success/{token}"
    ipnUrl = "https://webhook.site/b3088a6a-2d17-4f8d-a383-71389a6c600b"
    amount = a
    orderId = oid
    requestId = str(uuid.uuid4())
    extraData = ""  # pass empty value or Encode base64 JsonString
    partnerName = "MoMo Payment"
    requestType = "payWithMethod"
    storeId = "Test Store"
    orderGroupId = ""
    autoCapture = True
    lang = "vi"
    orderGroupId = ""

    # before sign HMAC SHA256 with format: accessKey=$accessKey&amount=$amount&extraData=$extraData&ipnUrl=$ipnUrl
    # &orderId=$orderId&orderInfo=$orderInfo&partnerCode=$partnerCode&redirectUrl=$redirectUrl&requestId=$requestId
    # &requestType=$requestType
    rawSignature = f"accessKey=" + accessKey + "&amount=" + str(amount) + "&extraData=" + extraData + "&ipnUrl=" + ipnUrl + "&orderId=" + orderId \
                + "&orderInfo=" + orderInfo + "&partnerCode=" + partnerCode + "&redirectUrl=" + redirectUrl\
                + "&requestId=" + requestId + "&requestType=" + requestType
    
    # puts raw signature
    # signature
    h = hmac.new(bytes(secretKey, 'ascii'), bytes(rawSignature, 'ascii'), hashlib.sha256)
    signature = h.hexdigest()

    # json object send to MoMo endpoint

    data = {
        'partnerCode': partnerCode,
        'orderId': orderId,
        'partnerName': partnerName,
        'storeId': storeId,
        'ipnUrl': ipnUrl,
        'amount': amount,
        'lang': lang,
        'requestType': requestType,
        'redirectUrl': redirectUrl,
        'autoCapture': autoCapture,
        'orderInfo': orderInfo,
        'requestId': requestId,
        'extraData': extraData,
        'signature': signature,
        'orderGroupId': orderGroupId
    }
    data = json.dumps(data)
    clen = len(data)
    response = requests.post(endpoint, data=data, headers={'Content-Type': 'application/json', 'Content-Length': str(clen)})
    print(f'Payment with Momo: OrderID[{orderId}]')
    return response.json()
