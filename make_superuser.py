from app import create_app
from app.extensions import db
from app.models import User
from sqlalchemy import func

app = create_app()
with app.app_context():
    # Case‑insensitive search
    user = User.query.filter(func.lower(User.email) == func.lower('Sirdamienderrick@gmail.com')).first()
    if user:
        user.is_superuser = True
        db.session.commit()
        print(f"✅ {user.email} is now a superuser.")
    else:
        print("❌ User not found. Here are all registered emails:")
        all_users = User.query.all()
        for u in all_users:
            print(f"  - {u.email}")
        print("\nPlease sign up first, or correct the email in the script.")