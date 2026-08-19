from flask import Blueprint, request, jsonify, g
from app.extensions import db
from app.models import Withdrawal, Transaction
from app.utils.decorators import login_required, agreed_required, head_required
from app.utils.validators import is_valid_kenyan_phone
from app.Services.capital import subtract_deposit
from app.Services.mpesa import send_money
from datetime import datetime

withdrawals_bp = Blueprint('withdrawals', __name__, url_prefix='/api/withdrawals')

@withdrawals_bp.route('/', methods=['POST'])
@login_required
@agreed_required
def request_withdrawal():
    data = request.get_json()
    required = ['amount', 'method', 'mpesa_number']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing fields'}), 400
    if not is_valid_kenyan_phone(data['mpesa_number']):
        return jsonify({'error': 'Invalid M-Pesa number'}), 400
    try:
        amount = float(data['amount'])
    except ValueError:
        return jsonify({'error': 'Invalid amount'}), 400
    if amount <= 0:
        return jsonify({'error': 'Amount must be positive'}), 400

    withdrawal = Withdrawal(
        user_id=g.user.id,
        amount=amount,
        method=data['method'],
        mpesa_number=data['mpesa_number'],
        status='pending'
    )
    db.session.add(withdrawal)
    db.session.commit()

    if g.user.role == 'head':
        withdrawal.status = 'approved'
        withdrawal.approved_by = g.user.id
        withdrawal.approved_at = datetime.utcnow()
        success = send_money(withdrawal.mpesa_number, float(withdrawal.amount), f"Withdrawal {withdrawal.id}")
        if success:
            subtract_deposit(g.user.id, withdrawal.amount, reference=f"withdrawal_{withdrawal.id}")
            tx = Transaction(
                user_id=g.user.id,
                type='withdrawal',
                amount=withdrawal.amount,
                reference=f"withdrawal_{withdrawal.id}",
                status='success',
                description=f"Withdrawal via {withdrawal.method}"
            )
            db.session.add(tx)
            withdrawal.status = 'completed'
            db.session.commit()
            return jsonify({'message': 'Withdrawal processed', 'withdrawal': withdrawal.to_dict()}), 200
        else:
            withdrawal.status = 'failed'
            db.session.commit()
            return jsonify({'error': 'Failed to send money via M-Pesa'}), 500
    else:
        return jsonify({'message': 'Withdrawal request submitted. Awaiting head approvals.', 'withdrawal': withdrawal.to_dict()}), 201

@withdrawals_bp.route('/', methods=['GET'])
@login_required
@agreed_required
def list_withdrawals():
    if g.user.role == 'head':
        withdrawals = Withdrawal.query.all()
    else:
        withdrawals = Withdrawal.query.filter_by(user_id=g.user.id).all()
    return jsonify([w.to_dict() for w in withdrawals]), 200

@withdrawals_bp.route('/<int:withdrawal_id>/approve', methods=['POST'])
@login_required
@head_required
@agreed_required
def approve_withdrawal(withdrawal_id):
    withdrawal = Withdrawal.query.get_or_404(withdrawal_id)
    if withdrawal.status != 'pending':
        return jsonify({'error': f'Withdrawal already {withdrawal.status}'}), 400
    approvers = withdrawal.approvers_ids.split(',') if withdrawal.approvers_ids else []
    if str(g.user.id) not in approvers:
        approvers.append(str(g.user.id))
        withdrawal.approvers_ids = ','.join(approvers)
        db.session.commit()
    if len(approvers) >= 2:
        withdrawal.status = 'approved'
        withdrawal.approved_by = g.user.id
        withdrawal.approved_at = datetime.utcnow()
        success = send_money(withdrawal.mpesa_number, float(withdrawal.amount), f"Withdrawal {withdrawal.id}")
        if success:
            subtract_deposit(withdrawal.user_id, withdrawal.amount, reference=f"withdrawal_{withdrawal.id}")
            tx = Transaction(
                user_id=withdrawal.user_id,
                type='withdrawal',
                amount=withdrawal.amount,
                reference=f"withdrawal_{withdrawal.id}",
                status='success',
                description=f"Withdrawal via {withdrawal.method}"
            )
            db.session.add(tx)
            withdrawal.status = 'completed'
            db.session.commit()
            return jsonify({'message': 'Withdrawal approved and processed'}), 200
        else:
            withdrawal.status = 'failed'
            db.session.commit()
            return jsonify({'error': 'M-Pesa sending failed'}), 500
    else:
        return jsonify({'message': f'Approval added. Need {2 - len(approvers)} more head(s).'}), 200

@withdrawals_bp.route('/<int:withdrawal_id>/reject', methods=['POST'])
@login_required
@head_required
@agreed_required
def reject_withdrawal(withdrawal_id):
    withdrawal = Withdrawal.query.get_or_404(withdrawal_id)
    if withdrawal.status != 'pending':
        return jsonify({'error': f'Withdrawal already {withdrawal.status}'}), 400
    withdrawal.status = 'rejected'
    db.session.commit()
    return jsonify({'message': 'Withdrawal rejected'}), 200