from models.db import db, app
from flask import send_from_directory
from decimal import Decimal
import pytz
from sqlalchemy.sql import text
from sqlalchemy import  func, or_, select
import os 
import uuid
from models.UserModels import UserBankDetails, UserModel, UserDetails, UserMap
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
        
def path_info(user_id, level=1):
    with db.session() as session:
            print('user_id:', user_id)
            stmt = (
                db.select(UserMap)
                .filter(UserMap.path.like(f'%{user_id}|%'))
            )
            print('stmt:', stmt)
            results = session.execute(stmt).scalars().all()

            print('path:', results)
            
            filtered_paths = []

            for result in results:
                # Split the path by '|'
                split_paths = result.path.split('|')

                # Remove empty strings
                split_paths = [path for path in split_paths if path.strip()]
                print('split_paths:', split_paths)
                
                # Reverse the split paths for easier index access
                reversed_paths = split_paths[::-1]
                print('reversed_paths:', reversed_paths)
                
                # Check if the level-1 index exists and if the user_id matches
                if len(reversed_paths) >= level:
                    if reversed_paths[level - 1] == user_id:
                        filtered_paths.append(result.path)

            print('Filtered Paths:', filtered_paths)

            # print('Filtered Paths:', filtered_paths)

            # ids=[]
            # paths=[]
            
            # for result in results:
            #     # Assuming `result.path` is a string with values separated by '|'
            #     split_paths = result.path.split('|')
                
            #     # Remove empty strings and other unwanted values
            #     cleaned_paths = [path for path in split_paths if path.strip()]
                
            #     # Example: adding cleaned paths to paths list
            #     paths.extend(cleaned_paths)
                
            #     # If you also need to collect ids or other attributes, handle accordingly
            #     ids.append(result.id)  # Replace 'id' with the actual attribute if needed
            
            # print('IDs:', ids)
            # print('Cleaned Paths:', paths)

            
            # print('path:',results)
            pass
