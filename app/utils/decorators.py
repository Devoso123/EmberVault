from functools import wraps
from flask import request, g, jsonify
from app.utils.security import decode_token
from app.models import User

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header missing'}), 401
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'error': 'Invalid authorization header'}), 401
        token = parts[1]
        user_id = decode_token(token)
        if not user_id:
            return jsonify({'error': 'Invalid or expired token'}), 401
        user = User.query.get(user_id)
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
        g.user = user
        return f(*args, **kwargs)
    return decorated

def head_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if g.user.role != 'head':
            return jsonify({'error': 'Only main heads can perform this action'}), 403
        return f(*args, **kwargs)
    return decorated

def agreed_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not g.user.agreed_to_policy:
            return jsonify({'error': 'You must accept the policies first'}), 403
        return f(*args, **kwargs)
    return decorated

def superuser_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not g.user.is_superuser:
            return jsonify({'error': 'Superuser privileges required'}), 403
        return f(*args, **kwargs)
    return decorated