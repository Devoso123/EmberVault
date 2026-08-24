import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, redirect, url_for, flash, session
from app.config import Config
from app.extensions import db, migrate, bcrypt, limiter
from app.routes.auth import auth_bp
from app.routes.group import group_bp
from app.routes.pledges import pledges_bp
from app.routes.loans import loans_bp
from app.routes.payments import payments_bp
from app.routes.withdrawals import withdrawals_bp
from app.routes.settings import settings_bp
from app.routes.mpesa_callback import mpesa_cb_bp
from app.routes.admin import admin_bp
from app.routes.support import support_bp
from app.routes.notifications import notifications_bp   # NEW
from app.routes.deposits import deposit_bp                # NEW (after rename)
from app.routes.currency import currency_bp              # NEW
from app.Services.scheduler import start_scheduler
from app.models import User, PasswordResetToken
from app.utils.security import generate_token
from app.utils.validators import is_valid_kenyan_phone, is_valid_email
from sqlalchemy import func
from datetime import datetime, timedelta
import secrets
from flask_talisman import Talisman   # NEW

def create_app():
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates'))
    app.config.from_object(Config)
    
    Talisman(app, content_security_policy=None)   # Security headers
    
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    limiter.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(group_bp)
    app.register_blueprint(pledges_bp)
    app.register_blueprint(loans_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(withdrawals_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(mpesa_cb_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(support_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(deposit_bp)
    app.register_blueprint(currency_bp)

    if not app.config.get('TESTING'):
        start_scheduler()

    @app.route('/')
    def index():
        return redirect(url_for('dashboard_page') if 'token' in session else url_for('login_page'))

    @app.route('/login', methods=['GET'])
    def login_page():
        return render_template('login.html')

    @app.route('/login', methods=['POST'])
    def login():
        identifier = request.form.get('identifier')
        password = request.form.get('password')
        user = User.query.filter((User.primary_phone == identifier) | (func.lower(User.email) == func.lower(identifier))).first()
        if not user or not user.check_password(password):
            flash('Invalid credentials', 'error')
            return redirect(url_for('login_page'))
        if not user.is_active:
            flash('Account inactive. Contact support.', 'error')
            return redirect(url_for('login_page'))
        if user.is_banned:
            flash('Account banned. Contact support.', 'error')
            return redirect(url_for('login_page'))
        token = generate_token(user.id)
        session['token'] = token
        session['user_id'] = user.id
        return redirect(url_for('dashboard_page'))

    @app.route('/signup', methods=['GET'])
    def signup_page():
        return render_template('signup.html')

    @app.route('/signup', methods=['POST'])
    def signup():
        name = request.form.get('name')
        primary_phone = request.form.get('primary_phone')
        secondary_phone = request.form.get('secondary_phone')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        if not is_valid_kenyan_phone(primary_phone):
            flash('Invalid phone number', 'error')
            return redirect(url_for('signup_page'))
        if not is_valid_email(email):
            flash('Invalid email', 'error')
            return redirect(url_for('signup_page'))
        if User.query.filter((User.primary_phone == primary_phone) | (func.lower(User.email) == func.lower(email))).first():
            flash('Phone or email already registered', 'error')
            return redirect(url_for('signup_page'))
        user = User(name=name, primary_phone=primary_phone, secondary_phone=secondary_phone, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        token = generate_token(user.id)
        session['token'] = token
        session['user_id'] = user.id
        flash('Signup successful! Please accept the policies.', 'success')
        return redirect(url_for('dashboard_page'))

    @app.route('/dashboard')
    def dashboard_page():
        if 'token' not in session:
            return redirect(url_for('login_page'))
        user = User.query.get(session.get('user_id'))
        if not user or not user.is_active:
            session.clear()
            return redirect(url_for('login_page'))
        return render_template('dashboard.html', user=user, token=session.get('token'))

    @app.route('/pledges')
    def pledges_page():
        if 'token' not in session:
            return redirect(url_for('login_page'))
        user = User.query.get(session.get('user_id'))
        return render_template('pledges.html', user=user, token=session.get('token'))

    @app.route('/loans')
    def loans_page():
        if 'token' not in session:
            return redirect(url_for('login_page'))
        user = User.query.get(session.get('user_id'))
        return render_template('loans.html', user=user, token=session.get('token'))

    @app.route('/payments')
    def payments_page():
        if 'token' not in session:
            return redirect(url_for('login_page'))
        user = User.query.get(session.get('user_id'))
        return render_template('payments.html', user=user, token=session.get('token'))

    @app.route('/withdrawals')
    def withdrawals_page():
        if 'token' not in session:
            return redirect(url_for('login_page'))
        user = User.query.get(session.get('user_id'))
        return render_template('withdrawals.html', user=user, token=session.get('token'))

    @app.route('/profile')
    def profile_page():
        if 'token' not in session:
            return redirect(url_for('login_page'))
        user = User.query.get(session.get('user_id'))
        return render_template('profile.html', user=user, token=session.get('token'))

    @app.route('/admin')
    def admin_page():
        if 'token' not in session:
            return redirect(url_for('login_page'))
        user = User.query.get(session.get('user_id'))
        if not user.is_superuser:
            flash('You are not authorized to view this page.', 'error')
            return redirect(url_for('dashboard_page'))
        return render_template('admin.html', user=user, token=session.get('token'))

    @app.route('/support')
    def support_page():
        if 'token' not in session:
            return redirect(url_for('login_page'))
        user = User.query.get(session.get('user_id'))
        return render_template('support.html', user=user, token=session.get('token'))

    @app.route('/reset-password', methods=['GET'])
    def request_reset_page():
        return render_template('password_reset.html')

    @app.route('/reset-password', methods=['POST'])
    def request_reset():
        email = request.form.get('email')
        user = User.query.filter(func.lower(User.email) == func.lower(email)).first()
        if not user:
            flash('No user with that email.', 'error')
            return redirect(url_for('request_reset_page'))
        token = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(hours=1)
        reset = PasswordResetToken(user_id=user.id, token=token, expires_at=expires)
        db.session.add(reset)
        db.session.commit()
        print(f"🔑 Password reset link: http://localhost:5000/reset-password?token={token}")
        flash('Reset link sent (check console).', 'success')
        return redirect(url_for('login_page'))

    @app.route('/logout')
    def logout_page():
        session.clear()
        flash('Logged out.', 'info')
        return redirect(url_for('login_page'))

    with app.app_context():
        db.create_all()


    return app