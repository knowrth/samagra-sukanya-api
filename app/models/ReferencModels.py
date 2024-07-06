from .UserModels import UserModel, UserMap
from datetime import datetime, timedelta
from .db import db
from sqlalchemy.dialects.postgresql import UUID
import pytz


# class ReferralNetwork(db.Model):
#     __tablename__ = 'referral_network'

#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.String(36), nullable=False)
#     level1 = db.Column(db.String(36))
#     level2 = db.Column(db.String(36))
#     level3 = db.Column(db.String(36))
#     level4 = db.Column(db.String(36))
#     level5 = db.Column(db.String(36))
#     level6 = db.Column(db.String(36))
#     level7 = db.Column(db.String(36))
#     level8 = db.Column(db.String(36))
#     level9 = db.Column(db.Text)

# class TransactionModel(db.Model):
#     __tablename__ = 'transactions'

#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
#     amount = db.Column(db.String(50), nullable=False)
#     level = db.Column(db.String(50), nullable=False)
#     member = db.Column(db.String(50), nullable=False)
#     logType = db.Column(db.String(50), nullable=False)
#     pre_wallet_amount = db.Column(db.String(50), nullable=False)
#     after_wallet_amount = db.Column(db.String(50), nullable=False)
#     transaction_mode_type = db.Column(db.String(50), nullable=False)
#     transaction_note = db.Column(db.String(255), nullable=True)
#     timestamp = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Asia/Kolkata')))

#     def __init__(self, user_id, amount, level, member, logType, pre_wallet_amount, after_wallet_amount, transaction_mode_type, transaction_note):
#         self.user_id = user_id
#         self.amount = amount
#         self.level = level
#         self.member = member
#         self.logType = logType
#         self.pre_wallet_amount = pre_wallet_amount
#         self.after_wallet_amount = after_wallet_amount
#         self.transaction_mode_type = transaction_mode_type
#         self.transaction_note = transaction_note



class ResetTokenModel(db.Model):
    __tablename__ = 'reset_tokens'

    token = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'))
    email = db.Column(db.String(120), nullable=False)
    valid_till = db.Column(db.DateTime, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)

    def __init__(self, user_id, email, token):
        self.user_id = user_id
        self.email = email
        self.token = token
        self.valid_till = datetime.now(pytz.timezone('Asia/Kolkata')) + timedelta(minutes=15)


class IncomeLevel(db.Model):
    __tablename__ = 'income_level'

    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(36))
    rate = db.Column(db.Integer)

class SupportTicket(db.Model):
    __tablename__ = 'support'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'))
    query_type = db.Column(db.String(50))
    query_title = db.Column(db.String(50))
    query_desc = db.Column(db.String(255))
    query_status = db.Column(db.String(50))
    resolved_issue = db.Column(db.String(50))
    date_time = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Asia/Kolkata')))


income_levels = [
    {'level': 'Level-1', 'rate': 25},
    {'level': 'Level-2', 'rate': 15},
    {'level': 'Level-3', 'rate': 10},
    {'level': 'Level-4', 'rate': 7},
    {'level': 'Level-5', 'rate': 6},
    {'level': 'Level-6', 'rate': 5},
    {'level': 'Level-7', 'rate': 4},
    {'level': 'Level-8', 'rate': 3},
    {'level': 'Level-9', 'rate': 2}
]

def insert_income_levels():
    for income_level in income_levels:
        existing_income_level = IncomeLevel.query.filter_by(level=income_level['level']).first()
        if existing_income_level is None:
            new_income_level = IncomeLevel(level=income_level['level'], rate=income_level['rate'])
            db.session.add(new_income_level)
    db.session.commit()


def create_initial_admin():
    admin_user = UserModel.query.filter_by(role='ADMIN').first()
    if not admin_user:
        admin = UserModel(username='admin', email='d4066445@gmail.com', role='ADMIN')
        admin.password = 'admin1234'
        admin.user_status = 'ACTIVE'
        admin.name = 'ADMIN'
        admin.phone = '1234567890'
        db.session.add(admin)
        db.session.commit()


def create_initial_user():
    admin_user = UserModel.query.filter_by(role='USER').first()
    if not admin_user:
        user = UserModel(username='SSC455332', email='d40664452@gmail.com', role='USER')
        user.password = 'user1234'
        user.user_status = 'ACTIVE'
        user.name = 'DEFAULT'
        user.phone = '9876543210'
        user.amount_paid = '2000'
        user.paid_status = 'PAID'
        db.session.add(user)
        db.session.commit()

        user_id = user.user_id

        new_path = UserMap(user_id=user_id )
        db.session.add(new_path)
        db.session.commit()

        # new_analytics = UserAnalytics(user_id=user_id)
        # db.session.add(new_analytics)
        # db.session.commit()