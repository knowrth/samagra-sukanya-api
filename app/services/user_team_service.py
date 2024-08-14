from models.db import db
from datetime import datetime, timedelta
import pytz
from sqlalchemy.sql import text
from sqlalchemy import  func
from models.UserModels import UserBankDetails, UserModel, UserTransaction
from models.EpinModels import RegisterEPin
from models.ReferencModels import SupportTicket
from typing import List
from flask import jsonify
from math import ceil


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

def income_transaction_user(user_id, page, per_page, from_date, to_date  ):

    with db.session() as session:
        offset = (page - 1) * per_page
        
        # Convert date strings to datetime objects
        from_date_dt = datetime.strptime(from_date, '%Y-%m-%d') if from_date else None
        to_date_dt = datetime.strptime(to_date, '%Y-%m-%d') if to_date else None

        # End of day for to_date
        end_of_day = (to_date_dt + timedelta(days=1) - timedelta(milliseconds=1)) if to_date_dt else None
        

        count_query = (
            db.select(func.count())
            .filter(RegisterEPin.user_id == user_id)
        )
        
        if from_date_dt:
            count_query = count_query.filter(RegisterEPin.date_time >= from_date_dt)
        if end_of_day:
            count_query = count_query.filter(RegisterEPin.date_time <= end_of_day)
        
        total_count = session.execute(count_query).scalar()

        # Base query for transactions
        query = (
            db.select(RegisterEPin)
            .filter(RegisterEPin.user_id == user_id)
        )
        
        # Add date filtering if provided
        if from_date_dt:
            query = query.filter(RegisterEPin.date_time >= from_date_dt)
        if end_of_day:
            query = query.filter(RegisterEPin.date_time <= end_of_day)
        
        # Get paginated transactions
        transactions_query = query.order_by(text('date_time desc')).limit(per_page).offset(offset)
        transactions = session.execute(transactions_query).scalars().all()

        # Calculate the total commission
        commission_query = (
            db.select(func.sum(RegisterEPin.commission))
            .filter(RegisterEPin.user_id == user_id)
        )
        
        if from_date_dt:
            commission_query = commission_query.filter(RegisterEPin.date_time >= from_date_dt)
        if end_of_day:
            commission_query = commission_query.filter(RegisterEPin.date_time <= end_of_day)
        
        total_commission = session.execute(commission_query).scalar()

        
        total_pages = ceil(total_count / per_page)


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

    return jsonify({'transactions': transactions_data, 'total_amount': total_commission, 'total_pages': total_pages,
                        'current_page': (offset // per_page) + 1,
                        'total_supports': total_count})

def create_support_ticket(user_id, query_type, query_title, query_desc):
    created_at = datetime.now(pytz.timezone('Asia/Kolkata'))
    with db.session() as session:
        new_ticket = SupportTicket(user_id=user_id, query_type=query_type, query_title=query_title, query_desc=query_desc, query_status="Open", date_time=created_at)
        session.add(new_ticket)
        session.commit()
    return jsonify({'message': 'Support ticket created successfully.'}), 200

def create_withdrawal_request(user_id, amount):
    with db.session() as session:
        created_at = datetime.now(pytz.timezone('Asia/Kolkata'))

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

def get_transactions_table(user_id, page, per_page, from_date, to_date  ):
    with db.session() as session:
        offset = (page - 1) * per_page
        
        query = (
            db.select(UserTransaction)
            .filter(UserTransaction.user_id == user_id)
        )
        
        # Add date filtering if provided
        if from_date:
            query = query.filter(UserTransaction.date_time >= datetime.strptime(from_date, '%Y-%m-%d'))
        if to_date:
            # Ensure to_date is inclusive by setting the end of the day
            end_of_day = datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1) - timedelta(milliseconds=1)
            query = query.filter(UserTransaction.date_time <= end_of_day)
        
        # Count total matching transactions
        count_stmt = (
            db.select(func.count())
            .select_from(UserTransaction)
            .filter(UserTransaction.user_id == user_id)
        )
        
        if from_date:
            count_stmt = count_stmt.filter(UserTransaction.date_time >= datetime.strptime(from_date, '%Y-%m-%d'))
        if to_date:
            count_stmt = count_stmt.filter(UserTransaction.date_time <= end_of_day)
        
        total_count = session.execute(count_stmt).scalar()
        
        # Fetch transactions with pagination
        transactions_query = query.order_by(text('date_time desc')).limit(per_page).offset(offset)
        transactions = session.execute(transactions_query).scalars().all()

        total_pages = ceil(total_count / per_page)

        #
        serialized_transactions = [{
            'user_id': transaction.user_id,
            'amount': transaction.amount,
            'type': transaction.type,
            'category': transaction.category,
            'remark': transaction.remark,
            'timestamp': transaction.date_time if transaction.date_time else None
        } for transaction in transactions]

        

        return jsonify({'transactions': serialized_transactions,
                        'total_pages': total_pages,
                        'current_page': (offset // per_page) + 1,
                        'total_supports': total_count})
    

def get_withdrawal_table(user_id, page, per_page, from_date, to_date ):
    with db.session() as session:
        offset = (page - 1) * per_page
        from_date_dt = datetime.strptime(from_date, '%Y-%m-%d') if from_date else None
        to_date_dt = datetime.strptime(to_date, '%Y-%m-%d') if to_date else None

        end_of_day = (to_date_dt + timedelta(days=1) - timedelta(milliseconds=1)) if to_date_dt else None
        
        stmt = db.Select(UserTransaction).filter_by(user_id=user_id, category="Withdrawals")
        
        if from_date_dt:
            stmt = stmt.filter(UserTransaction.date_time >= from_date_dt)
        if end_of_day:
            stmt = stmt.filter(UserTransaction.date_time <= end_of_day)
        
        stmt = stmt.order_by(UserTransaction.date_time.desc()).limit(per_page).offset(offset)
        
        result = session.execute(stmt)
        withdrawals = result.scalars().all()
        
        # Serialize the results
        serialized_withdrawals = [
            {
                'amount': withdrawal.amount, 
                'type': withdrawal.type,
                'status': withdrawal.status,
                'timestamp': withdrawal.date_time.strftime('%Y-%m-%d %H:%M:%S')
            } 
            for withdrawal in withdrawals
        ]

        count_stmt = (db.Select(func.count()).select_from(UserTransaction).filter_by(user_id=user_id, category="Withdrawals"))
        
        if from_date_dt:
            count_stmt = count_stmt.filter(UserTransaction.date_time >= from_date_dt)
        if end_of_day:
            count_stmt = count_stmt.filter(UserTransaction.date_time <= end_of_day)
        
        total_count_result = session.execute(count_stmt)
        total_count = total_count_result.scalar()
        total_pages = ceil(total_count / per_page)

    return jsonify({
        'withdrawals': serialized_withdrawals,
        'total_pages': total_pages,
        'current_page': (offset // per_page) + 1,
        'total_withdrawals': total_count
    })