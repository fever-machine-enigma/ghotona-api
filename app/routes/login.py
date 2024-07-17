from flask import Blueprint
from app import mongo, bcrypt, create_access_token, request, jsonify

bp = Blueprint('login', __name__)


@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = mongo.db.users.find_one({'email': email})

    if user and bcrypt.check_password_hash(user['password'], password):
        user_id = str(user['_id'])
        access_token = create_access_token(identity={'email': user['email']})
        return jsonify({'token': access_token, 'first_name': user['first_name'], 'last_name': user['last_name'], 'user_id': user_id}), 200
    return jsonify({'error': 'Invalid email or password'}), 401
