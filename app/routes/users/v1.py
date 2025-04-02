from flask import  jsonify, request
from flask import Blueprint
from sqlalchemy import func
from sqlalchemy import case
from models.db import db
import hashlib
from models.UserModels import UserModel, UserTransaction, UserMap
from models.EpinModels import RegisterEPin
from models.ReferencModels import  ResetTokenModel
from services.user_details_service import get_user_status, reset_password, user_sponsor, user_income_total, get_sponsor_stats
from models.decorator import user_required

from datetime import datetime

users = Blueprint('users', __name__,)



# Dashboard
from sqlalchemy.exc import SQLAlchemyError, InvalidRequestError


# user Income

@users.route('/v1/users/transactions/amount/<user_id>', methods=['GET'])
@user_required
def get_transactions_amount_by_user_id(user_id):
    try:
        user = user_income_total(user_id)
        # total_transaction_amount_query = db.session.query(func.sum(RegisterEPin.commission)) \
        #     .filter(RegisterEPin.user_id == user_id)

        # total_transaction_amount = total_transaction_amount_query.scalar() or 0

        # total_withdrawal_amount_query = db.session.query(func.sum(UserTransaction.amount)) \
        #     .filter(UserTransaction.user_id == user_id,
        #             UserTransaction.category == 'Withdrawals',
        #             UserTransaction.type == 'Debit')
        # # print('total',total_withdrawal_amount_query)

        # total_withdrawal_amount = total_withdrawal_amount_query.scalar() or 0
        
        # amount = total_transaction_amount - total_withdrawal_amount

        # return jsonify({'total_withdrawal_amount': total_withdrawal_amount,
        #                 'total_amount': total_transaction_amount,
        #                 'amount': amount}), 200
        return user, 200
    except (SQLAlchemyError, InvalidRequestError) as e:
        # print('error', e)
        return jsonify({'error': 'Internal Server Error'}), 500


# sponsor details

@users.route('/v1/user_sponsor/<user_id>', methods=['GET'])
@user_required
def get_user_sponsor(user_id):
    try:
        # user = UserModel.query.filter_by(user_id=user_id).first()
        # if user:
        #     sponsor_id = user.sponsor_id
        #     if sponsor_id:
        #         sponsor = UserModel.query.filter_by(user_id=sponsor_id).first()
        #         return jsonify({
        #             'name': sponsor.name,
        #             'phone': sponsor.phone,
        #             'userName': sponsor.username,
        #         }), 200
        #     else:
        #         return jsonify({}), 200 
            
        # else:
        #     return jsonify({'error': 'User not found'}), 404
        
        user = user_sponsor(user_id)
        return user, 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Team count

@users.route('/v2/team_count/<user_id>', methods=['GET'])
@user_required
def get_team_count(user_id):
    # try:
    #     results = db.session.query(
    #         func.length(func.substring_index(UserMap.path, user_id, -1)) - func.length(func.replace(func.substring_index(UserMap.path, user_id, -1), '|', '')),
    #         func.count(UserMap.user_id).label('sponsor_count'),
    #         UserMap.sponsor_id,
    #         func.sum(func.case([(UserModel.paid_status == 'PAID', 1)], else_=0)).label('paid_count'),
    #         func.sum(func.case([(UserModel.paid_status == 'UNPAID', 1)], else_=0)).label('unpaid_count')
    #     ).join(UserModel, UserModel.user_id == UserMap.user_id)\
    #      .filter(UserMap.path.like(f'%{user_id}|%'))\
    #      .group_by(func.length(func.substring_index(UserMap.path, user_id, -1)) - func.length(func.replace(func.substring_index(UserMap.path, user_id, -1), '|', '')), UserMap.sponsor_id)\
    #      .order_by(func.length(func.substring_index(UserMap.path, user_id, -1)) - func.length(func.replace(func.substring_index(UserMap.path, user_id, -1), '|', '')))\
    #      .all()

    try:
#         results = db.session.query(
#     func.length(func.substring(UserMap.path, func.strpos(UserMap.path, user_id))) - 
#     func.length(func.replace(func.substring(UserMap.path, func.strpos(UserMap.path, user_id)), '|', '')),
#     func.count(UserMap.user_id).label('sponsor_count'),
#     UserMap.sponsor_id,
#     func.sum(case((UserModel.paid_status == 'PAID', 1), else_=0)).label('paid_count'),
#     func.sum(case((UserModel.paid_status != 'PAID', 1), else_=0)).label('unpaid_count'),
# ).select_from(UserMap).join(UserModel, UserModel.user_id == UserMap.user_id).filter(
#     UserMap.path.like(f'%{user_id}|%')
# ).group_by(
#     func.length(func.substring(UserMap.path, func.strpos(UserMap.path, user_id))) - 
#     func.length(func.replace(func.substring(UserMap.path, func.strpos(UserMap.path, user_id)), '|', '')),
#     UserMap.sponsor_id
# ).order_by(
#     func.length(func.substring(UserMap.path, func.strpos(UserMap.path, user_id))) - 
#     func.length(func.replace(func.substring(UserMap.path, func.strpos(UserMap.path, user_id)), '|', ''))
# ).all()

#         total_results = {}
#         for row in results:
#             pipe_count = min(row[0], 9)
#             if pipe_count in total_results:
#                 total_results[pipe_count]['sponsor_count'] += row[1]
#                 total_results[pipe_count]['paid_count'] += row[3]
#                 total_results[pipe_count]['unpaid_count'] += row[4]
#             else:
#                 total_results[pipe_count] = {
#                     'Level': pipe_count,
#                     'sponsor_count': row[1],
#                     'paid_count': row[3],
#                     'unpaid_count': row[4],
#                 }

#         data = list(total_results.values())
#         return jsonify(data), 200

        response = get_sponsor_stats(user_id)
        return response

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    



# reset Pswd


@users.route('/v1/users/<string:user_id>', methods=['PUT'])
@user_required
def update_password(user_id):
    try:

        new_password = request.json.get('password')

        # user = UserModel.query.get(user_id)
        # user.password = new_password
        # db.session.commit()

        user = reset_password(user_id=user_id, new_password=new_password)

        return user, 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500





# @users.route('/v1/users', methods=['POST'])
# def self_create_user():
#     try:
#         data = request.json
#         email = data.get('email')

#         if not email:
#             return jsonify({'error': 'Email is required'}), 400

#         new_user = UserModel(email=email, status='SUSPENDED', role='USER', paid_status='UNPAID')
#         new_user.username = new_user.generate_username()
#         db.session.add(new_user)
#         db.session.commit()

#         reset_token = hashlib.sha256(new_user.user_id.encode()).hexdigest()
#         reset_token_obj = ResetTokenModel(user_id=new_user.user_id, email=email, token=reset_token)
#         db.session.add(reset_token_obj)
#         db.session.commit()

#         send_registration_email(new_user, reset_token)

#         return jsonify({'message': 'User created successfully. Set password link sent to the email.'}), 201

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500


# @users.route('/v1/users', methods=['PUT'])
# def set_password():
#     try:
#         token = request.args.get('token')
#         if not token:
#             return jsonify({'error': 'Token is missing'}), 400

#         reset_token_obj = ResetTokenModel.query.filter_by(token=token).first()
#         if not reset_token_obj:
#             return jsonify({'error': 'Invalid or expired token'}), 400
        
#         if datetime.utcnow() > reset_token_obj.valid_till:
#             return jsonify({'error': 'Token has expired'}), 400

#         data = request.get_json()  
#         new_password = data.get('password') 
#         user = UserModel.query.get(reset_token_obj.user_id)
#         user.password = new_password
#         user.status = 'ACTIVE'
#         db.session.delete(reset_token_obj)
#         db.session.commit()

#         return jsonify({'message': 'Password updated successfully'}), 200

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500


from datetime import datetime, timedelta

# @users.route('/v1/users/reset_password', methods=['GET'])
# def request_reset_password():
#     email = request.args.get('email')
#     phone = request.args.get('phone')

#     user = None
#     if phone:
#         user = UserModel.query.filter_by(phone=phone).first()
#     elif email:
#         user = UserModel.query.filter_by(email=email).first()

#     if not user:
#         return jsonify({'error': 'User not found'}), 404

#     if email and not user.email:
#         user.email = email
#         db.session.commit()

#     existing_token = ResetTokenModel.query.filter_by(user_id=user.user_id).first()

#     if existing_token:
#         if existing_token.valid_till > datetime.utcnow():
#             send_reset_email(user.email, existing_token.token)
#             return jsonify({'message': 'Password reset link sent successfully'}), 200
#         else:
#             db.session.delete(existing_token)

#     token = hashlib.sha256(user.user_id.encode()).hexdigest()
#     valid_till = datetime.utcnow() + timedelta(hours=1)  # Example: Token valid for 1 hour

#     reset_token = ResetTokenModel(user_id=user.user_id, email=user.email, token=token, valid_till=valid_till)
#     db.session.add(reset_token)
#     db.session.commit()

#     send_reset_email(user.email, token)

#     return jsonify({'message': 'Reset password link sent successfully'}), 200






@users.route('/v1/users/<string:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = get_user_status(user_id)
        
        if user:
            # status = user.user_status
            # amount = user.amount_paid
            # paid_status = user.paid_status
            
            return user, 200
        else:
            return jsonify({'error': 'User not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

