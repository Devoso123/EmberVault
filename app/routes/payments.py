from flask import Blueprint, request, jsonify, g
from app.extensions import db
from app.models import Transaction
from app.utils.decorators import login_required, agreed_required
from app.Services.mpesa import stk_push
from app.utils.validators import is_valid_kenyan_phone

payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')

@payments_bp.route('/', methods=['POST'])
@login_required
@agreed_required
def make_payment():
    data = request.get_json()
    amount = data.get('amount')
    if not amount:
        return jsonify({'error': 'Amount required'}), 400
    try:
        amount = float(amount)
    except ValueError:
        return jsonify({'error': 'Invalid amount'}), 400
    if amount <= 0:
        return jsonify({'error': 'Amount must be positive'}), 400

    paybill = data.get('paybill')
    account = data.get('account_number')
    till = data.get('till_number')
    phone = data.get('phone_number')
    payee_name = data.get('payee_name')

    if not (paybill or till or phone):
        return jsonify({'error': 'At least one of paybill, till, or phone required'}), 400

    description = f"Payment to {payee_name or paybill or till or phone} - {account or ''}"
    result = stk_push(g.user.primary_phone, amount, description, paybill=paybill, till=till)
    if result.get('success'):
        tx = Transaction(
            user_id=g.user.id,
            type='payment',
            amount=amount,
            reference=result.get('checkout_request_id'),
            status='success',
            description=description,
            paybill=paybill,
            account_number=account,
            till_number=till,
            phone_number=phone,
            payee_name=payee_name
        )
        db.session.add(tx)
        db.session.commit()
        return jsonify({'message': 'Payment initiated successfully', 'transaction': tx.to_dict()}), 200
    else:
        return jsonify({'error': 'STK Push failed', 'details': result.get('message')}), 500