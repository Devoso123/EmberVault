from app import create_app
from app.extensions import db
from app.models import User, Pledge, Loan, Transaction, GroupCapital, Withdrawal, AuditLog, PasswordResetToken

app = create_app()
with app.app_context():
    db.drop_all()
    db.create_all()
    print("✅ Database reset and all tables recreated.")