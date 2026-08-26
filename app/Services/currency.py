import requests
from flask import current_app
import json

def get_exchange_rates(base_currency='KES'):
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
        # Fallback to static rates (approximate)
        return {
            'base': base_currency,
            'rates': {
                'KES': 1.0,
                'USD': 0.0077,
                'EUR': 0.0071,
                'GBP': 0.0061,
                'JPY': 1.15,
                'UGX': 28.5,
                'TZS': 19.0,
                'RWF': 9.5
            },
            'date': 'static'
        }
    except Exception as e:
        current_app.logger.error(f"Currency API error: {e}")
        # Fallback
        return {
            'base': base_currency,
            'rates': {
                'KES': 1.0,
                'USD': 0.0077,
                'EUR': 0.0071,
                'GBP': 0.0061,
                'JPY': 1.15,
                'UGX': 28.5,
                'TZS': 19.0,
                'RWF': 9.5
            },
            'date': 'static'
        }

def convert_amount(amount, from_currency, to_currency):
    if from_currency == to_currency:
        return amount
    rates_data = get_exchange_rates(from_currency)
    rates = rates_data.get('rates', {})
    if to_currency in rates:
        return amount * rates[to_currency]
    return amount