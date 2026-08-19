from flask import Blueprint, request, jsonify, g
from app.extensions import db
from app.models import Notification
from app.utils.decorators import login_required

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@notifications_bp.route('/', methods=['GET'])
@login_required
def get_notifications():
    notifs = Notification.query.filter_by(user_id=g.user.id, is_read=False).order_by(Notification.created_at.desc()).all()
    return jsonify([n.to_dict() for n in notifs]), 200

@notifications_bp.route('/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_read(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != g.user.id:
        return jsonify({'error': 'Not authorized'}), 403
    notif.is_read = True
    db.session.commit()
    return jsonify({'message': 'Marked as read'}), 200

@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=g.user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'message': 'All notifications marked as read'}), 200

@notifications_bp.route('/count', methods=['GET'])
@login_required
def unread_count():
    count = Notification.query.filter_by(user_id=g.user.id, is_read=False).count()
    return jsonify({'count': count}), 200