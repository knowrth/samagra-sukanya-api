from flask import  jsonify, request
from flask import Blueprint
from sqlalchemy import text, inspect, desc, or_
from models.db import db
from models.UserModels import UserModel, UserTransaction, UserMap
from models.EpinModels import  EPinTransaction, RegisterEPin
from models.ReferencModels import  IncomeLevel
from models.decorator import user_required
from routes.admin.v1 import check_sponsor
from sqlalchemy.exc import IntegrityError
from services.user_pin_service import create_user_with_epin, epin_transfer_epin, multiple_epin_transfer, get_transfer_epin_details, get_epin_count_by_user, get_paginated_transactions

import pytz
from datetime import datetime

epins = Blueprint('epins', __name__,)



# Sponsor's Sponsor check
# def check_sponsor_ac(user_id, sponsor_id, epin_id):
#     epin = epin_id
#     current_user_id = user_id
#     current_sponsor_id = sponsor_id
#     sponsor_info_list = []
#     sponsor_ids = []
#     non_null_sponsor_ids = []

#     while current_sponsor_id is not None:
#         sponsor = UserTransaction.query.filter_by(user_id=current_sponsor_id, category="Activation").first()
#         if sponsor:
#             has_sponsor = sponsor.sponsor_id is not None
#             sponsor_info = {'sponsor_id': current_sponsor_id, 'has_sponsor': has_sponsor}
#             sponsor_info_list.append(sponsor_info)
#             sponsor_ids.append(current_sponsor_id)
#             current_sponsor_id = sponsor.sponsor_id
#         else:
#             current_sponsor_id = None
#             sponsor_ids.append(None)

#     referral_network = ReferralNetwork(user_id=user_id)

#     setattr(referral_network, 'level1', user_id)
#     success, message = perform_transaction(user_id, 1, user_id, epin)
#     # print(f"Performing transaction for level 1: {message}")


#     for i, sponsor_id in enumerate(sponsor_ids, start=2):
#         if i <= 8:
#             setattr(referral_network, f'level{i}', sponsor_id)
#             # print(f"Inserted sponsor ID {sponsor_id} into level {i}")
#             success, message = perform_transaction(sponsor_id, i, user_id, epin )
#             # print(f"Performing transaction for sponsor ID {sponsor_id} at level {i}: {message}")
#         else:
#             non_null_sponsor_ids.append(sponsor_id)
#             # print(f"Added sponsor ID {sponsor_id} to non-null sponsor IDs list")
            

#     if non_null_sponsor_ids:
#         level9_ids = ','.join(non_null_sponsor_ids)
#         setattr(referral_network, 'level9', level9_ids)
#         # print(f"Inserted level 9 IDs: {','.join(level9_ids)}")
#         for sponsor_id in non_null_sponsor_ids:
#             success, message = perform_transaction(sponsor_id, 9, user_id, epin )
#             # print(f"Performing transaction for sponsor ID {sponsor_id} at level 9: {message}")


#     for i in range(len(sponsor_ids) + 2, 10):
#         setattr(referral_network, f'level{i}', None)

#     db.session.add(referral_network)
#     db.session.commit()
#     return sponsor_info_list



# Transaction from e-pin issued!
# def perform_transaction(user_id, level, credited_id, epin):
#     income_level = IncomeLevel.query.filter_by(id=level).first()
#     if not income_level:
#         return False, "Income level not found"

#     rate = income_level.rate

#     amount = rate  

#     latest_transaction = RegisterEPin.query.filter_by(user_id=user_id).order_by(desc(RegisterEPin.after_wallet), desc(RegisterEPin.created_at)).first()

#     if latest_transaction:
#         pre_wallet = Decimal(latest_transaction.after_wallet)
#     else:
#         pre_wallet = Decimal(0)

#     after_wallet = pre_wallet + amount


#     user = UserModel.query.filter_by(user_id=credited_id).first()
#     if not user:
#         return False, "User not found"
#     email = user.email


#     user_transaction = UserTransaction(
#         user_id=user_id,
#         type='Receipt',  
#         category='Commission',
#         amount=str(amount),
#         remark=f"Level Income {level} from {email}",
#         sponsor_id= None
#     )
#     db.session.add(user_transaction)

#     epin_id = epin

#     epin_register = RegisterEPin(
#         user_id=user_id,
#         epin= epin_id,
#         commission=str(amount), 
#         level= f"Level-{level}",
#         status= 'ISSUED',
#         member= email,
#         trans_type='CR',
#         pre_wallet=str(pre_wallet),
#         after_wallet=str(after_wallet),
#         log_type='Level Income ',  
#         trans_note=f"Level Income {level} from {email}"
        
#     )

#     db.session.add(epin_register)
#     db.session.commit()

#     transaction = TransactionModel(
#         user_id=user_id,
#         amount=str(amount), 
#         level= f"Level-{level}",
#         member= email,
#         logType='CR',
#         pre_wallet_amount=str(pre_wallet),
#         after_wallet_amount=str(after_wallet),
#         transaction_mode_type='Income Level ',  
#         transaction_note=f"Income level {level} from {email}"
#     )


#     db.session.add(transaction)
#     db.session.commit()

#     return True, "Transaction completed successfully"





# Transfer epins


@epins.route('/v1/transfer_epin', methods=['POST'])
@user_required
def transfer_epin():
    data = request.json
    # epin_id = data.get('epin_id')
    pin = data.get('pin')
    name = data.get('name')
    phone = data.get('phone')
    user_id = data.get('user_id')

    # new_user = UserModel.query.filter_by(name=name, phone=phone).first()
    # if not new_user:
    #     return jsonify({'message': 'User not found with the provided email'}), 404
    
    # # user_id = new_user.user_id
    # # print('user_id', user_id)
    
    # epin_transaction = EPinTransaction.query.filter_by(pin=pin).order_by(desc(EPinTransaction.created_at)).first()
    
    # if not epin_transaction:
    #     return jsonify({'message': 'EPin transaction not found'}), 404

    # if epin_transaction.user_id != user_id:
    #     return jsonify({'message': 'EPin is already transferred to another user'}), 400
    
    # if epin_transaction.transaction_type != "registered":
    #     created_at = datetime.now(pytz.timezone('Asia/Kolkata'))
    #     transfer_epin = EPinTransaction(
    #         epin_id=epin_transaction.epin_id,
    #         transaction_type="transfer",
    #         user_id=new_user.user_id,
    #         sponsor_id=epin_transaction.user_id,
    #         created_at=created_at,
    #         pin=epin_transaction.pin,
    #         pin_type=epin_transaction.pin_type,
    #         pin_amount=epin_transaction.pin_amount,
    #         issued_to=epin_transaction.issued_to,
    #         held_by=new_user.user_id,
    #     )

    #     db.session.add(transfer_epin)
    #     db.session.commit()
    try:
        epin = epin_transfer_epin(phone=phone, user_id=user_id, pin=pin, name=name)
        if epin :
            return jsonify({'message': 'EPin transferred successfully'})
        else:
            return jsonify({'message': 'EPin is already registered'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'An error occurred while transferring epin', 'details': str(e)}), 500

        


# multiple transfer E-pin

@epins.route('/v1/transfer_multiple_epin', methods=['POST'])
@user_required
def transfer_multiple_epin():
    data = request.json
    # epin_id = data.get('epin_id')
    pin = data.get('pin')
    name = data.get('name')
    phone = data.get('phone')
    user_id = data.get('user_id')
    print('Pins:', pin)

    # new_user = UserModel.query.filter_by(name=name, phone=phone).first()
    # if not new_user:
    #     return jsonify({'message': 'User not found with the provided email'}), 404
    
    # # user_id = new_user.user_id
    # # print('user_id', user_id)
    # pin_list = pin.split(', ')
    
    # for epin in pin_list:
    #     epin_transaction = EPinTransaction.query.filter_by(pin=epin).order_by(desc(EPinTransaction.created_at)).first()
    #     # print('epin:', epin_transaction)

    #     if not epin_transaction:
    #         return jsonify({'message': 'EPin transaction not found'}), 404

    #     if epin_transaction.user_id != user_id:
    #         return jsonify({'message': 'EPin is already transferred to another user'}), 400

    #     if epin_transaction.transaction_type != "registered":
    #         print('pin:', epin_transaction.pin)
    #         created_at = datetime.now(pytz.timezone('Asia/Kolkata'))
    #         transfer_epin = EPinTransaction(
    #             epin_id=epin_transaction.epin_id,
    #             transaction_type="transfer",
    #             user_id=new_user.user_id,
    #             sponsor_id=epin_transaction.user_id,
    #             created_at=created_at,
    #             pin=epin_transaction.pin,
    #             pin_type=epin_transaction.pin_type,
    #             pin_amount=epin_transaction.pin_amount,
    #             issued_to=epin_transaction.issued_to,
    #             held_by=new_user.user_id,
    #         )
    #         db.session.add(transfer_epin)
    #         db.session.commit()
    #         # print('TransferedPin:', transfer_epin.user_id)
    try:
        epin = multiple_epin_transfer(phone=phone, user_id=user_id, pin=pin, name=name)
        if epin :
            return jsonify({'message': 'All EPins transferred successfully'})
        else:
            return jsonify({'message': 'EPin is already registered'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'An error occurred while transferring epin', 'details': str(e)}), 500

    


# Transfer Epins table

@epins.route('/v2/transfer/<user_id>', methods=['GET'])
@user_required
def get_pin_details(user_id):
    # sent_pin_details = []
    # received_pin_details = []

    # issued_pins = EPinTransaction.query.filter_by(sponsor_id=user_id, transaction_type='transfer').all()
    # for pin in issued_pins:
    #     latest_transaction = EPinTransaction.query.filter_by(epin_id=pin.epin_id).order_by(EPinTransaction.created_at.desc()).first()
    #     created_at_time = EPinTransaction.query.filter_by(epin_id=pin.epin_id, transaction_type='generate').first().created_at
    #     issued_to_name = UserModel.query.filter_by(user_id=pin.sponsor_id).first().name if pin.issued_to else None
    #     held_by_name = UserModel.query.filter_by(user_id=pin.user_id).first().name if pin.held_by else None
    #     used_by = UserModel.query.filter_by(user_id=latest_transaction.used_by).first().name if latest_transaction.used_by else None
    #     registered_to = UserModel.query.filter_by(user_id=latest_transaction.registered_to).first().name if latest_transaction.registered_to else None
    #     package = 'Registration Package' if pin.pin_amount == 500 else 'User Package'
    #     sent_pin_details.append({
    #         'pin_id': pin.pin,
    #         'amount': pin.pin_amount,
    #         'package': package,
    #         'transferred_from': issued_to_name,
    #         'transferred_to': held_by_name,
    #         'used_by': used_by,
    #         'registered_to': registered_to,
    #         'created_at': created_at_time.strftime("%Y-%m-%d %H:%M:%S"),
    #         'transfer_at': latest_transaction.created_at.strftime("%Y-%m-%d %H:%M:%S") if latest_transaction else None
    #     })

    # received_pins = EPinTransaction.query.filter_by(user_id=user_id, transaction_type='transfer').all()
    # for pin in received_pins:
    #     latest_transaction = EPinTransaction.query.filter_by(epin_id=pin.epin_id).order_by(EPinTransaction.created_at.desc()).first()
    #     created_at_time = EPinTransaction.query.filter_by(epin_id=pin.epin_id, transaction_type='generate').first().created_at
    #     issued_to_name = UserModel.query.filter_by(user_id=pin.sponsor_id).first().name if pin.issued_to else None
    #     held_by_name = UserModel.query.filter_by(user_id=pin.user_id).first().name if pin.held_by else None
    #     used_by = UserModel.query.filter_by(user_id=latest_transaction.used_by).first().name if latest_transaction.used_by else None
    #     registered_to = UserModel.query.filter_by(user_id=latest_transaction.registered_to).first().name if latest_transaction.registered_to else None
    #     package = 'Registration Package' if pin.pin_amount == 500 else 'User Package'
    #     received_pin_details.append({
    #         'pin_id': pin.pin,
    #         'amount': pin.pin_amount,
    #         'package': package,
    #         'transferred_from': issued_to_name,
    #         'transferred_to': held_by_name,
    #         'used_by': used_by,
    #         'registered_to': registered_to,
    #         'created_at': created_at_time.strftime("%Y-%m-%d %H:%M:%S"),
    #         'transfer_at': latest_transaction.created_at.strftime("%Y-%m-%d %H:%M:%S") if latest_transaction else None
    #     })
    try:
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        transaction_type = request.args.get('type')


        transfer_pin = get_transfer_epin_details(user_id=user_id, per_page=per_page, page=page, from_date=from_date, to_date=to_date, transaction_type=transaction_type)
        if transfer_pin:
            return transfer_pin
        else:
            return jsonify({'message': 'No transfer EPins '}), 200
    except Exception as e:
        return jsonify({'error': 'An error occurred while transferring epin', 'details': str(e)}), 500


    # return jsonify({'sent_pin_details': sent_pin_details, 'received_pin_details': received_pin_details})


# pin to register user


@epins.route('/register_user_for_epin', methods=['POST'])
@user_required
def register_user_for_epin():
    data = request.json
    user_id = data.get('user_id')
    epin_id = data.get('pin')
    name = data.get('name')
    phone = data.get('phone')

    existing_user = UserModel.query.filter_by(phone=phone).first()
    if existing_user:
        return jsonify({'error': 'User with this phone number already exists'}), 409

    try:

        # user = UserModel(
        #     role='USER',
        #     user_status='ACTIVE',
        #     paid_status='UNPAID',
        #     name=name,
        #     phone=phone,
        #     pin_type='0 E-Pin',
        #     sponsor_id=user_id
        # )
        # user.password = epin_id
        # user.username = user.generate_username()
        # db.session.add(user)
        # db.session.commit()

        sponsor_id=user_id
        phone=phone
        
        name=name
        password = epin_id

        



        user = create_user_with_epin(epin=epin_id, sponsor_id=sponsor_id, phone=phone, name=name, password=password, role="USER")
        
        

        if user:
            new_user_id = user['user_id']
            print('New User:', new_user_id)
            return jsonify({'message': 'EPin registered successfully'})
        else:
            return jsonify({'error': 'EPin is not registration pin'}), 400


        # existing_path_user = UserMap.query.filter_by(user_id=user_id).first()
        # path = None
        # if existing_path_user:
        #     existing_path = existing_path_user.path
        #     path = f"{existing_path}{user_id}|" if existing_path else f"{user_id}|"
        
        # newUserPath = UserMap(user_id=new_user_id, sponsor_id=user_id, path=path)
        # db.session.add(newUserPath)
        # db.session.commit()

        # Handle UserTransaction logic here
        # existing_user = UserModel.query.filter_by(user_id=user_id).first()
        # sponsor_name = existing_user.name

        # epinUser = EPinTransaction.query.filter(
        #     EPinTransaction.user_id == user_id,
        #     EPinTransaction.pin == epin_id
        # ).order_by(desc(EPinTransaction.created_at)).first()

        # if not epinUser:
        #     return jsonify({'error': 'EPin not found with the provided user_id and pin combination'}), 404

        # created_at = datetime.now(pytz.timezone('Asia/Kolkata'))
        # user_transaction = UserTransaction(
        #     user_id=new_user_id,
        #     type='payment',
        #     category='Registration',
        #     amount='0.00',
        #     remark=f"Registered by {sponsor_name}",
        #     sponsor_id=user_id,
        #     date_time=created_at,
        #     status=None
        # )
        # db.session.add(user_transaction)
        # db.session.commit()

        # if epinUser.transaction_type != "registered" and phone is not None:
        #     transfer_epin = EPinTransaction(
        #         epin_id=epinUser.epin_id,
        #         transaction_type="registered",
        #         user_id=new_user_id,
        #         sponsor_id=epinUser.user_id,
        #         created_at=created_at,
        #         pin=epinUser.pin,
        #         pin_type=epinUser.pin_type,
        #         pin_amount=epinUser.pin_amount,
        #         issued_to=epinUser.issued_to,
        #         held_by=epinUser.held_by,
        #         used_by=epinUser.held_by,
        #         registered_to=new_user_id,
        #     )

        #     db.session.add(transfer_epin)
        #     db.session.commit()

        #     if epinUser.pin_type == '500 E-pin' or epinUser.pin_type == '2000 E-pin':
        #         epin_ids = epinUser.epin_id
        #         check_sponsor(new_user_id, user_id, epin_ids)

        

        # else:
        #     return jsonify({'error': 'EPin is not registration pin'}), 400

    except IntegrityError as e:
        db.session.rollback()
        print(e)
        return jsonify({'error': 'Database integrity error', 'details': str(e)}), 500
    
    except Exception as e:
        print(e)
        db.session.rollback()
        return jsonify({'error': 'An error occurred while registering user', 'details': str(e)}), 500

@epins.route('/v1/transactions/user/count/<user_id>', methods=['GET'])
@user_required
def get_epin_count(user_id):
    try:
        # used_count = db.session.query(func.count(func.distinct(EPinTransaction.epin_id))).\
        #     filter(EPinTransaction.issued_to == user_id, EPinTransaction.transaction_type == 'registered').scalar()
        
        # total_count = db.session.query(func.count(func.distinct(EPinTransaction.epin_id))).\
        #     filter(or_(EPinTransaction.issued_to == user_id, EPinTransaction.held_by == user_id)).scalar()
        
        # unused_count = total_count - used_count
        
        # epin_count = {
        #     'used_count': used_count,
        #     'unused_count': unused_count
        # }
        epin_count = get_epin_count_by_user(user_id)
        if epin_count :
            return jsonify(epin_count), 200
        else:
            return jsonify({'message': 'No  EPins '}), 200 
    except Exception as e:
        return jsonify({'error': str(e)}), 500

from sqlalchemy import desc, func, and_, select

@epins.route('/v1/transactions/user/<user_id>', methods=['GET'])
@user_required
def get_transactions_by_user(user_id):
    try:
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        
        # Query to get the latest transactions based on epin_id and created_at
        # subquery = db.session.query(
        #     EPinTransaction.epin_id,
        #     func.max(EPinTransaction.created_at).label('latest_created_at')
        # ).group_by(EPinTransaction.epin_id).subquery()

        # # Main query to fetch transactions, ordered by transaction_type descending
        # transactions = db.session.query(EPinTransaction).\
        #     join(subquery, and_(
        #         EPinTransaction.epin_id == subquery.c.epin_id,
        #         EPinTransaction.created_at == subquery.c.latest_created_at
        #     )).\
        #     filter(or_(EPinTransaction.issued_to == user_id, EPinTransaction.held_by == user_id)).\
        #     order_by(desc(EPinTransaction.transaction_type))

        # # Paginate the results
        # paginated_transactions = transactions.paginate(page=page, per_page=per_page)

        # # Serialize paginated transactions to JSON
        # serialized_transactions = [transaction.serialize() for transaction in paginated_transactions.items]

        # # # Return JSON response with paginated data
        
        # # response = get_paginated_transactions(user_id=user_id, per_page=per_page, page=page, from_date=from_date, to_date=to_date)
        # # return response
        # return jsonify({
        #     'transactions': serialized_transactions,
        #     'page': paginated_transactions.page,
        #     'total_pages': paginated_transactions.pages,
        #     'total_items': paginated_transactions.total
        # }), 200

        response = get_paginated_transactions(user_id=user_id, per_page=per_page, page=page, from_date=from_date, to_date=to_date)
        return response

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# @epins.route('/v1/transfer/transactions/user/<user_id>', methods=['GET'])
# def get_transfer_transactions_by_user(user_id):
#     try:
#         subquery = db.session.query(
#             EPinTransaction.epin_id,
#             func.max(EPinTransaction.created_at).label('latest_created_at')
#         ).group_by(EPinTransaction.epin_id).subquery()

#         transactions = db.session.query(EPinTransaction).\
#             join(subquery, and_(
#                 EPinTransaction.epin_id == subquery.c.epin_id,
#                 EPinTransaction.created_at == subquery.c.latest_created_at
#             )).\
#             filter(and_(
#                 EPinTransaction.transaction_type == 'transfer',
#                 EPinTransaction.user_id == user_id
#             )).\
#             order_by(desc(EPinTransaction.created_at)).all()
        
#         serialized_transactions = [transaction.serialize() for transaction in transactions]
#         return jsonify(serialized_transactions), 200
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500




# @epins.route('/transactions/latest/<user_id>', methods=['GET'])
# def get_latest_transfer_transactions(user_id):
#     try:
#         # Subquery to find the latest 'transfer' transaction for each unique pin by the specified user_id
#         subquery = db.session.query(
#             EPinTransaction.epin_id,
#             func.max(EPinTransaction.created_at).label('latest_created_at')
#         ).filter(
#             EPinTransaction.sponsor_id == user_id,
#             EPinTransaction.transaction_type == 'transfer'
#         ).group_by(EPinTransaction.epin_id).subquery()

#         # Query to retrieve the latest 'transfer' transaction for each unique pin by the specified user_id
#         transactions = db.session.query(EPinTransaction).\
#             join(subquery, and_(
#                 EPinTransaction.epin_id == subquery.c.epin_id,
#                 EPinTransaction.created_at == subquery.c.latest_created_at
#             )).filter(
#                 ~EPinTransaction.used_by.contains(user_id)  # Exclude transactions where user_id is present in used_by
#             ).all()

#         # Serialize the transactions into a JSON format
#         serialized_transactions = [transaction.serialize() for transaction in transactions]
        
#         # Return the serialized transactions as JSON response
#         return jsonify(serialized_transactions), 200
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
