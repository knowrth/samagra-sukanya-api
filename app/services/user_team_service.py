from models.db import db
import datetime
import pytz
from sqlalchemy.sql import text
from sqlalchemy import  func
from models.UserModels import UserBankDetails, UserModel, UserTransaction
from models.EpinModels import RegisterEPin
from models.ReferencModels import SupportTicket
from typing import List
from flask import jsonify


def get_transaction_summary(user_id):
    with db.session() as session:
        stmt = db.Select(
                RegisterEPin.level,
                func.count().label('count'),
            ).filter(RegisterEPin.user_id == user_id).group_by(RegisterEPin.level)

        # Fetch all results
        query_result = session.execute(stmt).fetchall()

        summary = [
            {
                'level': row[0],
                'count': int(row[1])
            }
            for row in query_result
        ]

    return jsonify(summary)

def income_transaction_user(user_id):

    with db.session() as session:
        # Fetch transactions ordered by date_time in descending order
        stmt = (
            db.Select(RegisterEPin)
            .filter_by(user_id=user_id)
            .order_by(text('date_time desc'))
        )
        transactions = session.execute(stmt).scalars().all()

        # Calculate the total commission for the user
        stmt = (
            db.Select(func.sum(RegisterEPin.commission))
            .filter_by(user_id=user_id)
        )
        total_transaction = session.execute(stmt).scalar()

        transactions_data = [
                {
                    'user_id': transaction.user_id,
                    'amount': transaction.commission,
                    'level': transaction.level,
                    'member': transaction.member,
                    'logType': transaction.log_type,
                    'pre_wallet_amount': transaction.pre_wallet,
                    'after_wallet_amount': transaction.after_wallet,
                    'transaction_mode_type': transaction.trans_type,
                    'transaction_note': transaction.trans_note,
                    'timestamp': transaction.date_time if transaction.date_time else None
                }
                for transaction in transactions
            ]

    return jsonify({'transactions': transactions_data, 'total_amount': total_transaction})

def create_support_ticket(user_id, query_type, query_title, query_desc):
    created_at = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
    with db.session() as session:
        new_ticket = SupportTicket(user_id=user_id, query_type=query_type, query_title=query_title, query_desc=query_desc, query_status="Open", date_time=created_at)
        session.add(new_ticket)
        session.commit()
    return jsonify({'message': 'Support ticket created successfully.'}), 200

def create_withdrawal_request(user_id, amount):
    with db.session() as session:
        created_at = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))

        #check bank details
        stmt = db.Select(UserBankDetails).filter_by(user_id=user_id)
        bank_details = session.execute(stmt).scalars().first()
        if bank_details is None:
            return jsonify({'message': 'User bank details (bank name or IFSC code) are missing. Please update bank details.'}), 400
        
        # fetch user
        stmt = db.Select(UserModel).filter_by(user_id=user_id)
        user = session.execute(stmt).scalars().first()

        withdrawal_request = UserTransaction(
            user_id=user_id,
            amount=amount,
            remark=f"Request from {user.name} amount {amount}",
            status='Pending',  
            category='Withdrawals',
            date_time=created_at,
            sponsor_id= None,
            type='Debit'
        )
        session.add(withdrawal_request)
        session.commit()

    return jsonify({'message': 'Withdrawal successful'})