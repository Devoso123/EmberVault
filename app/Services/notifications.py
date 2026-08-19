from app.extensions import db
from app.models import Notification
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
import logging

def create_notification(user_id, title, message, link=None):
    notif = Notification(user_id=user_id, title=title, message=message, link=link)
    db.session.add(notif)
    db.session.commit()
    return notif

def send_email_notification(recipient_email, subject, body):
    try:
        sender = current_app.config.get('EMAIL_USER')
        password = current_app.config.get('EMAIL_PASSWORD')
        if not sender or not password:
            logging.warning("Email not configured.")
            return False
        
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        logging.error(f"Email failed: {e}")
        return False