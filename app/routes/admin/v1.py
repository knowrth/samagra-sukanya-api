from flask import  jsonify, request
from flask import Blueprint
from sqlalchemy import text, inspect, desc, func, and_
import pytz
from models.db import db,  mail
import hashlib
from models.decorator import admin_required
from models.UserModels import UserModel, UserTransaction, UserMap
from models.EpinModels import  EPinTransaction, RegisterEPin
from models.ReferencModels import  ResetTokenModel, IncomeLevel, SupportTicket
from flask_mail import  Message
from datetime import datetime
from decimal import Decimal

from datetime import datetime

admin = Blueprint('admin', __name__,)


# Sponsor's Sponsor check
def check_sponsor(user_id, sponsor_id, epin_id):
    epin = epin_id
    current_user_id = user_id
    current_sponsor_id = sponsor_id
    sponsor_info_list = []
    sponsor_ids = []
    non_null_sponsor_ids = []

    user_path = UserMap.query.filter_by(user_id=current_user_id).first()
    user_path_list = user_path.path

    if user_path_list is not None:
            sponsor_list = user_path_list.split("|")
            sponsor_list = [sponsor_id for sponsor_id in sponsor_list if sponsor_id.strip()]
            print('ids:', sponsor_list)
            sponsor_idT = sponsor_list[::-1]
            print(sponsor_idT)
            non_null_sponsor_ids = []

    else:
        sponsor_idT = [sponsor_id]


    for i, sponsor_idb in enumerate(sponsor_idT, start=1):
        if i <= 8:
            success, message = perform_transaction(sponsor_idb, i, user_id, epin )
            print(f"Performing transaction for sponsor ID {sponsor_id} at level {i}: {message}")
        else:
            non_null_sponsor_ids.append(sponsor_idb)
            print(f"Added sponsor ID {sponsor_id} to non-null sponsor IDs list")
            

    if non_null_sponsor_ids:
        level9_ids = ','.join(non_null_sponsor_ids)
        print(f"Inserted level 9 IDs: {','.join(level9_ids)}")
        for sponsor_id in non_null_sponsor_ids:
            success, message = perform_transaction(sponsor_id, 9, user_id, epin )
            print(f"Performing transaction for sponsor ID {sponsor_id} at level 9: {message}")


    return sponsor_info_list



# Transaction from e-pin issued!
def perform_transaction(user_id, level, credited_id, epin):
    income_level = IncomeLevel.query.filter_by(id=level).first()
    if not income_level:
        return False, "Income level not found"

    rate = income_level.rate

    amount = rate  

    latest_transaction = RegisterEPin.query.filter_by(user_id=user_id).order_by(desc(RegisterEPin.date_time)).first()

    if latest_transaction:
        pre_wallet = Decimal(latest_transaction.after_wallet)
    else:
        pre_wallet = Decimal(0)

    after_wallet = pre_wallet + amount

    created_at = datetime.now(pytz.timezone('Asia/Kolkata'))
    user = UserModel.query.filter_by(user_id=credited_id).first()
    if not user:
        return False, "User not found"
    name = user.name
 

    user_transaction = UserTransaction(
        user_id=user_id,
        type='Receipt',  
        category='Commission',
        amount=str(amount),
        remark=f"Level Income {level} from {name}",
        date_time=created_at,
        sponsor_id= None,
        status=None
    )
    db.session.add(user_transaction)

    epin_id = epin

    epin_register = RegisterEPin(
        user_id=user_id,
        epin= epin_id,
        commission=str(amount), 
        level= f"Level-{level}",
        status= 'ISSUED',
        member= name,
        trans_type='CR',
        pre_wallet=str(pre_wallet),
        after_wallet=str(after_wallet),
        log_type='Level Income ',  
        trans_note=f"Level Income {level} from {name}"
        
    )

    db.session.add(epin_register)
    db.session.commit()


    return True, "Transaction completed successfully"



# Mails after creating user

def send_registration_email(user, reset_token):
    try:
        msg = Message('Welcome to Our Application', recipients=[user.email])

        registration_link = f'http://localhost:3000/registration?token={reset_token}'

        body = f"Dear {user.name},\n\nWelcome to our application! Please click on the link below to complete your registration:\n\n{registration_link}\n\nBest regards,\nYour Application Team"
        msg.body = body

        mail.send(msg)

    except Exception as e:
        print("Error sending registration email:", e)


def send_registration_password(user, password):
    try:
        msg = Message('Welcome to Our Application', recipients=[user.email])

        body = f"Dear {user.name},\n\nWelcome to our application! Your login credentials are as follows:\n\nUsername: {user.username}\nPassword: {password}\nMobile: {user.phone}\n\nPlease note that for security reasons, we recommend updating your password after logging in.\n\nBest regards,\nYour Application Team"
        msg.body = body

        mail.send(msg)

    except Exception as e:
        print("Error sending registration email:", e)


def send_reset_email(email, token):
    try:
        msg = Message('Password Reset Link', recipients=[email])

        reset_link = f'http://localhost:3000/reset_password?token={token}'

        body = f"Dear User,\n\nPlease click on the link below to reset your password:\n\n{reset_link}\n\nBest regards,\nYour Application Team"
        msg.body = body

        mail.send(msg)
    except Exception as e:
        print("Error sending reset email:", e)

#admin user-acc creation (removed)

# @admin.route('/admin/users', methods=['POST'])
# @admin_required
# def create_user():
#     try:
#         data = request.json
#         email = data.get('email')
#         name = data.get('name')
#         phone = data.get('phone')

#         if not email:
#             return jsonify({'error': 'Email required'}), 400
#         if UserModel.query.filter_by(email=email).first():
#             return jsonify({'message': 'User with this email already exists'}), 409

#         new_user = UserModel(email=email, role='USER', status='SUSPENDED', paid_status='UNPAID', name=name, phone=phone, pin_type='0 E-Pin')
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

# (removed)

# @admin.route('/admin/users_pswd', methods=['POST'])
# @admin_required
# def create_user_by_pswd():
        
#         data = request.json
#         # email = data.get('email')
#         name = data.get('name')
#         phone = data.get('phone')
#         # password = data.get('password')
        
#         # if not email or not password:
#         #     return jsonify({'message': 'Email and password are required'}), 400
        
#         if UserModel.query.filter_by(name=name, phone=phone).first():
#             return jsonify({'message': 'User with this email already exists'}), 409
        
#         user = UserModel(email=email, role='USER', status='ACTIVE', paid_status='UNPAID', name=name, phone=phone, pin_type='0 E-Pin')
#         user.password = password
#         user.username = user.generate_username()
#         db.session.add(user)
#         db.session.commit()
        
#         send_registration_password(user, password)

#         return jsonify({'message': 'User created successfully'}), 201


# Update password by admin

@admin.route('/admin/users/<string:user_id>', methods=['PUT'])
@admin_required
def update_user_password(user_id):
    try:
        user = UserModel.query.get(user_id)
        if user:
            new_password = request.json.get('password')

            user.password = new_password

            if user.user_status != 'ACTIVE':
                user.user_status = 'ACTIVE'

            db.session.commit()
            # send_registration_password(user, new_password)
            return jsonify({'message': 'User password updated successfully'}), 200

        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        print("Error:", e)
        return jsonify({'error': 'An error occurred while updating user password'}), 500



@admin.route('/admin/users/<string:user_id>/reset_password', methods=['POST'])
@admin_required
def admin_send_reset_password_link(user_id):
    try:
        user = UserModel.query.get(user_id)
        if user:
            if not user.email:
                return jsonify({'error': 'User email not available. Cannot send password reset link.'}), 400
            
            existing_token = ResetTokenModel.query.filter_by(user_id=user_id).first()

            if existing_token:
                if existing_token.valid_till > datetime.utcnow():
                    send_reset_email(user.email, existing_token.token)
                    return jsonify({'message': 'Password reset link sent successfully'}), 200
                else:
                    db.session.delete(existing_token)

            token = hashlib.sha256(user_id.encode()).hexdigest()

            reset_token = ResetTokenModel(user_id=user_id, email=user.email, token=token)
            db.session.add(reset_token)
            db.session.commit()

            send_reset_email(user.email, token)

            return jsonify({'message': 'Password reset link sent successfully'}), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        # print("Error:", e)
        return jsonify({'error': 'An error occurred while sending password reset link'}), 500

# receive epin subscription

@admin.route('/admin/issue_epin', methods=['POST'])
@admin_required
def admin_issue_epin():
    try:
        data = request.json
        # print('Received data: %s', data)  

        user_id = data.get('user_id')
        amount = data.get('pin_type')
        transaction_type = data.get('transaction_type')
        transaction_note = data.get('transaction_note')
        

        if not all([user_id, amount, transaction_type]):
            error_message = 'Missing required fields'
            return jsonify({'error': error_message}), 400

        user = UserModel.query.get(user_id)
        if not user:
            error_message = 'User not found'
            return jsonify({'error': error_message}), 404

        package_map = {
            '0': 'Registered',
            '600': 'Partial Access',
            '1400': 'Partial Access',
            '2000': 'Activated'
        }
        package = package_map.get(amount)
        if not package:
            error_message = 'Invalid pin type'
            return jsonify({'error': error_message}), 400

        user_amt = Decimal(amount)
        user.amount_paid += user_amt
        user.paid_type = transaction_type
        if user.amount_paid >= Decimal('2000'):
            user.paid_status = 'PAID'
            user.user_status = 'ACTIVE'
            user.reg_status = 'Activated'
        else:
            user.reg_status = package
        db.session.commit()

        sponsor_info = data.get('sponsor')

        # print('Sponsor_info:', sponsor_info)

        sponsor_id = None
        if sponsor_info != None :
            try:
                sponsor_name, sponsor_phone = map(str.strip, sponsor_info.split('-'))
                sponsor = UserModel.query.filter_by(name=sponsor_name, phone=sponsor_phone).first()
                if sponsor:
                    sponsor_id = sponsor.user_id
            except ValueError:
                sponsor_id = None
        else:
            sponsor_id = None

        # print('Sponsor ID: %s', sponsor_id)  

        created_at = datetime.now(pytz.timezone('Asia/Kolkata'))

        payment_type = "Payment"
        remark = f"Paid {amount} {transaction_type}, {transaction_note}"
        new_transaction = UserTransaction(
            user_id=user_id,
            type=payment_type,
            category="Activation",
            amount=str(amount),
            remark=remark,
            date_time=created_at,
            sponsor_id=sponsor_id,
            status=None
        )

        db.session.add(new_transaction)
        db.session.commit()

        created_at = datetime.now(pytz.timezone('Asia/Kolkata'))

        if user.amount_paid == Decimal('2000'):
            sponsor_transaction = UserModel.query.filter_by(user_id=user_id).first()
            if sponsor_transaction:
                sponsor_id = sponsor_transaction.sponsor_id
                print(sponsor_id)
                if sponsor_id:
                    epin_transaction = EPinTransaction(
                        transaction_type='generate',
                        user_id=sponsor_id,
                        pin_type='2000 E-pin',
                        pin_amount= '2000.00',
                        created_at=created_at,
                        issued_to=sponsor_id,
                        held_by=sponsor_id,
                    )

                    db.session.add(epin_transaction)
                    db.session.commit()

                else:
                    pass

        return jsonify({'message': 'Epin issued successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500



# Transaction of user

@admin.route('/pay_amount', methods=['POST'])
@admin_required
def pay_amount():
    data = request.json
    name = data.get('name')
    phone = data.get('phone')
    amount_str = data.get('amount')
    if amount_str is not None:
        amount = Decimal(amount_str)
    
    # print('Data:', data)
    created_at = datetime.now(pytz.timezone('Asia/Kolkata'))
    user = UserModel.query.filter_by(name=name, phone=phone).first()
    if user:
        user_id = user.user_id;


        transaction_type = "Payment"
        remark = f"Paid {amount} "
        new_transaction = UserTransaction(
            user_id=user_id,
            type=transaction_type,
            category="Kit Purchase",
            amount=str(amount),
            remark=remark,
            sponsor_id=user_id,
            date_time=created_at,
            status=None
        )

        db.session.add(new_transaction)
        db.session.commit()

        
        if amount == Decimal('0.00'):
            epin_transaction = EPinTransaction(
                    transaction_type='generate',
                    user_id=user_id,
                    pin_type='0 E-pin',
                    pin_amount= '0.00',
                    created_at=created_at,
                    issued_to=user_id,
                    held_by=user_id,
                )
        else:
            epin_transaction = EPinTransaction(
                    transaction_type='generate',
                    user_id=user_id,
                    pin_type='500 E-pin',
                    pin_amount= '500.00',
                    created_at=created_at,
                    issued_to=user_id,
                    held_by=user_id,
                )
        db.session.add(epin_transaction)
        db.session.commit()
        

        return jsonify({'message': 'Amount paid successfully'}), 200
    else:
        return jsonify({'error': 'User not found'}), 404


# transactions table

@admin.route('/admin/transactions', methods=['GET'])
@admin_required
def get_all_transactions_with_user_email():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        transactions = db.session.query(
            RegisterEPin,
            UserModel.username,
            UserModel.name
        ).join(
            UserModel,
            RegisterEPin.user_id == UserModel.user_id
        ).order_by(desc(RegisterEPin.date_time))

        paginated_transactions = transactions.paginate(page=page, per_page=per_page)

        transaction_data = [{
            'user_email': username,
            'name': name,
            'amount': transaction.commission,
            'pre_wallet_amount': transaction.pre_wallet,
            'after_wallet_amount': transaction.after_wallet,
            'transaction_mode_type': transaction.trans_type,
            'logType': transaction.log_type,
            'transaction_note': transaction.trans_note,
            'timestamp': transaction.date_time.strftime('%Y-%m-%d %H:%M:%S'),
        } for transaction, username, name in paginated_transactions.items]
        print(paginated_transactions.pages)
        return jsonify({
            'transactions': transaction_data,
            'total_pages': paginated_transactions.pages,
            'current_page': paginated_transactions.page,
            'total_transactions': paginated_transactions.total
        }), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': 'An error occurred while fetching transactions'}), 500


# names and phone 

@admin.route('/v1/usernames-and-phones', methods=['GET'])
def get_usernames_and_phones():
    try:
        users = UserModel.query.all()

        data = [f"{user.name} - {user.phone}" for user in users]

        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@admin.route('/v1/names-and-phones', methods=['GET'])
def get_names_and_phones():
    try:
        users = UserModel.query.all()

        data = [(user.name, user.phone) for user in users]

        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# user table 

@admin.route('/v1/users', methods=['GET'])
@admin_required
def get_all_users():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        users_paginated = UserModel.query.order_by(UserModel.user_id.asc()).paginate(page=page, per_page=per_page, error_out=False)

        user_list = []
        for user in users_paginated.items:
            user_data = {
                'user_id': user.user_id,
                'email': user.email,
                'role': user.role,
                'name': user.name,
                'phone': user.phone,
                'paid_status': user.paid_status,
                'username': user.username,
                'amount_paid': user.amount_paid
            }
            user_list.append(user_data)

        return jsonify({
            'users': user_list,
            'total_users': users_paginated.total,
            'current_page': users_paginated.page,
            'total_pages': users_paginated.pages
        }), 200
    
    except Exception as e:
        print("An error occurred:", e)  # Print the error
        return jsonify({'error': 'An error occurred. Please try again later.'}), 500

# pin table

@admin.route('/v1/e-pin/transactions', methods=['GET'])
@admin_required
def get_latest_transactions():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # Subquery to get the latest created_at for each epin_id
        subquery = db.session.query(
            EPinTransaction.epin_id,
            func.max(EPinTransaction.created_at).label('latest_created_at')
        ).group_by(EPinTransaction.epin_id).\
            order_by(desc(func.max(EPinTransaction.created_at))).subquery()

        # Main query to fetch EPinTransaction records joined with the latest created_at
        transactions_query = db.session.query(EPinTransaction).\
            join(subquery, and_(
                EPinTransaction.epin_id == subquery.c.epin_id,
                EPinTransaction.created_at == subquery.c.latest_created_at
            )).order_by(desc(subquery.c.latest_created_at))

        # Paginate the results
        paginated_transactions = transactions_query.paginate(page=page, per_page=per_page, error_out=False)

        # Serialize each transaction into a dictionary
        serialized_transactions = [transaction.serialize() for transaction in paginated_transactions.items]

        # Return paginated results as JSON response
        return jsonify({
            'transactions': serialized_transactions,
            'total_transactions': paginated_transactions.total,
            'current_page': paginated_transactions.page,
            'total_pages': paginated_transactions.pages
        }), 200
    
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

# withdrawals request table
@admin.route('/v1/user_withdrawal_list', methods=['GET'])
@admin_required
def get_user_withdrawal():
    try:
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)

        user_transactions = UserTransaction.query.filter_by(status="Pending").paginate(page=page, per_page=per_page, error_out=False)

        if user_transactions.items:
            withdrawals = []
            for transaction in user_transactions.items:
                user = UserModel.query.filter_by(user_id=transaction.user_id).first()
                if user:
                    # date_time_ist = transaction.date_time.astimezone(pytz.timezone('Asia/Kolkata'))
                    
                    withdrawal = {
                        'user_id': user.user_id,
                        'name': user.name,
                        'username': user.username,
                        'phone': user.phone,
                        'amount': transaction.amount,
                        'remark': transaction.remark,
                        'date_time': transaction.date_time,  # Format datetime as string
                    }
                    withdrawals.append(withdrawal)
                else:
                    return jsonify({'error': 'User not found'}), 404
            
            return jsonify({
                'withdrawals': withdrawals,
                'total_pages': user_transactions.pages,
                'current_page': user_transactions.page,
                'total_withdrawals': user_transactions.total
            }), 200

        else:
            return jsonify({'success': 'No withdrawal requests found'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500



@admin.route('/v1/user_withdrawal/<user_id>', methods=['POST'])
@admin_required
def user_withdrawal(user_id):
    data = request.json
    amount = data.get('amount')
    created_at = data.get('created_at')
    remarkAdmin = data.get('remark')
    # print(created_at)
    user_transaction = UserTransaction.query.filter_by(user_id=user_id, amount=amount, date_time=created_at, status="Pending").first()
    print('transaction', user_transaction)
    if user_transaction:
        # transaction_type = "Debit"
        if remarkAdmin:
            remark = f"Withdrawal amount {amount}, {remarkAdmin} "
        else:
            remark = f"Withdrawal amount {amount}"

        # db.session.delete(user_transaction)
        created_at = datetime.now(pytz.timezone('Asia/Kolkata'))
        user_transaction.status = "Approved",
        user_transaction.remark = remark,
        user_transaction.date_time = created_at,
        # Create a new transaction
        # new_transaction = UserTransaction(
        #     user_id=user_id,
        #     type=transaction_type,
        #     category="Withdrawals",
        #     amount=str(amount),
        #     remark=remark,
        #     date_time=created_at,
        #     sponsor_id=None,
        #     status="Approved"
        # )

        # Commit the changes
        # db.session.add(new_transaction)
        db.session.commit()

        return jsonify({'message': 'Withdrawal successful'})

    else:
        return jsonify({'error': 'User transaction not found'}), 404


# user transaction table

@admin.route('/user/transactions/<user_id>', methods=['GET'])
@admin_required
def get_user_transactions(user_id):
    try:
        user_transactions = UserTransaction.query.filter_by(user_id=user_id).filter(UserTransaction.category != 'Commission').all()

        if user_transactions:
            transactions = [{
                'id': transaction.id,
                'type': transaction.type,
                'category': transaction.category,
                'amount': transaction.amount,
                'remark': transaction.remark,
                'date_time': transaction.date_time,
                'sponsor_id': transaction.sponsor_id
            } for transaction in user_transactions]
            
            return jsonify({'transactions': transactions}), 200
        else:
            return jsonify({'message': 'No transactions found for the user'}), 404
    
    except Exception as e:
        print('Error in get_user_transactions: %s', str(e))
        return jsonify({'error': 'Internal Server Error'}), 500    
    


# support table

@admin.route('/v1/user_support_list', methods=['GET'])
@admin_required
def get_user_support():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        user_support = SupportTicket.query.filter_by(query_status="Open") \
                        .paginate(page=page, per_page=per_page, error_out=False)

        supports = []

        for support in user_support.items:
            user = UserModel.query.filter_by(user_id=support.user_id).first()
            if user:
                ticket = {
                    'user_id': user.user_id,
                    'name': user.name,
                    'username': user.username,
                    'phone': user.phone,
                    'query_type': support.query_type,
                    'query_title': support.query_title,
                    'query_desc': support.query_desc,
                    'query_status': support.query_status,
                    'date_time': support.date_time.strftime('%Y-%m-%d %H:%M:%S.%f'),  
                }
                supports.append(ticket)
            else:
                return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'supports': supports,
            'total_pages': user_support.pages,
            'current_page': user_support.page,
            'total_supports': user_support.total
        }), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': 'An error occurred while fetching user supports'}), 500




@admin.route('/v1/resolve_user_support/<user_id>', methods=['POST'])
@admin_required
def resolve_user_support(user_id):
    data = request.json
    resolved_issue = data.get('resolved_issue')
    created_at = data.get('created_at')
    # remarkAdmin = data.get('remark')
    user_support = SupportTicket.query.filter_by(user_id=user_id, date_time=created_at).first()

    if user_support:
        # created_at = datetime.now(pytz.timezone('Asia/Kolkata'))
        # user_support.date_time = created_at,
        user_support.query_status = "Closed",
        user_support.resolved_issue = resolved_issue,
        db.session.commit()

        return jsonify({'message': 'Ticket closed successful'})
    
    else:
        return jsonify({'error': 'Support ticket not found'}), 404
        








@admin.route('/v2/user_counts', methods=['GET'])
@admin_required

def get_user_counts():
    try:
        total_count = UserModel.query.count()
        paid_count = UserModel.query.filter_by(paid_status='PAID').count()
        unpaid_count = UserModel.query.filter_by(paid_status='UNPAID').count()

        response = {
            'total_count': total_count,
            'paid_count': paid_count,
            'unpaid_count': unpaid_count
        }
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@admin.route('/v2/pin_counts', methods=['GET'])
@admin_required

def pin_counts():
    try:
        unique_pins = db.session.query(EPinTransaction.pin).distinct().all()
        total_unique_pins = len(unique_pins)

        used_pins = db.session.query(EPinTransaction.pin).filter(EPinTransaction.used_by.isnot(None)).distinct().all()
        used_pins_count = len(used_pins)

        unused_pins_count = total_unique_pins - used_pins_count

        return jsonify({
            'total_unique_pins': total_unique_pins,
            'used_pins': used_pins_count,
            'unused_pins': unused_pins_count
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@admin.route('/v2/package_counts', methods=['GET'])
@admin_required

def package_counts():
    try:
        # Count unique pins for user package and their used and unused counts
        user_package_pins_count = db.session.query(EPinTransaction.pin).filter_by(pin_type='500 E-pin').distinct().count()
        user_package_used_count = db.session.query(EPinTransaction).filter(EPinTransaction.pin_type == '500 E-pin', EPinTransaction.used_by.isnot(None)).count()
        user_package_unused_count = user_package_pins_count - user_package_used_count

        # Count unique pins for registration package and their used and unused counts
        registration_package_pins_count = db.session.query(EPinTransaction.pin).filter_by(pin_type='0 E-pin').distinct().count()
        registration_package_used_count = db.session.query(EPinTransaction).filter(EPinTransaction.pin_type == '0 E-pin', EPinTransaction.used_by.isnot(None)).count()
        registration_package_unused_count = registration_package_pins_count - registration_package_used_count

        registration_2000_pins_count = db.session.query(EPinTransaction.pin).filter_by(pin_type='2000 E-pin').distinct().count()
        registration_2000_used_count = db.session.query(EPinTransaction).filter(EPinTransaction.pin_type == '2000 E-pin', EPinTransaction.used_by.isnot(None)).count()
        registration_2000_unused_count = registration_2000_pins_count - registration_2000_used_count

        return jsonify({
            'user_package_pins': user_package_pins_count,
            'user_package_used': user_package_used_count,
            'user_package_unused': user_package_unused_count,
            'registration_package_pins': registration_package_pins_count,
            'registration_package_used': registration_package_used_count,
            'registration_package_unused': registration_package_unused_count,
            'registration_2000_pins': registration_2000_pins_count,
            'registration_2000_used': registration_2000_used_count,
            'registration_2000_unused': registration_2000_unused_count
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500