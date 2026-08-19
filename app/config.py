import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-me')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///embervault.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY')
    MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET')
    MPESA_PASSKEY = os.environ.get('MPESA_PASSKEY')
    MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE', '174379')
    MPESA_POCHI_NUMBER = os.environ.get('MPESA_POCHI_NUMBER', '0702634082')
    MPESA_CALLBACK_URL = os.environ.get('MPESA_CALLBACK_URL', 'https://your-ngrok-url.ngrok.io/mpesa/callback')

    JWT_EXPIRY_HOURS = 1
# Email (for notifications)
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')

# Security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'