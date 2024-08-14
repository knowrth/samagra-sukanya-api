from models.db import db
from datetime import datetime, timedelta
from decimal import Decimal
import pytz
from sqlalchemy.sql import text
from sqlalchemy import  func, or_, select, and_, desc
from math import ceil
from models.UserModels import UserMap, UserModel, UserTransaction
from models.EpinModels import EPinTransaction, RegisterEPin
from models.ReferencModels import income_levels

from flask import jsonify

def create_user_with_epin(epin, sponsor_id, phone, role, password, name="Unknown",  
                paid_status="UNPAID", user_status="ACTIVE"):
    new_user=None
    
    with db.session() as session:
        #get epin
        stmt = db.Select(EPinTransaction).filter_by(pin=epin) 
        epin_transaction = session.execute(stmt).scalars().first()
        if epin_transaction is None or epin_transaction.transaction_type !="generate":
            return None
        
        # get sponsor
        stmt = db.Select(UserModel).filter_by(user_id=sponsor_id)
        sponsor = session.execute(stmt).scalars().first()
        if sponsor is None:
            return None
        
        # create user
        user = UserModel(sponsor_id=sponsor_id,role="USER", phone=phone, name=name,
                                    paid_status=paid_status, user_status=user_status, password=password)
        user.username = user.generate_username()
        session.add(user)
        # session.commit()

        # update user map
        stmt = db.Select(UserMap).filter_by(user_id=sponsor_id)
        sponsor_map = session.execute(stmt).scalars().first()
        path = "" if sponsor_map.path is None else sponsor_map.path
        user_map = UserMap(user_id=user.user_id, sponsor_id=sponsor_id, path=path + sponsor_id + '|' )
        session.add(user_map)
        # session.commit()
        epin_user = str(user.user_id)
        # update epin-transaction
        created_at = datetime.now(pytz.timezone('Asia/Kolkata'))
        new_epin = EPinTransaction(epin_id=epin_transaction.epin_id, 
                                transaction_type="registered",
                                user_id=epin_user,
                                sponsor_id=sponsor_id,
                                pin=epin_transaction.pin,
                                pin_type=epin_transaction.pin_type,
                                pin_amount=epin_transaction.pin_amount,
                                created_at= created_at,
                                issued_to=epin_transaction.issued_to,
                                held_by=epin_transaction.held_by,
                                used_by=epin_transaction.held_by,
                                registered_to=epin_user)
        session.add(new_epin)
        # session.commit()

        #user Transaction
        user_transaction = UserTransaction(
            user_id= user.user_id,
            type='payment',
            category='Registration',
            amount='0.00',
            remark=f"Registered by {sponsor.name}",
            sponsor_id=sponsor_id,
            date_time= created_at,
            status=None,
        )
        session.add(user_transaction)
        # session.commit()

        if epin_transaction.pin_type in ['500 E-pin', '2000 E-pin']:
            transactions = []
            created_at = datetime.now(pytz.timezone('Asia/Kolkata'))
            sponsors = user_map.path.split('|')[::-1]
            sponsors = [sponsor for sponsor in sponsors if sponsor.strip()]
            for i in range(len(sponsors)):
                if sponsors[i] == "":
                    continue
                rate = income_levels[8]['rate'] if i >= 8 else income_levels[i]['rate']
                
                commission = UserTransaction(
                    user_id=sponsors[i],
                    type='Receipt',  
                    category='Commission',
                    amount=str(rate),
                    remark=f"Level Income {i+1} from {name}",
                    date_time=created_at,
                    sponsor_id= None,
                    status=None
                    )
                
                stmt = db.Select(RegisterEPin).filter_by(user_id=user.user_id).order_by(text('date_time desc'))
                latest_transaction = session.execute(stmt).scalars().first()

                # latest_transaction = RegisterEPin.query.filter_by(user_id=user.user_id).order_by(desc(RegisterEPin.date_time)).first()

                if latest_transaction:
                    pre_wallet = Decimal(latest_transaction.after_wallet)
                else:
                    pre_wallet = Decimal(0)

                after_wallet = pre_wallet + rate

                register_transaction = RegisterEPin(
                    user_id=sponsors[i],
                    epin= epin_transaction.epin_id,
                    commission=str(rate), 
                    level= f"Level-{i+1}",
                    status= 'ISSUED',
                    member= user.name,
                    trans_type='CR',
                    pre_wallet=str(pre_wallet),
                    after_wallet=str(after_wallet),
                    log_type='Level Income ',  
                    date_time= created_at,
                    trans_note=f"Level Income {i+1} from {user.name}"
                )
                session.add(commission)
                session.add(register_transaction)
        session.commit()
        new_user = user.to_dict()
    return new_user
                
def epin_transfer_epin(pin, user_id, phone, name):
    new_transfer_pin=None
    with db.session() as session:
            #check user availability
            stmt = db.Select(UserModel).filter_by(phone=phone, name=name)
            user = session.execute(stmt).scalars().first()
            if user is  None:
                return jsonify({'message': 'User not found with the provided phone and name'}), 404
            
            # pin availability
            stmt = db.Select(EPinTransaction).filter_by(pin=pin).order_by(text('created_at desc'))
            epin = session.execute(stmt).scalars().first()
            if epin is None:
                return jsonify({'message': 'EPin transaction not found'}), 404
            
            # pin accountability
            if epin.user_id != user_id:
                return jsonify({'message': 'EPin is already transferred to another user'}), 400
            
            # pin transfer
            if  epin.transaction_type != "registered":
                created_at = datetime.now(pytz.timezone('Asia/Kolkata'))
                transfer_epin = EPinTransaction(
                epin_id=epin.epin_id,
                transaction_type="transfer",
                user_id=user.user_id,
                sponsor_id=epin.user_id,
                created_at=created_at,
                pin=epin.pin,
                pin_type=epin.pin_type,
                pin_amount=epin.pin_amount,
                issued_to=epin.issued_to,
                held_by=user.user_id,
            )

            session.add(transfer_epin)
            session.commit()
            new_transfer_pin = epin.to_dict()
                
    return new_transfer_pin

# import logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

def multiple_epin_transfer(pin, user_id, phone, name):
    new_transfer_pin = None
    try:
        with db.session() as session:
            # Check user availability
            stmt = db.select(UserModel).filter_by(phone=phone, name=name)
            user = session.execute(stmt).scalars().first()
            
            if user is None:
                # logger.warning(f"User not found with phone: {phone} and name: {name}")
                return jsonify({'message': 'User not found with the provided phone and name'}), 404
            
            pin_list = [x.strip() for x in pin.split(',')]
            for x in pin_list:
                # logger.info(f"Processing PIN: {x}")

                # Check pin availability
                stmt = db.select(EPinTransaction).filter_by(pin=x).order_by(text('created_at desc'))
                epin = session.execute(stmt).scalars().first()
                
                if epin is None:
                    # logger.warning(f"EPin transaction not found for PIN: {x}")
                    return jsonify({'message': 'EPin transaction not found'}), 404
                
                # Check pin accountability
                if epin.user_id != user_id:
                    # logger.warning(f"EPin with PIN: {x} is already transferred to another user (user_id: {epin.user_id})")
                    return jsonify({'message': 'EPin is already transferred to another user'}), 400

                # Pin transfer
                if epin.transaction_type != "registered":
                    created_at = datetime.now(pytz.timezone('Asia/Kolkata'))
                    transfer_epin = EPinTransaction(
                        epin_id=epin.epin_id,
                        transaction_type="transfer",
                        user_id=user.user_id,
                        sponsor_id=epin.user_id,
                        created_at=created_at,
                        pin=epin.pin,
                        pin_type=epin.pin_type,
                        pin_amount=epin.pin_amount,
                        issued_to=epin.issued_to,
                        held_by=user.user_id,
                    )
                    
                    session.add(transfer_epin)
                    session.commit()
                    # logger.info(f"Added new transfer EPin with PIN: {x}")

            
            new_transfer_pin = epin.to_dict()
            # logger.info(f"EPin transfer completed for PIN: {x}")
            
    except Exception as e:
        # logger.error(f"An error occurred during EPin transfer: {e}")
        return jsonify({'message': 'An error occurred during EPin transfer'}), 500

    return jsonify(new_transfer_pin)


def get_transfer_epin_details(user_id, transaction_type, page, per_page, from_date=None, to_date=None):
    sent_pin_details = []
    received_pin_details = []

    with db.session() as session:
        # Define base query
        base_query = db.Select(EPinTransaction)
        
        if transaction_type not in ['sent', 'received']:
            return jsonify({'error': 'Invalid transaction type. Must be "sent" or "received".'}), 400
        
        # Filter by transaction type and user
        if transaction_type == 'sent':
            base_query = base_query.where(
                and_(EPinTransaction.sponsor_id == user_id, EPinTransaction.transaction_type == 'transfer')
            )
        elif transaction_type == 'received':
            base_query = base_query.where(
                and_(EPinTransaction.user_id == user_id, EPinTransaction.transaction_type == 'transfer')
            )

        # Apply date filters if provided
        if from_date:
            from_date = datetime.strptime(from_date, '%Y-%m-%d')
            base_query = base_query.where(EPinTransaction.created_at >= from_date)
        if to_date:
            to_date = datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1) - timedelta(milliseconds=1)
            base_query = base_query.where(EPinTransaction.created_at <= to_date)
        
        # Pagination
        offset = (page - 1) * per_page
        paginated_query = base_query.order_by(desc(EPinTransaction.created_at)).limit(per_page).offset(offset)

        # Fetch paginated results
        pins = session.execute(paginated_query).scalars().all()
        
        for pin in pins:
            # Fetch latest transaction and creation time
            latest_stmt = select(EPinTransaction).where(EPinTransaction.epin_id == pin.epin_id).order_by(desc(EPinTransaction.created_at))
            latest_transaction = session.execute(latest_stmt).scalars().first()

            created_stmt = select(EPinTransaction).where(and_(EPinTransaction.epin_id == pin.epin_id, EPinTransaction.transaction_type == 'generate'))
            created = session.execute(created_stmt).scalars().first()
            created_at_time = created.created_at if created else None

            # Fetch names
            issued_to_name = get_user_name(pin.sponsor_id)
            held_by_name = get_user_name(pin.user_id)
            used_by_name = get_user_name(latest_transaction.used_by) if latest_transaction and latest_transaction.used_by else None
            registered_to_name = get_user_name(latest_transaction.registered_to) if latest_transaction and latest_transaction.registered_to else None

            package = 'Registration Package' if pin.pin_amount == 500 else 'User Package'

            # Append details based on transaction type
            if transaction_type == 'sent':
                sent_pin_details.append({
                    'pin_id': pin.pin,
                    'amount': pin.pin_amount,
                    'package': package,
                    'transferred_from': issued_to_name,
                    'transferred_to': held_by_name,
                    'used_by': used_by_name,
                    'registered_to': registered_to_name,
                    'created_at': created_at_time.strftime("%Y-%m-%d %H:%M:%S") if created_at_time else None,
                    'transfer_at': latest_transaction.created_at.strftime("%Y-%m-%d %H:%M:%S") if latest_transaction else None
                })
            elif transaction_type == 'received':
                received_pin_details.append({
                    'pin_id': pin.pin,
                    'amount': pin.pin_amount,
                    'package': package,
                    'transferred_from': issued_to_name,
                    'transferred_to': held_by_name,
                    'used_by': used_by_name,
                    'registered_to': registered_to_name,
                    'created_at': created_at_time.strftime("%Y-%m-%d %H:%M:%S") if created_at_time else None,
                    'transfer_at': latest_transaction.created_at.strftime("%Y-%m-%d %H:%M:%S") if latest_transaction else None
                })

        # Count total records
        total_count_stmt = select(func.count()).select_from(base_query.subquery())
        total_count = session.execute(total_count_stmt).scalar()
        total_pages = ceil(total_count / per_page)

        return jsonify({
            'sent_pin_details': sent_pin_details if transaction_type == 'sent' else [],
            'received_pin_details': received_pin_details if transaction_type == 'received' else [],
            'page': page,
            'total_pages': total_pages,
            'total_items': total_count
        })


def get_user_name(user_id):
    with db.session() as session:
        if user_id:
            stmt = db.Select(UserModel).filter_by(user_id=user_id)
            user = session.execute(stmt).scalars().first()
            return user.name if user else None
    return None



def get_epin_count_by_user(user_id):
    with db.session() as session:
        # Count used epins
        used_count = session.query(func.count(func.distinct(EPinTransaction.epin_id))).\
            filter(EPinTransaction.issued_to == user_id, EPinTransaction.transaction_type == 'registered').scalar()
        
        total_count = session.query(func.count(func.distinct(EPinTransaction.epin_id))).\
            filter(or_(EPinTransaction.issued_to == user_id, EPinTransaction.held_by == user_id)).scalar()
        
        unused_count = total_count - used_count
        
        epin_count = {
            'used_count': used_count,
            'unused_count': unused_count
        }

        return epin_count


def update_user(user_id,password=None, name=None):
    updated_user = None
    with db.session() as session:
        stmt = db.Select(UserModel).filter_by(user_id=user_id)
        user = session.execute(stmt).scalars().first()
        if user :
            user.name = name
        session.add(user)
        session.commit()
        updated_user = dict(user)
    return updated_user

def get_user_by_id(user_id):
    selected_user = None
    with db.session() as session:
        stmt = db.Select(UserModel).filter_by(user_id=user_id)
        user = session.execute(stmt).scalars.first()
        if user:
            selected_user = dict(user)
    selected_user

def get_paginated_transactions(user_id, page, per_page, from_date=None, to_date=None):
    with db.session() as session:
        subquery = (
            select(
                EPinTransaction.epin_id,
                func.max(EPinTransaction.created_at).label('latest_created_at')
            )
            .group_by(EPinTransaction.epin_id)
            .order_by(desc(func.max(EPinTransaction.created_at)))
            .subquery()
        )
    
        # Main query to fetch transactions
        transactions_stmt = (
            select(EPinTransaction)
            .join(subquery, and_(
                EPinTransaction.epin_id == subquery.c.epin_id,
                EPinTransaction.created_at == subquery.c.latest_created_at
            ))
            .where(
                or_(EPinTransaction.issued_to == user_id, EPinTransaction.held_by == user_id)
            )
            .order_by(desc(subquery.c.latest_created_at))
        )
        
        if from_date:
            transactions_stmt = transactions_stmt.where(EPinTransaction.created_at >= datetime.strptime(from_date, '%Y-%m-%d'))
        if to_date:
            end_of_day = datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1) - timedelta(milliseconds=1)
            transactions_stmt = transactions_stmt.where(EPinTransaction.created_at <= end_of_day)
        
        offset = (page - 1) * per_page
        
        # Subquery for counting total transactions
        total_stmt = (
            select(func.count())
            .select_from(
                select(EPinTransaction)
                .join(subquery, and_(
                    EPinTransaction.epin_id == subquery.c.epin_id,
                    EPinTransaction.created_at == subquery.c.latest_created_at
                ))
                .where(
                    or_(EPinTransaction.issued_to == user_id, EPinTransaction.held_by == user_id)
                )
                .where(
                    EPinTransaction.created_at >= (datetime.strptime(from_date, '%Y-%m-%d') if from_date else datetime.min)
                )
                .where(
                    EPinTransaction.created_at <= (end_of_day if to_date else datetime.max)
                )
            )
        )
    
        total_count = session.execute(total_stmt).scalar()

        limit_stmt = transactions_stmt.limit(per_page).offset(offset)
        transactions = session.execute(limit_stmt).scalars().all()

        total_pages = ceil(total_count / per_page)

        serialized_transactions = [transaction.serialize() for transaction in transactions]

        return jsonify({
            'transactions': serialized_transactions,
            'page': (offset // per_page) + 1,
            'total_pages': total_pages,
            'total_items': total_count
        })
    




















    # # Execute the query to get the total count of items
    # total_count_query = (
    #     select([func.count()])
    #     .select_from(
    #         select([EPinTransaction.epin_id])
    #         .select_from(
    #             EPinTransaction.join(
    #                 subquery,
    #                 and_(
    #                     EPinTransaction.epin_id == subquery.c.epin_id,
    #                     EPinTransaction.created_at == subquery.c.latest_created_at
    #                 )
    #             )
    #         )
    #         .where(
    #             or_(
    #                 EPinTransaction.issued_to == user_id,
    #                 EPinTransaction.held_by == user_id
    #             )
    #         )
    #     )
    # )
    
    #     total_count = session.execute(total_count_query).scalar()
    
    #     # Apply pagination
    #     offset = (page - 1) * per_page
    #     paginated_query = main_query.limit(per_page).offset(offset)
    
    #     # Execute the paginated query
    #     with db.session() as session:
    #         result = session.execute(paginated_query)
    #         transactions = result.fetchall()
    
    #         # Serialize the results
    #         serialized_transactions = [dict(row) for row in transactions]
    
    #         # Calculate total pages
    #         total_pages = (total_count + per_page - 1) // per_page
    
    #         # Return JSON response with paginated data
    #         return jsonify({
    #             'transactions': serialized_transactions,
    #             'page': page,
    #             'total_pages': total_pages,
    #             'total_items': total_count
    #         })
