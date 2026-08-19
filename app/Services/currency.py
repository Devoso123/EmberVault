import requests
from flask import current_app
import json

def get_exchange_rates(base_currency='KES'):
    """Fetch live exchange rates from exchangerate-api.com (free, no key needed)"""
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                'base': data.get('base'),
                'rates': data.get('rates', {}),
                'date': data.get('date')
            }
        return None
    except Exception as e:
        current_app.logger.error(f"Currency API error: {e}")
        return None

def convert_amount(amount, from_currency, to_currency):
    """Convert amount between currencies using live rates"""
    if from_currency == to_currency:
        return amount
    
    rates_data = get_exchange_rates(from_currency)
    if not rates_data:
        return amount  # fallback
    
    rates = rates_data.get('rates', {})
    if to_currency in rates:
        return amount * rates[to_currency]
    return amount  # fallback