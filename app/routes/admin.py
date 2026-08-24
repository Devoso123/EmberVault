from flask import Blueprint, request, jsonify, g
from app.extensions import db
from app.models import User, Pledge, Loan, Transaction, Withdrawal, AuditLog
from app.utils.decorators import login_required, superuser_required
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/users', methods=['GET'])
@login_required
@superuser_required
def list_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200

@admin_bp.route('/users/<int:user_id>/ban', methods=['POST'])
@login_required
@superuser_required
def ban_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_superuser:
        return jsonify({'error': 'Cannot ban superuser'}), 400
    user.is_banned = True
    db.session.commit()
    log = AuditLog(user_id=g.user.id, action='ban_user', details=f'Banned user {user.email}')
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': f'User {user.email} banned'}), 200

@admin_bp.route('/users/<int:user_id>/unban', methods=['POST'])
@login_required
@superuser_required
def unban_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_banned = False
    db.session.commit()
    log = AuditLog(user_id=g.user.id, action='unban_user', details=f'Unbanned user {user.email}')
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': f'User {user.email} unbanned'}), 200

@admin_bp.route('/users/<int:user_id>/make_moderator', methods=['POST'])
@login_required
@superuser_required
def make_moderator(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_superuser:
        return jsonify({'error': 'Superuser is already above moderator'}), 400
    user.is_moderator = True
    db.session.commit()
    log = AuditLog(user_id=g.user.id, action='make_moderator', details=f'Made {user.email} moderator')
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': f'{user.email} is now a moderator'}), 200

@admin_bp.route('/users/<int:user_id>/remove_moderator', methods=['POST'])
@login_required
@superuser_required
def remove_moderator(user_id):
    user = User.query.get_or_404(user_id)
    user.is_moderator = False
    db.session.commit()
    log = AuditLog(user_id=g.user.id, action='remove_moderator', details=f'Removed moderator from {user.email}')
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': f'{user.email} is no longer a moderator'}), 200

@admin_bp.route('/transactions', methods=['GET'])
@login_required
@superuser_required
def all_transactions():
    txs = Transaction.query.order_by(Transaction.created_at.desc()).all()
    return jsonify([tx.to_dict() for tx in txs]), 200

@admin_bp.route('/pledges', methods=['GET'])
@login_required
@superuser_required
def all_pledges():
    pledges = Pledge.query.order_by(Pledge.created_at.desc()).all()
    return jsonify([p.to_dict(show_private=True) for p in pledges]), 200

@admin_bp.route('/loans', methods=['GET'])
@login_required
@superuser_required
def all_loans():
    loans = Loan.query.order_by(Loan.created_at.desc()).all()
    return jsonify([l.to_dict() for l in loans]), 200

@admin_bp.route('/withdrawals', methods=['GET'])
@login_required
@superuser_required
def all_withdrawals():
    wds = Withdrawal.query.order_by(Withdrawal.created_at.desc()).all()
    return jsonify([w.to_dict() for w in wds]), 200

@admin_bp.route('/audit-logs', methods=['GET'])
@login_required
@superuser_required
def audit_logs():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(100).all()
    return jsonify([log.to_dict() for log in logs]), 200

@admin_bp.route('/users/<int:user_id>/make_head', methods=['POST'])
@login_required
@superuser_required
def make_head(user_id):
    user = User.query.get_or_404(user_id)
    user.role = 'head'
    db.session.commit()
    # Notify
    from app.Services.notifications import create_notification
    create_notification(user.id, "Promoted to Head", "You have been promoted to Head by the admin.")
    return jsonify({'message': f'{user.email} is now a head'}), 200