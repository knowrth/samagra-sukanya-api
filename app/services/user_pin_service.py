from models.db import db
import datetime
from decimal import Decimal
import pytz
from sqlalchemy.sql import text
from sqlalchemy import  func, or_, select

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
        created_at = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
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
            created_at = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
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
                created_at = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
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


def multiple_epin_transfer(pin, user_id, phone, name):
    new_transfer_pin=None
    with db.session() as session:
            #check user availability
            stmt = db.Select(UserModel).filter_by(phone=phone, name=name)
            user = session.execute(stmt).scalars().first()
            if user is  None:
                return jsonify({'message': 'User not found with the provided phone and name'}), 404
            
            pin_list = pin.split(',')
            for x in pin_list:
                # pin availability
                stmt = db.Select(EPinTransaction).filter_by(pin=x).order_by(text('created_at desc'))
                epin = session.execute(stmt).scalars().first()
                if epin is None:
                    return jsonify({'message': 'EPin transaction not found'}), 404
                
                # pin accountability
                if epin.user_id != user_id:
                    return jsonify({'message': 'EPin is already transferred to another user'}), 400
                
                # pin transfer
                if  epin.transaction_type != "registered":
                    created_at = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
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



def get_transfer_epin_details(user_id):
    sent_pin_details = []
    received_pin_details = []
    with db.session() as session:
    # Fetch all issued pins
        stmt = db.Select(EPinTransaction).filter_by(sponsor_id=user_id, transaction_type='transfer')
        issued_pins = session.execute(stmt).scalars().all()

            # Process issued pins
        for pin in issued_pins:
                # Fetch latest transaction and creation time
                latest_stmt = db.Select(EPinTransaction).filter_by(epin_id=pin.epin_id).order_by(text('created_at desc'))
                latest_transaction = session.execute(latest_stmt).scalars().first()

                created_stmt = db.Select(EPinTransaction).filter_by(epin_id=pin.epin_id, transaction_type='generate')
                created = session.execute(created_stmt).scalars().first()
                created_at_time = created.created_at if created else None

                # Fetch names
                issued_to_name = get_user_name(pin.sponsor_id)
                held_by_name = get_user_name(pin.user_id)
                used_by_name = get_user_name(latest_transaction.used_by) if latest_transaction and latest_transaction.used_by else None
                registered_to_name = get_user_name(latest_transaction.registered_to) if latest_transaction and latest_transaction.registered_to else None

                package = 'Registration Package' if pin.pin_amount == 500 else 'User Package'

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

            # Fetch all received pins
        stmt = db.Select(EPinTransaction).filter_by(user_id=user_id, transaction_type='transfer')
        received_pins = session.execute(stmt).scalars().all()

            # Process received pins
        for pin in received_pins:
                # Fetch latest transaction and creation time
                latest_stmt = db.Select(EPinTransaction).filter_by(epin_id=pin.epin_id).order_by(text('created_at desc'))
                latest_transaction = session.execute(latest_stmt).scalars().first()

                created_stmt = db.Select(EPinTransaction).filter_by(epin_id=pin.epin_id, transaction_type='generate')
                created = session.execute(created_stmt).scalars().first()
                created_at_time = created.created_at if created else None

                # Fetch names
                issued_to_name = get_user_name(pin.sponsor_id)
                held_by_name = get_user_name(pin.user_id)
                used_by_name = get_user_name(latest_transaction.used_by) if latest_transaction and latest_transaction.used_by else None
                registered_to_name = get_user_name(latest_transaction.registered_to) if latest_transaction and latest_transaction.registered_to else None

                package = 'Registration Package' if pin.pin_amount == 500 else 'User Package'

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


    return jsonify({'sent_pin_details': sent_pin_details, 'received_pin_details': received_pin_details})


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


# def list_user(
#     filter_by:dict= None, 
#     limit:int=10, 
#     offset:int=0, 
#     order_by:list= None
# ):
#     '''
#     filter_by = {
#         "name": "value1",
#         "phone": "value2"
#     }
#     order_by = ["user_id", "name desc"]
#     '''
#     filters = []
#     with db.session() as session:
#         # Build the base query
#         stmt = select(UserModel)
        
#         # Apply filters
#         if filter_by:
#             filters = [
#                 getattr(UserModel, col).ilike(f'%{val}%') 
#                 for col, val in filter_by.items()
#             ]
#             stmt = stmt.filter(or_(*filters))

#         # Apply ordering
#         if order_by:
#             order_by_clauses = []
#             for ob in order_by:
#                 if ' desc' in ob:
#                     col = ob.replace(' desc', '')
#                     order_by_clauses.append(getattr(UserModel, col).desc())
#                 else:
#                     order_by_clauses.append(getattr(UserModel, ob))
#             stmt = stmt.order_by(*order_by_clauses)

#         # Apply pagination
#         stmt = stmt.limit(limit).offset(offset)

#         # Execute the statement and fetch results
#         result = session.execute(stmt).scalars().fetchall()
        
#         # Fetch total count separately
#         # count_stmt = select([func.count(UserModel.user_id)]).select_from(UserModel)

#         # if filters:
#         #     count_stmt = count_stmt.filter(or_(*filters))
#         # total_users = session.execute(count_stmt)
#         # total_user = total_users.scalar()
        
#         # Convert results to a list of dictionaries
#         user_list = [dict(user.__dict__) for user in result]
    
#     return {
#         'users': user_list,
#         'total_users': result.count,
#         'current_page': (offset // limit) + 1,
#         'total_pages': (result // limit) + (1 if result % limit > 0 else 0)
#     }



# User details

def create_user_details(sponsor_id, username, role, image_url=None, title=None, 
                gender=None, dob=None, father_name=None, house_telephone=None,
                email=None, country=None, state=None, city=None, pin_code=None, address=None,
                marital_status=None):
    new_user=None
    with db.sesssion(expire_on_commit=False) as session:
    # Check if sponsor exists
        if role == "USER":
            stmt = db.Select(UserModel).filter_by(user_id=sponsor_id)
            sponsor = session.execute(stmt).scalars.first()
            if sponsor is not None:
                user = UserModel(sponsor_id=sponsor_id,role="USER")
                session.add(user)
                session.commit()
                new_user = dict(user)
    return new_user