import jwt
from functools import wraps
from flask import request, jsonify
import logging

secret_key = 'your_secret_key'

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        bearer_token = request.headers.get('Authorization')
        if not bearer_token or not bearer_token.startswith('Bearer '):
            return jsonify({'error': 'Invalid authorization token'}), 401

        token_parts = bearer_token.split()
        if len(token_parts) != 2:
            return jsonify({'error': 'Invalid token format'}), 401

        token = token_parts[1]

        try:
            decoded_token = jwt.decode(token, secret_key, algorithms=['HS256'])

            if 'role' not in decoded_token or decoded_token['role'].upper() != 'ADMIN':
                return jsonify({'error': 'Unauthorized'}), 403

        # except ExpiredSignatureError:
        #     return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            logging.exception("Invalid token: %s", token)
            return jsonify({'error': 'Invalid token'}), 401

        return f(*args, **kwargs)

    return decorated_function

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        bearer_token = request.headers.get('Authorization')
        if not bearer_token or not bearer_token.startswith('Bearer '):
            return jsonify({'error': 'Invalid authorization token'}), 401

        token_parts = bearer_token.split()
        if len(token_parts) != 2:
            return jsonify({'error': 'Invalid token format'}), 401

        token = token_parts[1]

        try:
            decoded_token = jwt.decode(token, secret_key, algorithms=['HS256'])

            if 'role' not in decoded_token or decoded_token['role'] != 'USER':
                return jsonify({'error': 'Unauthorized'}), 403

        # except ExpiredSignatureError:
        #     return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            logging.exception("Invalid token: %s", token)
            return jsonify({'error': 'Invalid token'}), 401

        return f(*args, **kwargs)

    return decorated_function
