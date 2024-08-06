from flask import  jsonify, request
from flask import Blueprint, send_from_directory
from sqlalchemy import func
import os 
from models.db import db,  app
import uuid
from models.UserModels import UserModel, UserDetails, UserMap, UserTransaction, UserBankDetails
from sqlalchemy.exc import SQLAlchemyError
from models.decorator import user_required
from services.user_details_service import create_user_details, inser_user_img, get_user_img, path_info, user_bank_details, user_nominee_details, get_user_phone, get_user_direct_team
from datetime import datetime

user_details = Blueprint('user_details', __name__,)

def generate_unique_filename(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    unique_filename = str(uuid.uuid4()) + '.' + ext
    return unique_filename


import logging

logger = logging.getLogger(__name__)

# user profile details

@user_details.route('/v2/user_details/<user_id>', methods=['POST'])
@user_required
def insert_user_details(user_id):
    try:
        data = request.json
        title = data.get('title')
        gender = data.get('gender')
        dob = data.get('dob')
        father_name = data.get('father_name')
        house_telephone = data.get('house_telephone')
        email = data.get('email')
        country = data.get('country')
        state = data.get('state')
        city = data.get('city')
        pin_code = data.get('pin_code')
        address = data.get('address')
        marital_status = data.get('marital_status')
        # existing_user = UserDetails.query.filter_by(user_id=user_id).first()

        # if existing_user:
        #     existing_user.title = data.get('title', existing_user.title)
        #     existing_user.gender = data.get('gender', existing_user.gender)
        #     existing_user.dob = datetime.strptime(data['dob'], '%Y-%m-%d')
        #     existing_user.father_name = data.get('father_name', existing_user.father_name)
        #     existing_user.house_telephone = data.get('house_telephone', existing_user.house_telephone)
        #     existing_user.email = data.get('email', existing_user.email)
        #     existing_user.country = data.get('country', existing_user.country)
        #     existing_user.state = data.get('state', existing_user.state)
        #     existing_user.city = data.get('city', existing_user.city)
        #     existing_user.pin_code = data.get('pin_code', existing_user.pin_code)
        #     existing_user.address = data.get('address', existing_user.address)
        #     existing_user.marital_status = data.get('marital_status', existing_user.marital_status)

        #     db.session.commit()
        #     return jsonify({'message': 'User details updated successfully.'}), 200
        # else:
        #     new_user = UserDetails(
        #         user_id=user_id,
        #         title=data['title'],
        #         gender=data['gender'],
        #         dob=datetime.strptime(data['dob'], '%Y-%m-%d'),
        #         father_name=data['father_name'],
        #         house_telephone=data['house_telephone'],
        #         email=data['email'],
        #         country=data['country'],
        #         state=data['state'],
        #         city=data['city'],
        #         pin_code=data['pin_code'],
        #         address=data['address'],
        #         marital_status=data['marital_status']
        #     )

        #     db.session.add(new_user)
        #     db.session.commit()
        new_user_details = create_user_details(user_id=user_id, title=title, gender=gender, email=email, 
                        country=country, state=state, dob=dob, father_name=father_name, house_telephone=house_telephone,
                        city=city, pin_code=pin_code, address=address, marital_status=marital_status)
        if new_user_details:
            return new_user_details, 200

    except Exception as e:
        db.session.rollback()
        logger.exception("An error occurred while inserting or updating user details")
        return jsonify({'error': str(e)}), 500
    

# user profile image insert

@user_details.route('/v2/user_details_img/<user_id>', methods=['PUT'])
@user_required
def insert_user_details_img(user_id):
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # user = UserDetails.query.filter_by(user_id=user_id).first()

        # if not user:
        #     user = UserDetails(user_id=user_id)

        # filename = generate_unique_filename(file.filename)
        # file.save(os.path.join(app.static_folder, filename))
        # user.image_url = filename
        # db.session.add(user)
        # db.session.commit()
        user = inser_user_img(user_id=user_id, file=file)
        if user:
            return user, 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# user image retrieve

@user_details.route('/v2/user_image_name/<user_id>', methods=['GET'])
def get_user_image_name(user_id):
    try:
        # user = UserDetails.query.filter_by(user_id=user_id).first()

        # if user:
        #     image_name = user.image_url
        #     # print('image:', image_name)
        #     return send_from_directory('static', image_name)
        # else:
        #     return send_from_directory('static', 'profile.jpg')
        user = get_user_img(user_id)
        if user:
            return user

    except Exception as e:
        return jsonify({'error': str(e)}), 500



# Total team

@user_details.route('/v2/path_info/<user_id>', methods=['GET'])
@user_required
def get_path_info(user_id):
    level = request.args.get('level')

    target_level = int(level)
    
    # results = db.session.query(
    #     func.length(func.substring(UserMap.path, func.strpos(UserMap.path, user_id))) - 
    #     func.length(func.replace(func.substring(UserMap.path, func.strpos(UserMap.path, user_id)), '|', '')),
    #     func.array_agg(UserMap.user_id).label('user_ids')
    # ).join(UserModel, UserModel.user_id == UserMap.user_id).filter(UserMap.path.like(f'%{user_id}|%')).group_by(
    #     func.length(func.substring(UserMap.path, func.strpos(UserMap.path, user_id))) - 
    #     func.length(func.replace(func.substring(UserMap.path, func.strpos(UserMap.path, user_id)), '|', ''))
    # ).order_by(
    #     func.length(func.substring(UserMap.path, func.strpos(UserMap.path, user_id))) - 
    #     func.length(func.replace(func.substring(UserMap.path, func.strpos(UserMap.path, user_id)), '|', ''))
    # ).all()
    # path_info(user_id)
    # total_results = {}
    # for row in results:
    #     pipe_count = min(row[0], 9) 
    #     if pipe_count in total_results:
    #         total_results[pipe_count]['user_ids'].extend(row[1])
    #     else:
    #         total_results[pipe_count] = {
    #             'Level': pipe_count,
    #             'user_ids': row[1]
    #         }

    # for level_data in total_results.values():
    #     user_ids = level_data['user_ids']
    #     user_info = []
    #     for user_id in user_ids:
    #         user = db.session.query(
    #             UserModel.name,
    #             UserModel.username,
    #             UserModel.paid_status,
    #             UserModel.phone,
    #             UserModel.joining_date,
    #             UserModel.sponsor_id
    #         ).filter(UserModel.user_id == user_id).first()
    #         sponsor = UserModel.query.filter_by(user_id=user.sponsor_id).first().name
    #         transaction = UserTransaction.query.filter_by(user_id=user_id, category='Activation').first()
    #         user_info.append({
    #             'name': user.name,
    #             'username': user.username,
    #             'paid_status': user.paid_status,
    #             'phone': user.phone,
    #             'joining_date': user.joining_date,
    #             'sponsor_by': sponsor,
    #             'amount': transaction.amount if transaction else None
    #         })
    #     level_data['users'] = user_info
    response = path_info(user_id=user_id, target_level=target_level)
    # data = list(total_results.values())
    return response


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# team downline

from sqlalchemy import and_

@user_details.route('/v2/direct_team/<user_id>', methods=['GET'])
@user_required
def get_direct_team(user_id):
    # sponsor_details = UserModel.query.filter_by(sponsor_id=user_id).all()
    # direct_team_details = []
    # sponsor_name = UserModel.query.filter_by(user_id=user_id).first().name  
    # sponsor_username = UserModel.query.filter_by(user_id=user_id).first().username  

    
    # for user in sponsor_details:
    #     user_details = UserModel.query.filter_by(user_id=user.user_id).first()
    #     positive_transactions = UserTransaction.query.filter(and_(UserTransaction.user_id == user.user_id, UserTransaction.amount > 0.00)).all()
        
    #     if positive_transactions:
    #         # Assuming you want to consider only the first positive transaction
    #         first_positive_transaction = positive_transactions[0]
    #         direct_team_details.append({
    #             'user_id' : user_details.user_id,
    #             'username': user_details.username,
    #             'name': user_details.name,
    #             'phone': user_details.phone,
    #             'status': user_details.paid_status,
    #             'joining_date': user_details.joining_date,
    #             'amount': first_positive_transaction.amount,
    #             'date_time': first_positive_transaction.date_time,
    #         })
    #     else:
    #         direct_team_details.append({
    #             'user_id' : user_details.user_id,
    #             'username': user_details.username,
    #             'name': user_details.name,
    #             'phone': user_details.phone,
    #             'status': user_details.paid_status,
    #             'joining_date': user_details.joining_date,
    #             'amount': '0',
    #             'date_time': None,
    #         })
    
    # response = {
    #     'sponsor_name': sponsor_name,
    #     'sponsor_username': sponsor_username,
    #     'direct_team_details': direct_team_details
    # }

    response = get_user_direct_team(user_id=user_id)
    
    # return jsonify(response)
    return response


# user bank details

@user_details.route('/v2/user_bank/<user_id>', methods=['POST'])
@user_required
def user_bank(user_id):
    try:
        
        ifsc_code = request.form.get('ifsc_code')
        bank_name = request.form.get('bank_name')
        branch_name = request.form.get('branch_name')
        account_number = request.form.get('account_number')
        account_holder = request.form.get('account_holder')

        filename=None
        # print(f"Received POST request for user ID: {user_id}")
        # file = request.files['file']
        # if file:
        #     if 'file' not in request.files:
        #         # print("No file part in the request")
        #         return jsonify({'message': 'No file part in the request'}), 400
            
            
            
        #     if file.filename == '':
        #         # print("No selected file")
        #         return jsonify({'message': 'No selected file'}), 400
            
        #     if file and allowed_file(file.filename):
        #         filename = generate_unique_filename(file.filename)
        #         file.save(os.path.join(app.static_folder, filename))
        #         # print(f"Saved file as: {filename}")
        #     else:
        #         # print("File type not allowed")
        #         return jsonify({'message': 'File type not allowed'}), 400
        # else:
        #     pass

        

        # print(f"Received form data - IFSC Code: {ifsc_code}, Bank Name: {bank_name}, Branch Name: {branch_name}, Account Number: {account_number}, Account Holder: {account_holder}")

        # user_details = UserBankDetails.query.filter_by(user_id=user_id).first()
        
        # if user_details:
        #     # print("Updating existing user bank details")
        #     user_details.file_url = filename  
        #     user_details.ifsc_code = ifsc_code
        #     user_details.bank_name = bank_name
        #     user_details.branch_name = branch_name
        #     user_details.account_number = account_number
        #     user_details.account_holder = account_holder
        # else:
        #     # print("Creating new user bank details")
        #     user_details = UserBankDetails(
        #         user_id=user_id,
        #         file_url=filename, 
        #         ifsc_code=ifsc_code,
        #         bank_name=bank_name,
        #         branch_name=branch_name,
        #         account_number=account_number,
        #         account_holder=account_holder,
        #     )
        #     db.session.add(user_details)
        
        # db.session.commit()
        # print("Committed changes to database")
        response = user_bank_details(user_id=user_id, ifsc_code=ifsc_code, bank_name=bank_name, branch_name=branch_name, account_number=account_number, account_holder=account_holder)
        return response, 200
    
    except SQLAlchemyError as e:
        db.session.rollback()
        # print(f"Failed to save user bank details: {str(e)}")
        return jsonify({'message': f'Failed to save user bank details: {str(e)}'}), 500
    except Exception as e:
        # print(f"Error occurred: {str(e)}")
        return jsonify({'message': str(e)}), 500
        


# user nominee details


@user_details.route('/v2/user_nominee/<user_id>', methods=['POST'])
@user_required
def user_nominee(user_id):
    try:
        data = request.json
        nominee_name = data.get('nominee_name')
        nominee_relation = data.get('nominee_relation')
        nominee_dob = data.get('nominee_dob')
        print('nominee_name', nominee_name)
        
        # user_details = UserBankDetails.query.filter_by(user_id=user_id).first()
        
        # if user_details:
        #     user_details.nominee_name = nominee_name
        #     user_details.nominee_relation = nominee_relation
        #     user_details.nominee_dob = nominee_dob
        # else:
        #     user_details = UserBankDetails(
        #         user_id=user_id,
        #         nominee_name=nominee_name,
        #         nominee_relation=nominee_relation,
        #         nominee_dob=nominee_dob
        #     )
        #     db.session.add(user_details)
        
        # db.session.commit()

        response = user_nominee_details(user_id=user_id,nominee_dob=nominee_dob, nominee_name=nominee_name, nominee_relation=nominee_relation )
        
        return response, 200
    
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to save user details: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@user_details.route('/v1/names-and-phones', methods=['GET'])
@user_required
def get_names_and_phones():
    try:
        phone_start = request.args.get('phone_start')
        
        if not phone_start or len(phone_start) != 3 or not phone_start.isdigit():
            return jsonify({'message': 'Invalid phone_start parameter. It must be a 3-digit number.'}), 400

        # users = UserModel.query.filter(UserModel.phone.like(f"{phone_start}%")).all()
        
        # data = [{'name': user.name, 'phone': user.phone} for user in users]

        response = get_user_phone(phone_start=phone_start)
        
        return response, 200

    except SQLAlchemyError as e:
        # print(e)
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        # print(e)
        return jsonify({'error': str(e)}), 500
