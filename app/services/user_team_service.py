from models.db import db
from datetime import datetime, timedelta
import pytz
from sqlalchemy.sql import text
from sqlalchemy import  func, cast, Integer
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

        transactions = [
            {"lvl": 1, "condition": 20, "reward": 400},
            {"lvl": 2, "condition": 200, "reward": 4000},
            {"lvl": 3, "condition": 2000, "reward": 40000},
            {"lvl": 4, "condition": 20000, "reward": 200000},
            {"lvl": 5, "condition": 200000, "reward": 2000000},
            {"lvl": 6, "condition": 2000000, "reward": 4000000},
            {"lvl": 7, "condition": 20000000, "reward": 40000000},
            {"lvl": 8, "condition": 200000000, "reward": 200000000},
            {"lvl": 9, "condition": 1000000000, "reward": 500000000},
        ]

        created_at = datetime.now(pytz.timezone('Asia/Kolkata'))

        for transaction in transactions:
            # print(f"Processing Level: {transaction['lvl']}") 

            for row in query_result:
                level_number = int(row[0].split('-')[1]) if isinstance(row[0], str) and '-' in row[0] else int(row[0])
                # print(f"Extracted Level Number: {level_number} from {row[0]}") 
                # print(f"Comparing Level {level_number} with {transaction['lvl']}")  

                if level_number == transaction['lvl'] and row[1] >= transaction['condition']:
                    # print(f"Condition met for level {level_number}: {row[1]} >= {transaction['condition']}")  # Log when the condition is met

                    existing_transaction = session.execute(
                        db.Select(UserTransaction)
                        .filter(
                            UserTransaction.user_id == user_id,
                            UserTransaction.category == "Reward",
                            UserTransaction.remark == f"Reward Income of {transaction['condition']} ID"
                        )
                    ).scalars().first()

                    if existing_transaction:
                        print(f"Reward already granted for Level {transaction['lvl']}")  
                    else:
                        # Create a commission record for the user
                        commission = UserTransaction(
                            user_id=user_id,
                            type='Receipt',
                            category='Reward',
                            amount=str(transaction['reward']),
                            remark=f"Reward Income of {transaction['condition']} ID",
                            date_time=created_at,
                            sponsor_id=None,
                            status=None
                        )
                        # print(f"Adding reward for Level {transaction['lvl']} with {transaction['reward']} cash")  # Log the reward being added
                        session.add(commission)
                        break  

        session.commit()
        summary = [
            {
                'level': row[0],
                'count': int(row[1])
            }
            for row in query_result
        ]

    return jsonify(summary)


def reward_transaction_user(user_id, page, per_page, from_date, to_date  ):

    with db.session() as session:
        offset = (page - 1) * per_page
        
        # Convert date strings to datetime objects
        from_date_dt = datetime.strptime(from_date, '%Y-%m-%d') if from_date else None
        to_date_dt = datetime.strptime(to_date, '%Y-%m-%d') if to_date else None

        # End of day for to_date
        end_of_day = (to_date_dt + timedelta(days=1) - timedelta(milliseconds=1)) if to_date_dt else None
        

        count_query = (
            db.select(func.count())
            .filter(UserTransaction.user_id == user_id,
                    UserTransaction.category == "Reward")
        )
        
        if from_date_dt:
            count_query = count_query.filter(UserTransaction.date_time >= from_date_dt)
        if end_of_day:
            count_query = count_query.filter(UserTransaction.date_time <= end_of_day)
        
        total_count = session.execute(count_query).scalar()

        # Base query for transactions
        query = (
            db.select(UserTransaction)
            .filter(UserTransaction.user_id == user_id,
                    UserTransaction.category == "Reward")
        )
        
        # Add date filtering if provided
        if from_date_dt:
            query = query.filter(UserTransaction.date_time >= from_date_dt)
        if end_of_day:
            query = query.filter(UserTransaction.date_time <= end_of_day)
        
        # Get paginated transactions
        transactions_query = query.order_by(text('date_time desc')).limit(per_page).offset(offset)
        transactions = session.execute(transactions_query).scalars().all()

        # Calculate the total amount
        amount_query = (
            db.select(func.sum(UserTransaction.amount))
            .filter(UserTransaction.user_id == user_id,
                    UserTransaction.category == "Reward")
            )

        
        if from_date_dt:
            amount_query = amount_query.filter(UserTransaction.date_time >= from_date_dt)
        if end_of_day:
            amount_query = amount_query.filter(UserTransaction.date_time <= end_of_day)
        
        print(str(amount_query))  
        total_amount = session.execute(amount_query).scalar()

        
        total_pages = ceil(total_count / per_page)


        transactions_data = [
                {
                    'user_id': transaction.user_id,
                    'amount': transaction.amount,
                    'type': transaction.type,
                    'category': transaction.category,
                    'remark': transaction.remark,
                    'timestamp': transaction.date_time if transaction.date_time else None
                }
                for transaction in transactions
            ]

    return jsonify({'transactions': transactions_data, 'total_amount': total_amount, 'total_pages': total_pages,
                        'current_page': (offset // per_page) + 1,
                        'total_supports': total_count})


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

def get_user_support_tickets(user_id):
    with db.session() as session:
            stmt = db.Select(SupportTicket).filter_by(user_id=user_id)
            stmt = stmt.order_by(text('date_time desc'))

            result = session.execute(stmt)
            tickets = result.scalars().all()
            
            serialized_tickets = [
                {
                    'query_type': ticket.query_type,
                    'query_title': ticket.query_title,
                    'query_desc': ticket.query_desc,
                    'query_status': ticket.query_status,
                    'resolved_issue': ticket.resolved_issue,
                    'date_time': ticket.date_time.strftime('%Y-%m-%d %H:%M:%S')
                }
                for ticket in tickets
            ]
            
            count_open_stmt = (db.Select(func.count()).select_from(SupportTicket).filter_by(user_id=user_id, query_status='Open'))
            open_count_result = session.execute(count_open_stmt)
            open_count = open_count_result.scalar()
            
            count_closed_stmt = (db.Select(func.count()).select_from(SupportTicket).filter_by(user_id=user_id, query_status='Closed'))
            closed_count_result = session.execute(count_closed_stmt)
            closed_count = closed_count_result.scalar()
            

            total_count = open_count + closed_count
            
            return jsonify({
                'transactions': serialized_tickets,
                'open_count': open_count,
                'closed_count': closed_count,
                'total_count': total_count
            })

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