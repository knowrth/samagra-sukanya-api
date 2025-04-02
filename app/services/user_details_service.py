from models.db import db, app
from flask import send_from_directory
from decimal import Decimal
import pytz
from sqlalchemy.sql import text
from sqlalchemy import  func, or_, select, case
import os 
import uuid
from models.UserModels import UserBankDetails, UserModel, UserDetails, UserMap, UserTransaction
from models.EpinModels import EPinTransaction, RegisterEPin
from models.ReferencModels import SupportTicket
from typing import List
from flask import jsonify

def create_user_details(user_id, title, gender, email, 
                        country, state, dob, father_name, 
                        house_telephone, city, pin_code, address, marital_status):
    with db.session() as session:
        stmt = db.Select(UserDetails).filter_by(user_id=user_id)
        user_details = session.execute(stmt).scalars().first()

        if user_details:
            user_details.title = title
            user_details.gender = gender
            user_details.dob = dob
            user_details.father_name = father_name
            user_details.house_telephone = house_telephone
            user_details.email = email
            user_details.country = country
            user_details.state = state
            user_details.city = city
            user_details.pin_code = pin_code
            user_details.address = address
            user_details.marital_status = marital_status

            session.commit()
        
        else:
            new_details = UserDetails(
                user_id=user_id,
                title=title,
                gender=gender,
                dob=dob,
                father_name=father_name,
                house_telephone=house_telephone,
                email=email,
                country=country,
                state=state,
                city=city,
                pin_code=pin_code,
                address=address,
                marital_status=marital_status
            )

            session.add(new_details)
            session.commit()

    return jsonify({'message': 'User details inserted successfully.'})

def generate_unique_filename(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    unique_filename = str(uuid.uuid4()) + '.' + ext
    return unique_filename

def inser_user_img(user_id, file):
    with db.session() as session:
        stmt = db.Select(UserDetails).filter_by(user_id=user_id)
        user = session.execute(stmt).scalars().first()

        if not user:
            user = UserDetails(user_id=user_id)

        filename = generate_unique_filename(file.filename)
        file.save(os.path.join(app.static_folder, filename))
        user.image_url = filename
        session.add(user)
        session.commit()

    return jsonify({'message': 'User details updated successfully'})

def get_user_img(user_id):
    with db.session() as session:
        stmt = db.Select(UserDetails).filter_by(user_id=user_id)
        user = session.execute(stmt).scalars().first()
        if user:
            image_name = user.image_url
            return send_from_directory('static', image_name)
        else:
            return send_from_directory('static', 'profile.jpg')

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def user_bank_details(user_id, ifsc_code, bank_name, branch_name, account_number, account_holder):
    with db.session() as session:
        # Check if user details exist
        stmt = db.Select(UserBankDetails).filter_by(user_id=user_id)
        result = session.execute(stmt)
        user_details = result.scalars().first()


        filename = None

        # if file and allowed_file(file.filename):
        #     filename = generate_unique_filename(file.filename)
        #     file.save(os.path.join(app.static_folder, filename))

        if user_details:
            user_details.file_url = filename  
            user_details.ifsc_code = ifsc_code
            user_details.bank_name = bank_name
            user_details.branch_name = branch_name
            user_details.account_number = account_number
            user_details.account_holder = account_holder
        else:
            user_details = UserBankDetails(
                user_id=user_id,
                file_url=filename, 
                ifsc_code=ifsc_code,
                bank_name=bank_name,
                branch_name=branch_name,
                account_number=account_number,
                account_holder=account_holder,
            )
            session.add(user_details)
        
        session.commit()

    return jsonify({'message': 'User bank details saved successfully'})

def user_nominee_details(user_id, nominee_name, nominee_relation, nominee_dob):
    with db.session() as session:
        # Check if user details exist
        stmt = db.Select(UserBankDetails).filter_by(user_id=user_id)
        result = session.execute(stmt)
        user_details = result.scalars().first()

        if user_details:
            user_details.nominee_name = nominee_name
            user_details.nominee_relation = nominee_relation
            user_details.nominee_dob = nominee_dob
        else:
            user_details = UserBankDetails(
                user_id=user_id,
                nominee_name=nominee_name,
                nominee_relation=nominee_relation,
                nominee_dob=nominee_dob
            )
            db.session.add(user_details)
        
        db.session.commit()
        
        return jsonify({'message': 'User details saved successfully'})

def get_user_phone(phone_start):
    with db.session() as session:

        stmt = select(UserModel).filter(UserModel.phone.like(f"{phone_start}%"))
        result = session.execute(stmt)
        users = result.scalars().all()
            
        # Serialize the result
        data = [{'name': user.name, 'phone': user.phone} for user in users]
        return jsonify(data)

def get_user_status(user_id):
    with db.session() as session:
        stmt = db.Select(UserModel).filter_by(user_id=user_id)
        user = session.execute(stmt).scalars().first()

        if user:
            status = user.user_status
            amount = user.amount_paid
            paid_status = user.paid_status

            return jsonify({
                'user_id': user.user_id,
                'status': status,
                'amount': amount,
                'paid_status': paid_status
            })

def reset_password(user_id, new_password):
    with db.session() as session:
        stmt = db.Select(UserModel).filter_by(user_id=user_id)
        user = session.execute(stmt).scalars().first()

        if user:
            user.password = new_password

        session.commit()
            
        return jsonify({'message': 'Password updated successfully'})

def user_sponsor(user_id):
    with db.session() as session:
        stmt = db.Select(UserModel).filter_by(user_id=user_id)
        user = session.execute(stmt).scalars().first()

        if user is None:
            return jsonify({'error': 'User not found'})
        
        sponsor_id = user.sponsor_id
        if sponsor_id:
            stmt = db.Select(UserModel).filter_by(user_id=sponsor_id)
            sponsor = session.execute(stmt).scalars().first()
            return jsonify({
                    'name': sponsor.name,
                    'phone': sponsor.phone,
                    'userName': sponsor.username,
                })
        else:
                return jsonify({})

def user_income_total(user_id):
    with db.session() as session:
        # total commission
        total_transaction_stmt = (
            select(func.sum(RegisterEPin.commission))
            .filter(RegisterEPin.user_id == user_id)
        )
        total_transaction_amount = session.execute(total_transaction_stmt).scalar() or 0

        total_reward_stmt = (
            select(func.sum(UserTransaction.amount))
            .filter(UserTransaction.user_id == user_id,
                    UserTransaction.category == 'Reward')
        )

        total_reward_amount = session.execute(total_reward_stmt).scalar() or 0

        # total withdrawal
        total_withdrawal_stmt = (
            select(func.sum(UserTransaction.amount))
            .filter(
                UserTransaction.user_id == user_id,
                UserTransaction.category == 'Withdrawals',
                UserTransaction.type == 'Debit'
            )
        )
        total_withdrawal_amount = session.execute(total_withdrawal_stmt).scalar() or 0

        total_amount = total_reward_amount + total_transaction_amount
        # remaining amount
        amount = total_amount - total_withdrawal_amount


        return jsonify({
            'total_withdrawal_amount': total_withdrawal_amount,
            'total_amount': total_amount,
            'amount': amount
        })

def get_user_direct_team(user_id):
    with db.session() as session:

        direct_team_details = []

        stmt = db.Select(UserModel).filter_by(sponsor_id=user_id)
        team = session.execute(stmt).scalars().all()

                
        sponsor_stmt = db.Select(UserModel).filter_by(user_id=user_id)
        sponsor_details = session.execute(sponsor_stmt).scalars().first()



        for user in team:
            user_stmt = db.Select(UserModel).filter_by(user_id=user.user_id)
            user_details = session.execute(user_stmt).scalars().first()

            transaction_stmt = db.Select(UserTransaction).filter_by(user_id=user_details.user_id).where(UserTransaction.amount >0.00)
            transaction = session.execute(transaction_stmt).scalars().first()

            if transaction:
                direct_team_details.append({
                'user_id' : user_details.user_id,
                'username': user_details.username,
                'name': user_details.name,
                'phone': user_details.phone,
                'status': user_details.paid_status,
                'joining_date': user_details.joining_date,
                'amount': transaction.amount,
                'date_time': transaction.date_time,
                })
            else:
                direct_team_details.append({
                'user_id' : user_details.user_id,
                'username': user_details.username,
                'name': user_details.name,
                'phone': user_details.phone,
                'status': user_details.paid_status,
                'joining_date': user_details.joining_date,
                'amount': '0',
                'date_time': None,
            })
            response = {
            'sponsor_name': sponsor_details.name,
            'sponsor_username': sponsor_details.username,
            'direct_team_details': direct_team_details
            }
        return jsonify(response)
    


from collections import defaultdict


def get_sponsor_stats(user_id):
    with db.session() as session:
        pattern = f"%{user_id}|%"

        stmt = (
            db.session.query(UserMap)
            .filter(UserMap.path.like(pattern))
        )
        
        data = session.execute(stmt).scalars().all()

        level_summary = defaultdict(lambda: {
            'paid_count': 0,
            'sponsor_count': 0,
            'unpaid_count': 0
        })
        
        for entry in data:
            path = entry.path
            if path:
                ids_in_path = path.split('|')[::-1]
                ids_in_path = [id.strip() for id in ids_in_path if id.strip()]

                if user_id in ids_in_path:
                    level = ids_in_path.index(user_id) + 1
                    
                    user_stmt = select(UserModel).filter_by(user_id=entry.user_id)
                    user_details = session.execute(user_stmt).scalars().first()
                    
                    if user_details:
                        level_summary[level]['sponsor_count'] += 1
                        
                        if user_details.paid_status == 'PAID':
                            level_summary[level]['paid_count'] += 1
                        else:
                            level_summary[level]['unpaid_count'] += 1

        aggregated_summary = defaultdict(lambda: {
            'paid_count': 0,
            'sponsor_count': 0,
            'unpaid_count': 0
        })

        for level, counts in level_summary.items():
            if level >= 9:
                aggregated_summary[9]['sponsor_count'] += counts['sponsor_count']
                aggregated_summary[9]['paid_count'] += counts['paid_count']
                aggregated_summary[9]['unpaid_count'] += counts['unpaid_count']
            else:
                aggregated_summary[level] = counts

        if 9 not in aggregated_summary:
            aggregated_summary[9] = {
                'paid_count': 0,
                'sponsor_count': 0,
                'unpaid_count': 0
            }

        result = []
        for level, counts in sorted(aggregated_summary.items()):
            result.append({
                'Level': level,
                'paid_count': counts['paid_count'],
                'sponsor_count': counts['sponsor_count'],
                'unpaid_count': counts['unpaid_count']
            })
        
    return jsonify(result)


def path_info(user_id, target_level: int = 1):
    with db.session() as session:

        pattern = f"%{user_id}|%"

        stmt = (
                db.session.query(UserMap)
                .filter(UserMap.path.like(pattern))
            )

        
        data = session.execute(stmt).scalars().all()
        result = []

        for entry in data:
            path = entry.path
            if path:
                ids_in_path = path.split('|')[::-1]
                ids_in_path = [id.strip() for id in ids_in_path if id.strip()]
                
                

                if user_id in ids_in_path:
                    level = ids_in_path.index(user_id) + 1
                    
                    if level >= 9:
                        level = 9

                    if level == target_level:
                        stmt = db.Select(UserModel).filter_by(user_id=entry.user_id)
                        user = session.execute(stmt).scalars().first()

                        sponsor_stmt = db.Select(UserModel).filter_by(user_id=user.sponsor_id)
                        sponsor = session.execute(sponsor_stmt).scalars().first()

                        date_stmt = db.Select(UserTransaction).filter_by(user_id=user.user_id)
                        date = session.execute(date_stmt).scalars().first()

                        result.append({
                            'name': user.name,
                            'username': user.username,
                            'paid_status': user.paid_status,
                            'phone': user.phone,
                            'joining_date': user.joining_date,
                            'sponsor_by': sponsor.name,
                            'amount': date.amount if date else None,
                            'level': level
                        })

        

        if not result:
            print(f"No results at target level {target_level}")

        return result

