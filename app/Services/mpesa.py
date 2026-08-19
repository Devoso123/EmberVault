import requests
import base64
from datetime import datetime
from flask import current_app

def get_access_token():
    consumer_key = current_app.config['MPESA_CONSUMER_KEY']
    consumer_secret = current_app.config['MPESA_CONSUMER_SECRET']
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=(consumer_key, consumer_secret))
    if response.status_code == 200:
        return response.json().get('access_token')
    return None

def stk_push(phone_number, amount, description, paybill=None, till=None):
    if phone_number.startswith('0'):
        phone = '254' + phone_number[1:]
    elif phone_number.startswith('254'):
        phone = phone_number
    else:
        phone = '254' + phone_number
    if len(phone) != 12:
        raise ValueError("Invalid phone number format")

    access_token = get_access_token()
    if not access_token:
        return {'success': False, 'message': 'Failed to get access token'}

    shortcode = current_app.config['MPESA_SHORTCODE']
    passkey = current_app.config['MPESA_PASSKEY']
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(f"{shortcode}{passkey}{timestamp}".encode()).decode()

    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline" if paybill else "CustomerBuyGoodsOnline",
        "Amount": int(amount),
        "PartyA": phone,
        "PartyB": paybill or shortcode,
        "PhoneNumber": phone,
        "CallBackURL": current_app.config['MPESA_CALLBACK_URL'],
        "AccountReference": description[:12] if paybill else "Pmt",
        "TransactionDesc": description[:13]
    }
    if till:
        payload["PartyB"] = till
        payload["TransactionType"] = "CustomerBuyGoodsOnline"
    if paybill:
        payload["PartyB"] = paybill
        payload["TransactionType"] = "CustomerPayBillOnline"

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        result = response.json()
        if result.get('ResponseCode') == '0':
            return {'success': True, 'checkout_request_id': result.get('CheckoutRequestID')}
        else:
            return {'success': False, 'message': result.get('ResponseDescription')}
    else:
        return {'success': False, 'message': 'HTTP error'}

def send_money(phone_number, amount, reason):
    # Placeholder – implement B2C if needed
    return True