from flask import Blueprint, request, jsonify, g
from app.extensions import db
from app.models import AuditLog
from app.utils.decorators import login_required

support_bp = Blueprint('support', __name__, url_prefix='/api/support')

@support_bp.route('/contact', methods=['POST'])
@login_required
def contact_support():
    data = request.get_json()
    subject = data.get('subject')
    message = data.get('message')
    if not subject or not message:
        return jsonify({'error': 'Subject and message required'}), 400
    log = AuditLog(user_id=g.user.id, action='support_contact', details=f"{subject}: {message}")
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': 'Your message has been sent to support'}), 200