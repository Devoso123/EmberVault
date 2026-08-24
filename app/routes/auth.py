from flask import Blueprint, request, jsonify, g
from app.extensions import db, limiter
from app.models import User, Pledge, Loan, PasswordResetToken
from app.utils.security import generate_token
from app.utils.validators import is_valid_kenyan_phone, is_valid_email
from app.utils.decorators import login_required
from sqlalchemy import func
from datetime import datetime, timedelta
import secrets

auth_bp = Blueprint('auth', __name__, url_prefix='/api')

@auth_bp.route('/signup', methods=['POST'])
@limiter.limit("5 per minute")
def signup():
    data = request.get_json()
    required = ['name', 'primary_phone', 'email', 'password', 'role']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400
    if not is_valid_kenyan_phone(data['primary_phone']):
        return jsonify({'error': 'Invalid primary phone number'}), 400
    if data.get('secondary_phone') and not is_valid_kenyan_phone(data['secondary_phone']):
        return jsonify({'error': 'Invalid secondary phone number'}), 400
    if not is_valid_email(data['email']):
        return jsonify({'error': 'Invalid email address'}), 400
    if User.query.filter((User.primary_phone == data['primary_phone']) | (func.lower(User.email) == func.lower(data['email']))).first():
        return jsonify({'error': 'Phone or email already registered'}), 400
        # Make the first user a superuser automatically
    if User.query.count() == 1:
        user.is_superuser = True
    user = User(
        name=data['name'],
        primary_phone=data['primary_phone'],
        secondary_phone=data.get('secondary_phone'),
        email=data['email'],
        role=data['role'],
        profile_pic=data.get('profile_pic'),
        agreed_to_policy=False
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    token = generate_token(user.id)
    return jsonify({
        'message': 'Signup successful. Please accept policies to continue.',
        'token': token,
        'user': user.to_dict()
    }), 201

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    data = request.get_json()
    identifier = data.get('identifier')
    password = data.get('password')
    if not identifier or not password:
        return jsonify({'error': 'Identifier and password required'}), 400
    user = User.query.filter((User.primary_phone == identifier) | (func.lower(User.email) == func.lower(identifier))).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401
    if not user.is_active:
        return jsonify({'error': 'Account inactive. Contact support.'}), 401
    if user.is_banned:
        return jsonify({'error': 'Account banned. Contact support.'}), 401
    token = generate_token(user.id)
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': user.to_dict()
    }), 200

@auth_bp.route('/agreement', methods=['POST'])
@login_required
def agreement():
    data = request.get_json()
    accepted = data.get('accepted', False)
    user = g.user
    if accepted:
        user.agreed_to_policy = True
        db.session.commit()
        return jsonify({'message': 'Agreement accepted. Welcome to Embervault.'}), 200
    else:
        return jsonify({'message': 'You declined the policies. Please contact support if you change your mind.'}), 403

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_profile():
    return jsonify(g.user.to_dict()), 200

@auth_bp.route('/me', methods=['PUT'])
@login_required
def update_profile():
    data = request.get_json()
    user = g.user
    if 'name' in data:
        user.name = data['name']
    if 'secondary_phone' in data:
        if data['secondary_phone'] and not is_valid_kenyan_phone(data['secondary_phone']):
            return jsonify({'error': 'Invalid secondary phone'}), 400
        user.secondary_phone = data['secondary_phone']
    if 'profile_pic' in data:
        user.profile_pic = data['profile_pic']
    if 'theme_preference' in data:
        user.theme_preference = data['theme_preference']
    db.session.commit()
    return jsonify({'message': 'Profile updated', 'user': user.to_dict()}), 200

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    return jsonify({'message': 'Logged out successfully'}), 200

@auth_bp.route('/account/delete', methods=['DELETE'])
@login_required
def delete_account():
    user = g.user
    unpaid_pledges = Pledge.query.filter_by(user_id=user.id, is_paid=False).first()
    if unpaid_pledges:
        return jsonify({'error': 'You have outstanding pledges. Clear them before deleting.'}), 400
    unpaid_loan = Loan.query.filter_by(borrower_id=user.id).filter(Loan.status.in_(['pending', 'approved'])).first()
    if unpaid_loan:
        return jsonify({'error': 'You have unpaid loans. Settle them before deleting.'}), 400
    user.is_active = False
    db.session.commit()
    return jsonify({'message': 'Account deleted (deactivated)'}), 200

@auth_bp.route('/request-reset', methods=['POST'])
def request_password_reset():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({'error': 'Email required'}), 400
    user = User.query.filter(func.lower(User.email) == func.lower(email)).first()
    if not user:
        return jsonify({'error': 'No user with that email'}), 404
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(hours=1)
    reset = PasswordResetToken(user_id=user.id, token=token, expires_at=expires)
    db.session.add(reset)
    db.session.commit()
    print(f"🔑 Password reset link: http://localhost:5000/reset-password?token={token}")
    return jsonify({'message': 'Reset link sent (check console)'}), 200

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')
    if not token or not new_password:
        return jsonify({'error': 'Token and new password required'}), 400
    reset = PasswordResetToken.query.filter_by(token=token, used=False).first()
    if not reset or reset.expires_at < datetime.utcnow():
        return jsonify({'error': 'Invalid or expired token'}), 400
    user = User.query.get(reset.user_id)
    user.set_password(new_password)
    reset.used = True
    db.session.commit()
    return jsonify({'message': 'Password reset successful'}), 200

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json()
    new_password = data.get('new_password')
    if not new_password:
        return jsonify({'error': 'New password required'}), 400
    user = g.user
    user.set_password(new_password)
    db.session.commit()
    return jsonify({'message': 'Password changed successfully'}), 200