from flask import Blueprint, jsonify, request, g
from app.utils.decorators import login_required
from app.Services.currency import get_exchange_rates, convert_amount
from app.models import User
from app.extensions import db

currency_bp = Blueprint('currency', __name__, url_prefix='/api/currency')

@currency_bp.route('/rates', methods=['GET'])
@login_required
def rates():
    base = request.args.get('base', 'KES')
    data = get_exchange_rates(base)
    if data:
        return jsonify(data), 200
    return jsonify({'error': 'Failed to fetch exchange rates'}), 500

@currency_bp.route('/convert', methods=['POST'])
@login_required
def convert():
    data = request.get_json()
    amount = data.get('amount')
    from_curr = data.get('from', 'KES')
    to_curr = data.get('to', 'USD')
    
    if not amount:
        return jsonify({'error': 'Amount required'}), 400
    
    try:
        amount = float(amount)
    except ValueError:
        return jsonify({'error': 'Invalid amount'}), 400
    
    result = convert_amount(amount, from_curr, to_curr)
    return jsonify({
        'amount': amount,
        'from': from_curr,
        'to': to_curr,
        'result': result
    }), 200

@currency_bp.route('/preference', methods=['PUT'])
@login_required
def set_preference():
    data = request.get_json()
    currency = data.get('currency')
    if not currency:
        return jsonify({'error': 'Currency required'}), 400
    
    g.user.currency_preference = currency.upper()
    db.session.commit()
    return jsonify({'message': f'Currency preference set to {currency}'}), 200