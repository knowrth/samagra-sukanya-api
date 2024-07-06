from flask import  jsonify, request
from flask import Blueprint
from sqlalchemy import text, inspect, or_, desc, func
import jwt 
from models.db import db,  mail
from models.UserModels import UserModel, UserTransaction, UserDetails
from models.EpinModels import  EPinTransaction, RegisterEPin
from models.ReferencModels import  ResetTokenModel, IncomeLevel
from models.decorator import user_required

reg_trans = Blueprint('reg_trans', __name__,)


@reg_trans.route('/register_epins/<user_id>', methods=['GET'])
def get_register_epins_by_user_id(user_id):
    try:
 
        register_epins = RegisterEPin.query.filter_by(user_id=user_id).all()
 
        register_epins_json = [{
            'user_id': register_epin.user_id,
            'epin': register_epin.epin,
            'level': register_epin.level,
            'commission': register_epin.commission,
            'phone': register_epin.phone,
            'status': register_epin.status,
            'date_time': register_epin.date_time.strftime('%Y-%m-%d %H:%M:%S'),
            'register_time': register_epin.register_time.strftime('%Y-%m-%d %H:%M:%S') if register_epin.register_time else None,
            'pre_wallet': register_epin.pre_wallet,
            'after_wallet': register_epin.after_wallet,
            'member': register_epin.member,
            'trans_type': register_epin.trans_type,
            'log_type': register_epin.log_type,
            'trans_note': register_epin.trans_note
        } for register_epin in register_epins]
        return jsonify(register_epins_json), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    


@reg_trans.route('/user_task/transactions/<user_id>', methods=['GET'])
def get_user_task_transactions(user_id):
    try:
        user_transactions = RegisterEPin.query.filter_by(user_id=user_id).order_by(desc(RegisterEPin.date_time)).first()

        if user_transactions:
            transaction = {
                'id': user_transactions.level,
                'user_id': user_transactions.user_id,
                'epin_id': user_transactions.epin,
                'commission': user_transactions.commission,
                'pre_wallet': user_transactions.pre_wallet,
                'date_time': user_transactions.date_time.strftime('%Y-%m-%d %H:%M:%S'),  # Format date_time
                'after_wallet': user_transactions.after_wallet
            } 
            
            return jsonify({'transaction': transaction}), 200
        else:
            return jsonify({'message': 'No transactions found for the user'}), 404
    
    except Exception as e:
        print('Error in get_user_transactions:', str(e))
        return jsonify({'error': 'Internal Server Error'}), 500





