from flask import Flask, render_template, jsonify, request
# from flask_mysqldb import MySQLS
from models.db import db, app
from flask_cors import CORS, cross_origin
import jwt
from models.ReferencModels import insert_income_levels, create_initial_admin, create_initial_user
from models.UserModels import UserModel, UserMap
from models.EpinModels import EPinTransaction
from sqlalchemy import MetaData, Table


CORS(app, resources={r"/api/*": {"origins": "*", "http://localhost:3000": "*"}})

# def create_tables_and_populate_data():
#     with app.app_context():
#         db.create_all()
#         create_initial_admin()
#         create_initial_user()
#         insert_income_levels()

# create_tables_and_populate_data()


from routes.admin.v1 import admin
from routes.users.v1 import users 
from routes.users.v2 import user_details
from routes.transactions.v1 import transaction
from routes.epin.v2 import reg_trans
from routes.epin.v1 import epins


app.register_blueprint(admin)
app.register_blueprint(transaction)
app.register_blueprint(epins)
app.register_blueprint(users)
app.register_blueprint(reg_trans)
app.register_blueprint(user_details)


@app.route('/login', methods=['POST'])
@cross_origin()
def login():
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    print(email)
    print(password)
    user = UserModel.query.filter_by(phone=email).first()

    if user and user.verify_password(password):
        token_payload = {'user_id': str(user.user_id), 'email': user.email, 'role': user.role, 'name': user.name, 'username': user.username, 'phone': user.phone}
        access_token = jwt.encode(token_payload, 'your_secret_key', algorithm='HS256')
        return jsonify({'access_token': access_token}), 200
    else:
        return jsonify({'error': 'Invalid email or password'}), 401



@app.route('/decode_token', methods=['POST'])
def decode_token():
    token = request.json.get('token', None)

    if not token:
        return jsonify({'error': 'Token is missing'}), 400

    try:
        token_contents = jwt.decode(token, 'your_secret_key', algorithms=['HS256'])
        return jsonify({'token_contents': token_contents}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401



if __name__ == '__main__':
    app.run(host="0.0.0.0" , debug=True)