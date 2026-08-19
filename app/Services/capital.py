from app.extensions import db
from app.models import GroupCapital, Transaction

def add_deposit(user_id, amount, reference=None, description=None):
    cap = GroupCapital.get_balance()
    cap.balance += amount
    tx = Transaction(
        user_id=user_id,
        type='deposit',
        amount=amount,
        reference=reference,
        status='success',
        description=description or 'Deposit to group capital'
    )
    db.session.add(tx)
    db.session.commit()
    return cap.balance

def subtract_deposit(user_id, amount, reference=None, description=None):
    cap = GroupCapital.get_balance()
    if cap.balance < amount:
        raise ValueError("Insufficient funds")
    cap.balance -= amount
    tx = Transaction(
        user_id=user_id,
        type='withdrawal',
        amount=amount,
        reference=reference,
        status='success',
        description=description or 'Withdrawal from group capital'
    )
    db.session.add(tx)
    db.session.commit()
    return cap.balance