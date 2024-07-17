from flask import Blueprint, request, jsonify
from app import mongo, bcrypt, create_access_token

bp = Blueprint('register', __name__)


@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not all([first_name, last_name, email, password, confirm_password]):
        return jsonify({'error': 'Missing fields'}), 400

    if password != confirm_password:
        return jsonify({'error': 'Passwords do not match'}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'password': hashed_password
    }

    if mongo.db.users.find_one({'email': email}):
        return jsonify({'error': 'User with this email already exists'}), 400

    mongo.db.users.insert_one(user)
    user_token = mongo.db.users.find_one({'email': email})
    access_token = create_access_token(identity={'email': user_token['email']})
    return jsonify({
        'message': 'User registered successfully',
        'token': access_token}), 201
