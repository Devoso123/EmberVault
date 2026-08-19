from flask import Blueprint, request, jsonify, g
from app.extensions import db
from app.models import Pledge
from app.utils.decorators import login_required, agreed_required
from app.Services.capital import add_deposit
from datetime import datetime

pledges_bp = Blueprint('pledges', __name__, url_prefix='/api/pledges')

@pledges_bp.route('/', methods=['POST'])
@login_required
@agreed_required
def create_pledge():
    data = request.get_json()
    if not all(k in data for k in ('amount', 'due_date')):
        return jsonify({'error': 'Amount and due_date required'}), 400
    try:
        amount = float(data['amount'])
        due_date = datetime.fromisoformat(data['due_date'])
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid amount or date format'}), 400
    if amount <= 0:
        return jsonify({'error': 'Amount must be positive'}), 400

    pledge = Pledge(
        user_id=g.user.id,
        amount=amount,
        description=data.get('description'),
        due_date=due_date,
        is_private=data.get('is_private', False)
    )
    db.session.add(pledge)
    db.session.commit()
    return jsonify({'message': 'Pledge created', 'pledge': pledge.to_dict(show_private=True)}), 201

@pledges_bp.route('/', methods=['GET'])
@login_required
@agreed_required
def list_pledges():
    user = g.user
    if user.role == 'head':
        pledges = Pledge.query.all()
    else:
        pledges = Pledge.query.filter((Pledge.is_private == False) | (Pledge.user_id == user.id)).all()
    pledges.sort(key=lambda p: p.due_date)
    show_private = (user.role == 'head')
    return jsonify([p.to_dict(show_private=show_private) for p in pledges]), 200

@pledges_bp.route('/<int:pledge_id>/pay', methods=['POST'])
@login_required
@agreed_required
def pay_pledge(pledge_id):
    pledge = Pledge.query.get_or_404(pledge_id)
    if pledge.user_id != g.user.id and g.user.role != 'head':
        return jsonify({'error': 'Not authorized'}), 403
    if pledge.is_paid:
        return jsonify({'error': 'Pledge already paid'}), 400
    pledge.is_paid = True
    pledge.paid_at = datetime.utcnow()
    add_deposit(pledge.user_id, pledge.amount, reference=f"pledge_{pledge.id}")
    db.session.commit()
    return jsonify({'message': 'Pledge paid and capital updated'}), 200

@pledges_bp.route('/<int:pledge_id>', methods=['DELETE'])
@login_required
@agreed_required
def delete_pledge(pledge_id):
    pledge = Pledge.query.get_or_404(pledge_id)
    if pledge.user_id != g.user.id and g.user.role != 'head':
        return jsonify({'error': 'Not authorized'}), 403
    if pledge.is_paid:
        return jsonify({'error': 'Cannot delete a paid pledge'}), 400
    db.session.delete(pledge)
    db.session.commit()
    return jsonify({'message': 'Pledge deleted'}), 200