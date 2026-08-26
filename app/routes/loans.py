from flask import Blueprint, request, jsonify, g
from app.extensions import db
from app.models import Loan, Transaction, GroupCapital, User
from app.utils.decorators import login_required, agreed_required, head_required
from app.utils.validators import is_valid_kenyan_phone
from app.Services.capital import subtract_deposit, add_deposit
from app.Services.mpesa import send_money, stk_push
from app.Services.notifications import create_notification, send_email_notification
from datetime import datetime

loans_bp = Blueprint('loans', __name__, url_prefix='/api/loans')

@loans_bp.route('/', methods=['POST'])
@login_required
@agreed_required
def request_loan():
    data = request.get_json()
    required = ['amount', 'purpose', 'mpesa_number']
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

    loan = Loan(
        borrower_id=g.user.id,
        amount=amount,
        purpose=data['purpose'],
        mpesa_number=data['mpesa_number'],
        status='pending'
    )
    db.session.add(loan)
    db.session.commit()

    # Notify all heads
    heads = User.query.filter_by(role='head').all()
    for head in heads:
        if head.id != g.user.id:
            create_notification(head.id, "New Loan Request", f"{g.user.name} requested a loan of KES {amount}. Purpose: {data['purpose']}")
            send_email_notification(head.email, "New Loan Request", f"{g.user.name} requested a loan of KES {amount}. Please review.")

    return jsonify({'message': 'Loan request submitted', 'loan': loan.to_dict()}), 201

@loans_bp.route('/', methods=['GET'])
@login_required
@agreed_required
def list_loans():
    if g.user.role == 'head':
        loans = Loan.query.all()
    else:
        loans = Loan.query.filter_by(borrower_id=g.user.id).all()
    return jsonify([l.to_dict() for l in loans]), 200

@loans_bp.route('/<int:loan_id>/approve', methods=['POST'])
@login_required
@head_required
@agreed_required
def approve_loan(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    if loan.status != 'pending':
        return jsonify({'error': f'Loan already {loan.status}'}), 400

    # Check group capital
    cap = GroupCapital.get_balance()
    if float(cap.balance) < float(loan.amount):
        return jsonify({'error': 'Insufficient group capital for this loan'}), 400

    approvers = loan.approvers_ids.split(',') if loan.approvers_ids else []
    if str(g.user.id) not in approvers:
        approvers.append(str(g.user.id))
        loan.approvers_ids = ','.join(approvers)
        db.session.commit()

    if len(approvers) >= 2:
        # Determine interest rate based on borrower role
        if loan.borrower.role == 'head':
            loan.interest_rate = 0.0
        else:
            loan.interest_rate = 5.0
        loan.total_due = float(loan.amount) * (1 + float(loan.interest_rate) / 100)
        loan.status = 'approved'
        loan.approved_by = g.user.id
        loan.approved_at = datetime.utcnow()
        success = send_money(loan.mpesa_number, float(loan.amount), f"Loan disbursement {loan.id}")
        if success:
            subtract_deposit(loan.borrower_id, loan.amount, reference=f"loan_{loan.id}")
            tx = Transaction(
                user_id=loan.borrower_id,
                type='loan_disbursement',
                amount=float(loan.amount),
                reference=f"loan_{loan.id}",
                status='success',
                description=f"Loan approved by heads"
            )
            db.session.add(tx)
            db.session.commit()

            # Notify borrower
            create_notification(loan.borrower_id, "Loan Approved", f"Your loan of KES {loan.amount} has been approved.")
            send_email_notification(loan.borrower.email, "Loan Approved", f"Your loan of KES {loan.amount} has been approved and disbursed.")

            return jsonify({'message': 'Loan approved and disbursed', 'loan': loan.to_dict()}), 200
        else:
            loan.status = 'pending'
            db.session.commit()
            return jsonify({'error': 'Failed to send money via M-Pesa'}), 500
    else:
        # Notify the borrower that one head has approved
        create_notification(loan.borrower_id, "Loan Approval Progress", f"One head has approved your loan. Need {2 - len(approvers)} more head(s).")
        return jsonify({'message': f'Approval added. Need {2 - len(approvers)} more head(s).', 'loan': loan.to_dict()}), 200

@loans_bp.route('/<int:loan_id>/reject', methods=['POST'])
@login_required
@head_required
@agreed_required
def reject_loan(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    if loan.status != 'pending':
        return jsonify({'error': f'Loan already {loan.status}'}), 400
    loan.status = 'rejected'
    db.session.commit()

    # Notify borrower
    create_notification(loan.borrower_id, "Loan Rejected", f"Your loan of KES {loan.amount} was rejected.")
    send_email_notification(loan.borrower.email, "Loan Rejected", f"Your loan of KES {loan.amount} was rejected.")

    return jsonify({'message': 'Loan rejected'}), 200

@loans_bp.route('/<int:loan_id>/repay', methods=['POST'])
@login_required
@agreed_required
def repay_loan(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    if loan.borrower_id != g.user.id and g.user.role != 'head':
        return jsonify({'error': 'Not authorized'}), 403
    if loan.status != 'approved':
        return jsonify({'error': 'Loan not approved or already repaid'}), 400

    days = (datetime.utcnow() - loan.approved_at).days if loan.approved_at else 0
    interest = float(loan.amount) * (float(loan.interest_rate) / 100) * (days / 30)
    total_due = float(loan.amount) + interest
    phone = g.user.primary_phone
    result = stk_push(phone, total_due, f"Loan repayment {loan.id}")
    if result.get('success'):
        loan.status = 'repaid'
        add_deposit(g.user.id, total_due, reference=f"loan_repay_{loan.id}")
        db.session.commit()

        # Notify heads
        heads = User.query.filter_by(role='head').all()
        for head in heads:
            if head.id != g.user.id:
                create_notification(head.id, "Loan Repaid", f"{g.user.name} repaid loan of KES {total_due}.")
        # Notify user
        create_notification(loan.borrower_id, "Loan Repaid", f"You have repaid your loan of KES {total_due}.")

        return jsonify({'message': 'Loan repaid successfully'}), 200
    else:
        return jsonify({'error': 'STK Push failed. Please try again.'}), 500