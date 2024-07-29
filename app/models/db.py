from flask_sqlalchemy import SQLAlchemy
# from flask_mysqldb import MySQL
from datetime import datetime, timezone
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
# import mysql.connector
import os
from dotenv import load_dotenv
from sqlalchemy import URL
from flask_mail import Mail
# from flask_jwt_extended import JWTManager

app = Flask(__name__, static_folder='static')

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


DB_URL = URL.create(
    drivername=os.getenv('DB_DRIVER','postgresql'),
    username=os.getenv('POSTGRES_USER', 'postgres'),
    password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
    host=os.getenv('DB_HOST', 'localhost'),
    port=os.getenv('DB_PORT', '5432'),
    database=os.getenv('POSTGRES_DB', 'userdb'),

)


# print(DB_URL)

# def getMysqlConnection():
#     return mysql.connector.connect(user='user', host='localhost', port='3306', password='password', database='userDB')

# mail_port = os.getenv('MAIL_USE_TLS')
# print(f"MAIL_USE_TLS from environment: {mail_port}")

CORS(app) 
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = tuple(os.getenv('MAIL_DEFAULT_SENDER').split(','))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_TOKEN_LOCATION'] = os.getenv('JWT_TOKEN_LOCATION').split()
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER')
app.config['ALLOWED_EXTENSIONS'] = set(os.getenv('ALLOWED_EXTENSIONS').split(','))
# app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')

# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://test:test1234@db/mysql'
# app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqldb://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}/{os.getenv('MYSQL_DB')}"
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
# app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
# app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
# app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')




# db = getMysqlConnection()
db = SQLAlchemy(app)
mail = Mail(app)
# mysql = MySQL(app)
# jwt = JWTManager(app)

# from models.UserModels import UserModel
# from models.EpinModels import RegisterEPin
