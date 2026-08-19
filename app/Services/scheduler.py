from apscheduler.schedulers.background import BackgroundScheduler
from app.models import Pledge

def check_due_pledges():
    print("Checking due pledges...")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_due_pledges, 'interval', hours=1)
    scheduler.start()