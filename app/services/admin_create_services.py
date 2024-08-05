from models.db import db, app
from flask import send_from_directory
from decimal import Decimal
import datetime
import pytz
from sqlalchemy.sql import text
from sqlalchemy import  func, or_, select, update
import os 
import uuid
from models.UserModels import UserTransaction, UserModel, UserDetails, UserMap
from models.EpinModels import EPinTransaction, RegisterEPin
from models.ReferencModels import SupportTicket
from typing import List
from flask import jsonify


def approve_withdrawals(amount, user_id, created_at, remark_admin=None):
    with db.session() as session:
            # fetch the user request 
            transaction_stmt = (
                db.Select(UserTransaction)
                .where(UserTransaction.user_id == user_id)
                .where(UserTransaction.amount == amount)
                .where(UserTransaction.date_time == created_at)
                .where(UserTransaction.status == "Pending")
            )
            user_transaction = session.execute(transaction_stmt).scalars().first()

            if user_transaction:
                # update the request record
                remark = f"Withdrawal amount {amount}, {remark_admin}" if remark_admin else f"Withdrawal amount {amount}"
                updated_at = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))

                update_stmt = (
                    update(UserTransaction)
                    .where(UserTransaction.id == user_transaction.id)
                    .values(
                        status="Approved",
                        remark=remark,
                        date_time=updated_at
                    )
                )
                session.execute(update_stmt)
                session.commit()

                return jsonify({'message': 'Withdrawal successful'}), 200
            
def approve_support(resolved_issue, user_id, created_at):
    with db.session() as session:
            # fetch the user support 
            transaction_stmt = (
                db.Select(SupportTicket)
                .where(SupportTicket.user_id == user_id)
                .where(SupportTicket.date_time == created_at)
            )
            user_support = session.execute(transaction_stmt).scalars().first()

            if user_support:
                # update the support record
                
                update_stmt = (
                    update(SupportTicket)
                    .where(SupportTicket.id == user_support.id)
                    .values(
                        query_status="Closed",
                        resolved_issue=resolved_issue,
                    )
                )
                session.execute(update_stmt)
                session.commit()

                return jsonify({'message': 'Withdrawal successful'}), 200
            
def usernames_and_phones(page: int, per_page: int):
    with db.session() as session:
        offset = (page - 1) * per_page

        # paginated list of user
        stmt = (
                db.Select(UserModel.name, UserModel.phone)
                .limit(per_page)
                .offset(offset)
            )
        result = session.execute(stmt).all()

        data = [f"{row.name} - {row.phone}" for row in result]

        # Count the total 
        count_stmt = db.Select(func.count()).select_from(UserModel)
        total_count = session.execute(count_stmt).scalar()

        total_pages = (total_count + per_page - 1) // per_page

        return jsonify({
                'users': data,
                'total_pages': total_pages,
                'current_page': page
            })

def admin_user_password_reset(user_id, password):
    with db.session() as session:
        stmt = db.Select(UserModel).filter_by(user_id=user_id)
        user = session.execute(stmt).scalars().first()
        if user:
            user.password = password
            session.commit()

            return jsonify({'message': 'User password updated successfully'})
        else:
            return jsonify({'error': 'User not found'})

def user_subscription(pin_type, user_id, transaction_type, sponsor=None):
    with db.session() as session:
        #  Check if the user exists
        user_stmt = select(UserModel).where(UserModel.user_id == user_id)
        user = session.execute(user_stmt).scalars().first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Map pin types to packages
        package_map = {
            '0': 'Registered',
            '600': 'Partial Access',
            '1400': 'Partial Access',
            '2000': 'Activated'
        }
        package = package_map.get(pin_type)
        if not package:
            return jsonify({'error': 'Invalid pin type'}), 400

        # Update user information
        user_amt = Decimal(pin_type)
        user_stmt = (
            update(UserModel)
            .where(UserModel.user_id == user_id)
            .values(
                amount_paid=UserModel.amount_paid + user_amt,
                paid_type=transaction_type,
                reg_status=package
            )
        )
        session.execute(user_stmt)
        
        # Update user status 
        if user.amount_paid + user_amt >= Decimal('2000'):
            user_status_stmt = (
                update(UserModel)
                .where(UserModel.user_id == user_id)
                .values(
                    paid_status='PAID',
                    user_status='ACTIVE',
                    reg_status='Activated'
                )
            )
            session.execute(user_status_stmt)

        session.commit()

        sponsor_info = sponsor
        sponsor_id = None
        if sponsor_info:
            try:
                sponsor_name, sponsor_phone = map(str.strip, sponsor_info.split('-'))
                sponsor_stmt = select(UserModel).where(
                    UserModel.name == sponsor_name,
                    UserModel.phone == sponsor_phone
                )
                sponsor = session.execute(sponsor_stmt).scalars().first()
                if sponsor:
                    sponsor_id = sponsor.user_id
            except ValueError:
                sponsor_id = None

        # Create new transaction record
        created_at = datetime.now(pytz.timezone('Asia/Kolkata'))
        remark = f"Paid {pin_type} {transaction_type}, {transaction_note}"
        transaction_stmt = UserTransaction(
                user_id=user_id,
                type='Payment',
                category='Activation',
                amount=str(pin_type),
                remark=remark,
                date_time=created_at,
                sponsor_id=sponsor_id,
                status=None
            )
        session.add(transaction_stmt)
        session.commit()

        #  EPin generation for sponsors
        if user.amount_paid + user_amt >= Decimal('2000'):
            sponsor_stmt = select(UserModel).where(UserModel.user_id == user_id)
            sponsor_transaction = session.execute(sponsor_stmt).scalars().first()
            if sponsor_transaction and sponsor_transaction.sponsor_id:
                epin_transaction = EPinTransaction(
                        transaction_type='generate',
                        user_id=sponsor_transaction.sponsor_id,
                        pin_type='2000 E-pin',
                        pin_amount='2000.00',
                        created_at=created_at,
                        issued_to=sponsor_transaction.sponsor_id,
                        held_by=sponsor_transaction.sponsor_id
                    )
                session.add(epin_transaction)
                session.commit()

        return jsonify({'message': 'Epin issued successfully'}), 200

def user_multiple_pins(amount, count, name, phone):
    with db.session() as session:
        # get for the user
        user_stmt = select(UserModel).where(UserModel.name == name, UserModel.phone == phone)
        user = session.execute(user_stmt).scalars().first()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        user_id = user.user_id

        for _ in range(count):
            transaction_records = UserTransaction(
                user_id = user_id,
                type = 'Payment',
                category = 'Kit Purchase',
                amount = str(amount),
                remark = f"Paid {amount}",
                sponsor_id = user_id,
                date_time = created_at,
                status = None
            )
            session.add(transaction_records)

            pin_amount = '0.00' if amount == Decimal('0.00') else '500.00'
            pin_type = '0 E-pin' if amount == Decimal('0.00') else '500 E-pin'
            created_at = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
            epin_records = EPinTransaction(
                transaction_type = 'generate',
                user_id = user_id,
                pin_type = pin_type,
                pin_amount = pin_amount,
                created_at = created_at,
                issued_to = user_id,
                held_by = user_id,
            )
            session.add(epin_records)
        

        session.commit()

    return jsonify({'message': 'Amount paid successfully'}), 200




