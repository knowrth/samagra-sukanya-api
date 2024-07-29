from sqlalchemy import func, PrimaryKeyConstraint, Enum, String
from datetime import datetime
from .db import db
import uuid
import random
import string
import pytz
from .UserModels import UserModel
from sqlalchemy.dialects.postgresql import UUID

import uuid

# class EPinModel(db.Model):
#     __tablename__ = 'epins'

#     id = db.Column(db.Integer, primary_key=True)
#     pin_type = db.Column(db.String(50), nullable=False)
#     transaction_type = db.Column(db.String(50), nullable=False)
#     transaction_note = db.Column(db.String(200))
#     user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
#     sponsor_id = db.Column(db.String(36), db.ForeignKey('users.user_id'))
#     package = db.Column(db.String(50))
#     transfer_date = db.Column(db.DateTime)
#     status = db.Column(db.Enum('ACTIVE', 'INACTIVE'), nullable=False, default='INACTIVE')
#     created_at = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Asia/Kolkata')))


#     def __init__(self, pin_type, transaction_type, transaction_note, user_id, sponsor_id, package):
#         self.pin_type = pin_type
#         self.transaction_type = transaction_type
#         self.transaction_note = transaction_note
#         self.user_id = user_id
#         self.sponsor_id = sponsor_id
#         self.package = package


class EPinTransaction(db.Model):
    __tablename__ = 'epin_transaction'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    epin_id = db.Column(String(36), nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.String(36))
    sponsor_id = db.Column(db.String(36))
    created_at = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Asia/Kolkata')))
    pin = db.Column(db.String(12))
    pin_type = db.Column(db.String(36))
    pin_amount = db.Column(db.Numeric(precision=10, scale=2))
    issued_to = db.Column(db.String(36))
    held_by = db.Column(db.String(36))
    used_by = db.Column(db.String(36))
    registered_to = db.Column(db.String(36))
    trans_date = db.Column(db.DateTime)
    reg_date = db.Column(db.DateTime)

    def __init__(self, transaction_type=None, user_id=None, sponsor_id=None, epin_id=None, created_at=None, pin=None, pin_type=None, pin_amount=None, issued_to=None, held_by=None, used_by=None, registered_to=None ):
        if epin_id is None:
            if transaction_type == "generate":
                self.epin_id = str(uuid.uuid4())
                self.pin = self.generate_pin()
            else:
                raise ValueError("ID must be provided for transactions other than 'generate'.")
        else:
            self.epin_id = epin_id
            self.pin = pin
        self.transaction_type = transaction_type
        self.user_id = user_id
        self.sponsor_id = sponsor_id
        self.created_at = created_at
        self.pin_type = pin_type
        self.pin_amount = pin_amount
        self.issued_to = issued_to
        self.held_by = held_by
        self.used_by = used_by
        self.registered_to = registered_to

    @staticmethod
    def generate_pin():
        left_part = ''.join(random.choices(string.digits, k=5))
        right_part = ''.join(random.choices(string.digits, k=5))
        pin = left_part + 'P' + right_part
        return pin

    def serialize(self):
        # issued_to = self.issued_to  # Default to user_id as issued_to
        # issued_to_name = UserModel.query.filter_by(user_id=issued_to).first().name
        # held_by = self.held_by  # Initialize held_by to None
        # held_by_name = UserModel.query.filter_by(user_id=held_by).first().name
        # used_by_name = UserModel.query.filter_by(user_id=self.used_by).first().name if self.transaction_type == 'registered' else None
        issued_to_name = None
        held_by_name = None
        used_by_name = None
        registered_to_name = None

        # Fetch issued_to_name
        if self.issued_to:
            user = UserModel.query.filter_by(user_id=self.issued_to).first()
            issued_to_name = user.name if user else None

        # Fetch held_by_name
        if self.held_by:
            user = UserModel.query.filter_by(user_id=self.held_by).first()
            held_by_name = user.name if user else None

        # Fetch used_by_name only for 'registered' transactions
        if self.transaction_type == 'registered' and self.used_by:
            user = UserModel.query.filter_by(user_id=self.used_by).first()
            used_by_name = user.name if user else None

        if self.transaction_type == 'registered' and self.registered_to:
            user = UserModel.query.filter_by(user_id=self.registered_to).first()
            registered_to_name = user.name if user else None

        # if self.transaction_type == "transfer":
        #     # For transfer transactions, issued_to should be the original owner who generated the pin
        #     issued_to = self.sponsor_id
        #     issued_to_name = UserModel.query.filter_by(user_id=issued_to).first().name
            
        #     # For transfer transactions, held_by should be the current owner who holds the pin after the transfer
        #     held_by = self.user_id
        #     held_by_name = UserModel.query.filter_by(user_id=held_by).first().name
        return {
            'id': self.id,
            'epin_id': self.epin_id,
            'transaction_type': self.transaction_type,
            'user_id': self.user_id,
            'sponsor_id': self.sponsor_id,
            'created_at': self.created_at,
            'pin': self.pin,
            'pin_amount' : self.pin_amount,
            'pin_type' : self.pin_type,
            'issued_to': issued_to_name,  # Assuming user_id is the field representing the user to which it is issued
            'held_by': held_by_name,  # Assuming sponsor_id is the field representing the latest user who has the epin
            'used_by': used_by_name,
            'registered_to': registered_to_name,
        }


class RegisterEPin(db.Model):
    __tablename__ = 'registered_epins'

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'))
    epin = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level = db.Column(db.String(50), nullable=False)
    commission = db.Column(db.Numeric(50), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    status = db.Column(Enum('ISSUED', 'REGISTERED', name='pin_status'), nullable=False)
    date_time = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Asia/Kolkata')))
    register_time = db.Column(db.DateTime, default=None)
    pre_wallet = db.Column(db.String(50), nullable=False)
    after_wallet = db.Column(db.String(50), nullable=False)
    member = db.Column(db.String(50), nullable=False)
    trans_type = db.Column(db.String(50), nullable=False)
    log_type = db.Column(db.String(50), nullable=False)
    trans_note = db.Column(db.String(255), nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'epin'),
    )

    def __init__(self, user_id, epin, level, commission, status, pre_wallet, after_wallet, member, trans_type, log_type, trans_note, phone=None, register_time=None):
        self.user_id = user_id
        self.epin = epin
        self.level = level
        self.commission = commission
        self.phone = phone
        self.status = status
        self.date_time = datetime.now(pytz.timezone('Asia/Kolkata'))
        self.register_time = register_time
        self.pre_wallet = pre_wallet
        self.after_wallet = after_wallet
        self.member = member
        self.trans_type = trans_type
        self.log_type = log_type
        self.trans_note = trans_note