from app.extensions import db, bcrypt
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    primary_phone = db.Column(db.String(20), unique=True, nullable=False)
    secondary_phone = db.Column(db.String(20))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='member')
    profile_pic = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    is_banned = db.Column(db.Boolean, default=False)
    is_moderator = db.Column(db.Boolean, default=False)
    is_superuser = db.Column(db.Boolean, default=False)
    agreed_to_policy = db.Column(db.Boolean, default=False)
    theme_preference = db.Column(db.String(50), default='light')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    currency_preference = db.Column(db.String(10), default='KES')

    pledges = db.relationship('Pledge', backref='user', lazy=True)
    loans_taken = db.relationship('Loan', foreign_keys='Loan.borrower_id', backref='borrower', lazy=True)
    loans_approved = db.relationship('Loan', foreign_keys='Loan.approved_by', backref='approver', lazy=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'currency_preference': self.currency_preference,
            'id': self.id,
            'name': self.name,
            'primary_phone': self.primary_phone,
            'secondary_phone': self.secondary_phone,
            'email': self.email,
            'role': self.role,
            'profile_pic': self.profile_pic,
            'agreed_to_policy': self.agreed_to_policy,
            'theme_preference': self.theme_preference,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'is_banned': self.is_banned,
            'is_moderator': self.is_moderator,
            'is_superuser': self.is_superuser
            
        }

class Pledge(db.Model):
    __tablename__ = 'pledges'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Numeric(10,2), nullable=False)
    description = db.Column(db.String(200))
    due_date = db.Column(db.DateTime, nullable=False)
    is_private = db.Column(db.Boolean, default=False)
    is_paid = db.Column(db.Boolean, default=False)
    paid_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self, show_private=False):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'amount': float(self.amount),
            'description': self.description,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'is_private': self.is_private if show_private else None,
            'is_paid': self.is_paid,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Loan(db.Model):
    __tablename__ = 'loans'
    id = db.Column(db.Integer, primary_key=True)
    borrower_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Numeric(10,2), nullable=False)
    purpose = db.Column(db.Text, nullable=False)
    mpesa_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    repayment_due = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approvers_ids = db.Column(db.String(200), default='')
    interest_rate = db.Column(db.Numeric(5,2), default=0.0)
    total_due = db.Column(db.Numeric(10,2))

    def to_dict(self):
        return {
            'id': self.id,
            'borrower_id': self.borrower_id,
            'borrower_name': self.borrower.name if self.borrower else None,
            'amount': float(self.amount),
            'purpose': self.purpose,
            'mpesa_number': self.mpesa_number,
            'status': self.status,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'repayment_due': self.repayment_due.isoformat() if self.repayment_due else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'approvers_ids': self.approvers_ids.split(',') if self.approvers_ids else [],
            'interest_rate': float(self.interest_rate),
            'total_due': float(self.total_due) if self.total_due else None
        }

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(30), nullable=False)
    amount = db.Column(db.Numeric(10,2), nullable=False)
    reference = db.Column(db.String(100), unique=True)
    status = db.Column(db.String(20), default='pending')
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paybill = db.Column(db.String(20))
    account_number = db.Column(db.String(50))
    till_number = db.Column(db.String(20))
    phone_number = db.Column(db.String(20))
    payee_name = db.Column(db.String(100))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'type': self.type,
            'amount': float(self.amount),
            'reference': self.reference,
            'status': self.status,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'paybill': self.paybill,
            'account_number': self.account_number,
            'till_number': self.till_number,
            'phone_number': self.phone_number,
            'payee_name': self.payee_name
        }

class GroupCapital(db.Model):
    __tablename__ = 'group_capital'
    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Numeric(10,2), default=0.00)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    @classmethod
    def get_balance(cls):
        cap = cls.query.first()
        if not cap:
            cap = cls(balance=0.0)
            db.session.add(cap)
            db.session.commit()
        return cap

    @classmethod
    def add_to_balance(cls, amount):
        cap = cls.get_balance()
        cap.balance = db.cast(cap.balance + amount, db.Numeric(10,2))
        db.session.commit()
        return cap.balance

    @classmethod
    def subtract_from_balance(cls, amount):
        cap = cls.get_balance()
        if cap.balance < amount:
            raise ValueError("Insufficient group capital")
        cap.balance = db.cast(cap.balance - amount, db.Numeric(10,2))
        db.session.commit()
        return cap.balance

class Withdrawal(db.Model):
    __tablename__ = 'withdrawals'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Numeric(10,2), nullable=False)
    method = db.Column(db.String(20), nullable=False)
    mpesa_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')
    approvers_ids = db.Column(db.String(200), default='')
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'amount': float(self.amount),
            'method': self.method,
            'mpesa_number': self.mpesa_number,
            'status': self.status,
            'approvers_ids': self.approvers_ids.split(',') if self.approvers_ids else [],
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'action': self.action,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(200))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'title': self.title,
            'message': self.message,
            'link': self.link,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }



class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id])
    recipient = db.relationship('User', foreign_keys=[recipient_id])

    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'sender_name': self.sender.name if self.sender else None,
            'recipient_id': self.recipient_id,
            'recipient_name': self.recipient.name if self.recipient else None,
            'body': self.body,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }