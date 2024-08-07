from models.db import db
from sqlalchemy import  func, or_, select, desc, and_
from models.UserModels import  UserModel, UserTransaction
from models.EpinModels import EPinTransaction, RegisterEPin
from models.ReferencModels import SupportTicket
from typing import List
from flask import jsonify
import logging
from math import ceil
logging.basicConfig(level=logging.DEBUG)
from typing import List, Dict


def get_user_tables(filter_by: Dict[str, str] = None, limit: int = 10, offset: int = 0, order_by: List[str] = None) -> List[Dict]:
    '''
    filter_by = {
        "col_name_1": "value1",
        "col_name_2": "value2"
    }
    order_by = ["col_1", "col2 desc"]
    '''
    user_list = []
    with db.session() as session:
        # logging.debug(f'filter_by: {filter_by}')

        count_stmt = db.Select(func.count()).select_from(UserModel)
        
        # users count 
        if filter_by:
            filters = []
            for column_name, value in filter_by.items():
                if hasattr(UserModel, column_name):
                    column = getattr(UserModel, column_name)
                    filters.append(column.ilike(f'%{value}%'))
            if filters:
                count_stmt = count_stmt.where(or_(*filters))

        total_count = session.execute(count_stmt).scalar()


        stmt = db.Select(UserModel)
        
        # Apply flexible filtering for multiple columns
        if filter_by:
            filters = []
            for column_name, value in filter_by.items():
                if hasattr(UserModel, column_name):
                    column = getattr(UserModel, column_name)
                    filters.append(column.ilike(f'%{value}%'))
            if filters:
                stmt = stmt.where(or_(*filters))
            # logging.debug(f'stmt with filter: {stmt}')

        if order_by:
            order_clauses = []
            for order in order_by:
                if ' desc' in order:
                    column_name = order.replace(' desc', '')
                    order_clauses.append(getattr(UserModel, column_name).desc())
                else:
                    order_clauses.append(getattr(UserModel, order))
            stmt = stmt.order_by(*order_clauses)
        
        stmt = stmt.limit(limit).offset(offset)
        
        result = session.execute(stmt).scalars().all()
        
        # Convert result to list of dictionaries
        user_list = [user_to_dict(row) for row in result]
    total_pages = ceil(total_count / limit)

    return jsonify({
            'users': user_list,
            'total_users': total_count,
            'current_page':  (offset // limit) + 1,
            'total_pages': total_pages
        })

def user_to_dict(user):
    return {
        'user_id': user.user_id,
            'email': user.email,
            'role': user.role,
            'name': user.name,
            'phone': user.phone,
            'paid_status': user.paid_status,
            'username': user.username,
            'amount_paid': user.amount_paid
    }

def get_commission_tables(limit: int = 10, offset: int = 0):
    with db.session() as session:
        # count total commission 
        count_stmt = (
            select(func.count())
            .select_from(RegisterEPin)
            .join(UserModel, RegisterEPin.user_id == UserModel.user_id)
        )

        total_count = session.execute(count_stmt).scalar()

        # list of all commissions
        stmt = (
            select(RegisterEPin, UserModel.username, UserModel.name)
            .join(UserModel, RegisterEPin.user_id == UserModel.user_id)
            .order_by(desc(RegisterEPin.date_time))
            .limit(limit)
            .offset(offset)
        )

        results = session.execute(stmt).all()

        transactions = [
            {
                'user_email': result[1],  # username
                'name': result[2],        # name
                'amount': result[0].commission,
                'pre_wallet_amount': result[0].pre_wallet,
                'after_wallet_amount': result[0].after_wallet,
                'transaction_mode_type': result[0].trans_type,
                'logType': result[0].log_type,
                'transaction_note': result[0].trans_note,
                'timestamp': result[0].date_time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            for result in results
        ]

        total_pages = ceil(total_count / limit)

    return jsonify({
            'transactions': transactions,
            'total_users': total_count,
            'current_page':  (offset // limit) + 1,
            'total_pages': total_pages
        })

def get_pending_withdrawals(page: int, per_page: int):
    with db.session() as session:


        # withdrawal count
        count_stmt = (
            db.Select(func.count())
            .select_from(UserTransaction)
            .where(UserTransaction.status == "Pending")
        )
        total_count = session.execute(count_stmt).scalar()

        # user, phone for all withdrawals
        stmt = (
            db.Select(
                UserTransaction,
                UserModel.username,
                UserModel.name,
                UserModel.phone
            )
            .join(UserModel, UserTransaction.user_id == UserModel.user_id)
            .where(UserTransaction.status == "Pending")
            .order_by(UserTransaction.date_time)
            .limit(per_page)
            .offset((page - 1) * per_page)
        )

        results = session.execute(stmt).all()

        withdrawals = [
            {
                'user_id': result[0].user_id,
                'name': result[2],  
                'username': result[1],  
                'phone': result[3],  
                'amount': result[0].amount,
                'remark': result[0].remark,
                'date_time': result[0].date_time.strftime('%Y-%m-%d %H:%M:%S.%f'), 
            }
            for result in results
        ]

        total_pages = ceil(total_count / per_page)

    return jsonify({
        'withdrawals': withdrawals,
        'total_pages': total_pages,
        'current_page': page,
        'total_withdrawals': total_count
    })

def get_support_tickets(page: int, per_page: int):
    with db.session() as session:

            
            count_stmt = (
                db.Select(func.count())
                .select_from(SupportTicket)
                .where(SupportTicket.query_status == "Open")
            )
            total_count = session.execute(count_stmt).scalar()

            
            stmt = (
                db.Select(
                    SupportTicket,
                    UserModel.user_id,
                    UserModel.name,
                    UserModel.username,
                    UserModel.phone
                )
                .join(UserModel, SupportTicket.user_id == UserModel.user_id)
                .where(SupportTicket.query_status == "Open")
                .order_by(SupportTicket.date_time)
                .limit(per_page)
                .offset((page - 1) * per_page)
            )
            
            results = session.execute(stmt).all()
            
            supports = [
                {
                    'user_id': result[1],  
                    'name': result[2],     
                    'username': result[3], 
                    'phone': result[4],    
                    'query_type': result[0].query_type,
                    'query_title': result[0].query_title,
                    'query_desc': result[0].query_desc,
                    'query_status': result[0].query_status,
                    'date_time': result[0].date_time.strftime('%Y-%m-%d %H:%M:%S.%f')  # Format datetime
                }
                for result in results
            ]

            total_pages = (total_count + per_page - 1) // per_page

            return jsonify({
                'supports': supports,
                'total_pages': total_pages,
                'current_page': page,
                'total_supports': total_count
            })

def get_user_transaction_table(user_id):
    with db.session() as session:
            stmt = (
                db.Select(UserTransaction)
                .where(UserTransaction.user_id == user_id)
                .where(UserTransaction.category != 'Commission')
            )
            
            
            results = session.execute(stmt).scalars().all()
            
        
            transactions = [{
                'id': result.id,
                'type': result.type,
                'category': result.category,
                'amount': result.amount,
                'remark': result.remark,
                'date_time': result.date_time.strftime('%Y-%m-%d %H:%M:%S'), 
                'sponsor_id': result.sponsor_id
            } for result in results]
            
            
            if transactions:
                return jsonify({'transactions': transactions}), 200
            else:
                return jsonify({'message': 'No transactions found for the user'}), 404

def pin_package_counts():
    with db.session() as session:
            # Count 500 pins
            user_package_pins_stmt = (
                db.Select(func.count().label('count'))
                .select_from(select(EPinTransaction.pin).distinct().where(EPinTransaction.pin_type == '500 E-pin'))
            )
            user_package_pins_count = session.execute(user_package_pins_stmt).scalar()

            user_package_used_stmt = (
                db.Select(func.count().label('count'))
                .select_from(EPinTransaction)
                .where(EPinTransaction.pin_type == '500 E-pin')
                .where(EPinTransaction.used_by.isnot(None))
            )
            user_package_used_count = session.execute(user_package_used_stmt).scalar()
            user_package_unused_count = user_package_pins_count - user_package_used_count

            # Count 0 pins
            registration_package_pins_stmt = (
                db.Select(func.count().label('count'))
                .select_from(select(EPinTransaction.pin).distinct().where(EPinTransaction.pin_type == '0 E-pin'))
            )
            registration_package_pins_count = session.execute(registration_package_pins_stmt).scalar()

            registration_package_used_stmt = (
                db.Select(func.count().label('count'))
                .select_from(EPinTransaction)
                .where(EPinTransaction.pin_type == '0 E-pin')
                .where(EPinTransaction.used_by.isnot(None))
            )
            registration_package_used_count = session.execute(registration_package_used_stmt).scalar()
            registration_package_unused_count = registration_package_pins_count - registration_package_used_count

            # Count  2000 pins
            registration_2000_pins_stmt = (
                db.Select(func.count().label('count'))
                .select_from(select(EPinTransaction.pin).distinct().where(EPinTransaction.pin_type == '2000 E-pin'))
            )
            registration_2000_pins_count = session.execute(registration_2000_pins_stmt).scalar()

            registration_2000_used_stmt = (
                db.Select(func.count().label('count'))
                .select_from(EPinTransaction)
                .where(EPinTransaction.pin_type == '2000 E-pin')
                .where(EPinTransaction.used_by.isnot(None))
            )
            registration_2000_used_count = session.execute(registration_2000_used_stmt).scalar()
            registration_2000_unused_count = registration_2000_pins_count - registration_2000_used_count

            # total pins count
            total_unique_pins = user_package_pins_count + registration_package_pins_count + registration_2000_pins_count
            total_used_pins = user_package_used_count + registration_package_used_count + registration_2000_used_count
            total_unused_pins = user_package_unused_count + registration_package_unused_count + registration_2000_unused_count
            
            return jsonify({
                'user_package_pins': user_package_pins_count,
                'user_package_used': user_package_used_count,
                'user_package_unused': user_package_unused_count,
                'registration_package_pins': registration_package_pins_count,
                'registration_package_used': registration_package_used_count,
                'registration_package_unused': registration_package_unused_count,
                'registration_2000_pins': registration_2000_pins_count,
                'registration_2000_used': registration_2000_used_count,
                'registration_2000_unused': registration_2000_unused_count,
                'total_unique_pins': total_unique_pins,
                'total_used_pins': total_used_pins,
                'total_unused_pins': total_unused_pins,
            })

def user_count():
    with db.session() as session:
            # Total user count
            total_stmt = db.Select(func.count().label('total_count')).select_from(UserModel)
            total_count = session.execute(total_stmt).scalar()

            # Paid user count
            paid_stmt = (
                db.Select(func.count().label('paid_count'))
                .select_from(UserModel)
                .where(UserModel.paid_status == 'PAID')
            )
            paid_count = session.execute(paid_stmt).scalar()

            # Unpaid user count
            unpaid_stmt = (
                db.Select(func.count().label('unpaid_count'))
                .select_from(UserModel)
                .where(UserModel.paid_status == 'UNPAID')
            )
            unpaid_count = session.execute(unpaid_stmt).scalar()

            response = {
                'total_count': total_count,
                'paid_count': paid_count,
                'unpaid_count': unpaid_count
            }
            return jsonify(response)

def get_epins_list(page: int = 1, per_page: int = 10):
    with db.session() as session:
            # latest created for each epin 
            subquery = (
                db.Select(
                    EPinTransaction.epin_id,
                    func.max(EPinTransaction.created_at).label('latest_created_at')
                )
                .group_by(EPinTransaction.epin_id)
                .order_by(desc(func.max(EPinTransaction.created_at)))
                .subquery()
            )

            # fetch epin records with the latest created_at
            transactions_stmt = (
                db.Select(EPinTransaction)
                .join(subquery, and_(
                    EPinTransaction.epin_id == subquery.c.epin_id,
                    EPinTransaction.created_at == subquery.c.latest_created_at
                ))
                .order_by(desc(subquery.c.latest_created_at))
            )

            # pagination
            offset = (page - 1) * per_page
            limit_stmt = transactions_stmt.limit(per_page).offset(offset)
            total_stmt = select(func.count()).select_from(transactions_stmt.subquery())

            total_count = session.execute(total_stmt).scalar()
            transactions = session.execute(limit_stmt).scalars().all()

            
            serialized_transactions = [transaction.serialize() for transaction in transactions]

            
            return jsonify({
                'transactions': serialized_transactions,
                'total_transactions': total_count,
                'current_page': page,
                'total_pages': (total_count + per_page - 1) // per_page  # Calculate total pages
            })