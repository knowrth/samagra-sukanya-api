import bcrypt
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func, Enum, text 
from datetime import datetime
from .db import BaseModel, db
from sqlalchemy.dialects.postgresql import UUID

import uuid
# from .EpinModels import EPinModel

import pytz
import random
import string



class UserModel(BaseModel):
    __tablename__ = 'users'

    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(50))
    phone = db.Column(db.String(20), unique=True)
    amount_paid = db.Column(db.Numeric(precision=10, scale=2), nullable=False, default=0.00)
    paid_type = db.Column(db.String(50))
    paid_status = db.Column(db.String(50), default='UNPAID')
    email = db.Column(db.String(255), unique=True, nullable=True)
    role = db.Column(Enum('USER', 'ADMIN', name='user_role'), nullable=False)
    _password = db.Column('password', db.String(255)) 
    user_status = db.Column(Enum('ACTIVE', 'SUSPENDED', name='user_status'), nullable=True)
    # reg_status = db.Column(db.String(50))
    pin_type = db.Column(db.String(50))
    sponsor_id = db.Column(db.String(36))
    joining_date = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Asia/Kolkata')))
    # sponsored_epins = db.relationship('EPinModel', foreign_keys=[EPinModel.sponsor_id], backref='sponsor')
    # transactions = db.relationship('TransactionModel', backref='user', lazy=True)

    def __repr__(self):
        return f"UserModel(user_id={self.user_id})"

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, plain_text_password):
        self._password = bcrypt.hashpw(plain_text_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self._password.encode('utf-8'))
    
    def generate_username(self):
        prefix = "SSC" 
        suffix = ''.join(random.choices(string.digits, k=6))  
        username = prefix + suffix
        while UserModel.query.filter_by(username=username).first():  
            suffix = ''.join(random.choices(string.digits, k=6))  
            username = prefix + suffix
        return username



class UserTransaction(BaseModel):
    __tablename__ = 'user_transaction'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'))
    
    type = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Numeric(50), nullable=False)
    remark = db.Column(db.String(50))
    status = db.Column(db.String(36), nullable=True)
    date_time = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Asia/Kolkata')))
    sponsor_id = db.Column(db.String(50), nullable=True)

    

    def __init__(self, user_id, type, category, amount, remark, sponsor_id, date_time, status):
        self.user_id = user_id
        self.type = type
        self.category = category
        self.amount = amount
        self.remark = remark
        self.sponsor_id =sponsor_id
        self.status = status
        self.date_time = date_time


class UserDetails(BaseModel):
    __tablename__ = 'user_details'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'))

    image_url = db.Column(db.String(255))
    title = db.Column(db.String(10))
    # first_name = db.Column(db.String(50))
    # last_name = db.Column(db.String(50))
    gender = db.Column(db.String(10))
    dob = db.Column(db.Date)
    father_name = db.Column(db.String(100))
    # mobile_no = db.Column(db.String(15), db.ForeignKey('users.phone'))
    house_telephone = db.Column(db.String(15))
    email = db.Column(db.String(100))
    country = db.Column(db.String(50))
    state = db.Column(db.String(50))
    city = db.Column(db.String(50))
    pin_code = db.Column(db.String(10))
    address = db.Column(db.String(255))
    marital_status = db.Column(db.String(20))

    def __init__(self, user_id, image_url=None, title=None, 
                gender=None, dob=None, father_name=None, house_telephone=None,
                email=None, country=None, state=None, city=None, pin_code=None, address=None,
                marital_status=None):
        self.user_id = user_id
        self.image_url = image_url
        self.title = title
        self.gender = gender
        self.dob = dob
        self.father_name = father_name
        self.house_telephone = house_telephone
        self.email = email
        self.country = country
        self.state = state
        self.city = city
        self.pin_code = pin_code
        self.address = address
        self.marital_status = marital_status



class UserMap(BaseModel):
    __tablename__ = 'userMap'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'))

    path = db.Column(db.Text)
    sponsor_id = db.Column(db.String(36))


class UserBankDetails(BaseModel):
    __tablename__ = 'user_bank'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'))

    file_url = db.Column(db.String(255))
    ifsc_code = db.Column(db.String(36))
    bank_name = db.Column(db.String(64))
    branch_name = db.Column(db.String(64))
    account_number = db.Column(db.String(36))
    account_holder = db.Column(db.String(36))
    nominee_name = db.Column(db.String(50))
    nominee_relation = db.Column(db.String(50))
    nominee_dob = db.Column(db.Date)



# class UserAnalytics(db.Model):
#     __tablename__ = 'userAnalytics'

#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), primary_key=True, nullable=False)
#     direct_referrals = db.Column(db.Text)
#     indirect_referrals = db.Column(db.Text)