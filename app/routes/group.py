from flask import Blueprint, jsonify, g
from app.models import GroupCapital, User, Transaction
from app.utils.decorators import login_required, agreed_required
from datetime import datetime, date

group_bp = Blueprint('group', __name__, url_prefix='/api/group')

@group_bp.route('/capital', methods=['GET'])
@login_required
@agreed_required
def get_capital():
    cap = GroupCapital.get_balance()
    return jsonify({'balance': float(cap.balance), 'updated_at': cap.updated_at.isoformat() if cap.updated_at else None}), 200

@group_bp.route('/members', methods=['GET'])
@login_required
@agreed_required
def get_members():
    users = User.query.filter_by(is_active=True).all()
    return jsonify([u.to_dict() for u in users]), 200

@group_bp.route('/transactions/today', methods=['GET'])
@login_required
@agreed_required
def today_transactions():
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_end = datetime.combine(date.today(), datetime.max.time())
    txs = Transaction.query.filter(Transaction.created_at.between(today_start, today_end)).order_by(Transaction.created_at.desc()).all()
    return jsonify([tx.to_dict() for tx in txs]), 200