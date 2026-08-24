from flask import Blueprint, request, jsonify, g
from app.extensions import db
from app.utils.decorators import login_required, agreed_required
from app.Services.mpesa import stk_push
from app.Services.capital import add_deposit
from app.Services.notifications import create_notification
from app.models import Transaction

deposit_bp = Blueprint('deposit', __name__, url_prefix='/api/deposit')

@deposit_bp.route('/', methods=['POST'])
@login_required
@agreed_required
def deposit():
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
    
    # Initiate STK Push
    phone = g.user.primary_phone
    result = stk_push(phone, amount, f"Deposit to Embervault")
    if result.get('success'):
        # Record transaction (pending until callback confirms)
        tx = Transaction(
            user_id=g.user.id,
            type='deposit',
            amount=amount,
            reference=result.get('checkout_request_id'),
            status='pending',
            description=f"Deposit by {g.user.name}"
        )
        db.session.add(tx)
        db.session.commit()
        
        # Notify user
        create_notification(
            g.user.id,
            "Deposit Initiated",
            f"Your deposit of KES {amount} has been initiated. You will receive a confirmation shortly."
        )
        
        return jsonify({
            'message': 'Deposit initiated. Please check your phone to complete the payment.',
            'transaction': tx.to_dict()
        }), 200
    else:
        return jsonify({'error': 'STK Push failed', 'details': result.get('message')}), 500