from flask import Blueprint, request, jsonify, g
from app.extensions import db
from app.models import Message, User
from app.utils.decorators import login_required

messages_bp = Blueprint('messages', __name__, url_prefix='/api/messages')

@messages_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    data = request.get_json()
    recipient_id = data.get('recipient_id')
    body = data.get('body')
    if not recipient_id or not body:
        return jsonify({'error': 'Recipient and body required'}), 400
    recipient = User.query.get(recipient_id)
    if not recipient:
        return jsonify({'error': 'Recipient not found'}), 404
    msg = Message(sender_id=g.user.id, recipient_id=recipient.id, body=body)
    db.session.add(msg)
    db.session.commit()
    return jsonify({'message': 'Message sent', 'msg': msg.to_dict()}), 201

@messages_bp.route('/conversation/<int:user_id>', methods=['GET'])
@login_required
def get_conversation(user_id):
    msgs = Message.query.filter(
        ((Message.sender_id == g.user.id) & (Message.recipient_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.recipient_id == g.user.id))
    ).order_by(Message.created_at.asc()).all()
    return jsonify([m.to_dict() for m in msgs]), 200

@messages_bp.route('/unread', methods=['GET'])
@login_required
def unread_count():
    count = Message.query.filter_by(recipient_id=g.user.id, is_read=False).count()
    return jsonify({'count': count}), 200