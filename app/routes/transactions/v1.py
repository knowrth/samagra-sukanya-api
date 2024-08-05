from flask import  jsonify, request
from flask import Blueprint
from sqlalchemy import func, desc
import pytz
from models.db import db
from models.UserModels import UserModel, UserTransaction,  UserBankDetails
from models.EpinModels import  RegisterEPin
from models.ReferencModels import  SupportTicket
from models.decorator import user_required
from services.user_team_service import get_transaction_summary, income_transaction_user, create_support_ticket, create_withdrawal_request
from datetime import datetime

transaction = Blueprint('transaction', __name__,)


# Income

# user level income

@transaction.route('/v1/users/income_transactions/<user_id>', methods=['GET'])
@user_required
def get_income_transactions_by_user_id(user_id):
    try:
        # transactions = RegisterEPin.query.filter_by(user_id=user_id).order_by(desc(RegisterEPin.date_time)).all()
        # serialized_transactions = [{
        #     'user_id': transaction.user_id,
        #     'amount': transaction.commission,
        #     'level': transaction.level,
        #     'member': transaction.member,
        #     'logType': transaction.log_type,
        #     'pre_wallet_amount': transaction.pre_wallet,
        #     'after_wallet_amount': transaction.after_wallet,
        #     'transaction_mode_type': transaction.trans_type,
        #     'transaction_note': transaction.trans_note,
        #     'timestamp': transaction.date_time if transaction.date_time else None
        # } for transaction in transactions]
        # total_transaction_amount_query = db.session.query(func.sum(RegisterEPin.commission))\
        #     .filter(RegisterEPin.user_id == user_id).scalar()
        # return jsonify({'transactions': serialized_transactions, 'total_amount': total_transaction_amount_query}), 200 
        transaction = income_transaction_user(user_id)
        if transaction:
            return transaction
    except Exception as e:
        print(e)
        return jsonify({'error': 'Internal Server Error'}), 500

# level wise reward count

@transaction.route('/user_transaction_summary', methods=['GET'])
@user_required
def user_transaction_summary():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    # query_result = db.session.query(RegisterEPin.level, db.func.count(), db.func.sum(RegisterEPin.commission)) \
    #     .filter(RegisterEPin.user_id == user_id) \
    #     .group_by(RegisterEPin.level) \
    #     .all()

    # summary = [{'level': row[0], 'count': row[1], 'sum_amount': row[2]} for row in query_result]
    summary = get_transaction_summary(user_id)
    if summary :

        return summary, 200

# Transaction

#  transaction table

@transaction.route('/v1/users/transactions/<user_id>', methods=['GET'])
@user_required
def get_transactions_by_user_id(user_id):
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        transactions = UserTransaction.query.filter_by(user_id=user_id).order_by(desc(UserTransaction.date_time)).paginate(page=page, per_page=per_page, error_out=False)
        serialized_transactions = [{
            'user_id': transaction.user_id,
            'amount': transaction.amount,
            'type': transaction.type,
            'category': transaction.category,
            'remark': transaction.remark,
            'timestamp': transaction.date_time if transaction.date_time else None
        } for transaction in transactions]
        return jsonify({'transactions': serialized_transactions,
                        'total_pages': transactions.pages,
                        'current_page': transactions.page,
                        'total_supports': transactions.total}), 200
    except Exception as e:
        # print(e)
        return jsonify({'error': 'Internal Server Error'}), 500


# Support Tickets

# new ticket
@transaction.route('/v1/users/support_ticket/<user_id>', methods=['POST'])
@user_required
def support_ticket(user_id):
    try:
        data = request.json
        query_type = data.get('query_type')
        query_title = data.get('query_title')
        query_description = data.get('query_description')


        # created_at = datetime.now(pytz.timezone('Asia/Kolkata'))

        new_ticket = create_support_ticket(user_id=user_id, query_type=query_type, query_title=query_title, query_desc=query_description)
        if new_ticket:
            return new_ticket

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# support ticket table get by user_id

@transaction.route('/v1/users/support_ticket_all/<user_id>', methods=['GET'])
@user_required
def get_all_support_ticket(user_id):
    try:
        tickets = SupportTicket.query.filter_by(user_id=user_id).order_by(desc(SupportTicket.date_time)).all()
        serialized_tickets = [{
            'query_type': ticket.query_type,
            'query_title': ticket.query_title,
            'query_desc': ticket.query_desc,
            'query_status': ticket.query_status,
            'resolved_issue': ticket.resolved_issue,
            'date_time': ticket.date_time,
        } for ticket in tickets]
        open_count = SupportTicket.query.filter_by(query_status='Open').count()
        closed_count = SupportTicket.query.filter_by(query_status='Closed').count()
        total_count = SupportTicket.query.count()
        return jsonify({'transactions': serialized_tickets, 'open_count':open_count, 'closed_count': closed_count, 'total_count': total_count }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500




# IWallet

# withdrawal request


@transaction.route('/v1/user_withdrawal_request/<user_id>', methods=['POST'])
@user_required
def user_withdrawal_request(user_id):
    data = request.json
    amount = data.get('amount')
    # user = UserModel.query.filter_by(user_id=user_id).first()

    # created_at = datetime.now(pytz.timezone('Asia/Kolkata'))

    # if user:

    #     bank_details = UserBankDetails.query.filter_by(user_id=user_id).first()
    #     if not bank_details or not bank_details.bank_name or not bank_details.ifsc_code:
    #         return jsonify({'message': 'User bank details (bank name or IFSC code) are missing. Please update bank details.'}), 400

    #     withdrawal_request = UserTransaction(
    #         user_id=user_id,
    #         amount=amount,
    #         remark=f"Request from {user.name} amount {amount}",
    #         status='Pending',  
    #         category='Withdrawals',
    #         date_time=created_at,
    #         sponsor_id= None,
    #         type='Debit'


    #     )
    #     db.session.add(withdrawal_request)
    #     db.session.commit()
    try:
        withdrawal_request = create_withdrawal_request(user_id=user_id, amount=amount)
        if withdrawal_request:
            return withdrawal_request, 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500



# user withdrawals table


@transaction.route('/v1/users/withdrawals/<user_id>', methods=['GET'])
@user_required
def get_withdrawals_by_user_id(user_id):
    try:
        withdrawals = UserTransaction.query.filter_by(user_id=user_id, category="Withdrawals")\
                                            .order_by(UserTransaction.date_time.desc())\
                                            .all()
        
        serialized_withdrawals = [{'amount': withdrawal.amount, 
                                    'type' : withdrawal.type,
                                    'status': withdrawal.status,
                                    'timestamp': withdrawal.date_time.strftime('%Y-%m-%d %H:%M:%S')} 
                                    for withdrawal in withdrawals]
        
        return jsonify({'withdrawals': serialized_withdrawals}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': 'Internal Server Error'}), 500

