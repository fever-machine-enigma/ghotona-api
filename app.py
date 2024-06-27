from flask import Flask, request, jsonify, render_template
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_pymongo import PyMongo
from bson import json_util, ObjectId
from dotenv import load_dotenv
from datetime import datetime, timedelta
from flask_cors import CORS
# import tensorflow as tf
import os

load_dotenv()
app = Flask(__name__)

# CORS Validation
CORS(app, resources={r"/*": {"origins": ["http://localhost:5173"]}})


# App Configuration
mongo_uri = os.getenv('MONGO_URI')
app.config["MONGO_URI"] = mongo_uri
if not app.config["MONGO_URI"]:
    raise ValueError(
        "No MongoDB URI found. Please set the MONGO_URI environment variable in the .env file.")
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
mongo = PyMongo(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)


# Function to serialize MongoDB documents


def serialize_doc(doc):
    doc["_id"] = str(doc["_id"])
    return doc


@app.route('/', methods=['GET'])
def root():
    return render_template('index.html')

# Registration Endpoint


@app.route('/register', methods=['POST'])
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


# Login endpoint
@app.route('/login', methods=['POST'])
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

# Logout endpoint


def blacklist_token(token):
    mongo.db.token_blacklist.insert_one({
        'token': token,
        'blacklisted_at': datetime.utcnow()
    })


@app.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Missing Authorization header'}), 401
    token = auth_header.split()[1]  # Assuming 'Bearer token' format
    # Blacklist the token
    blacklist_token(token)

    return jsonify({'message': 'Logged out successfully'}), 200


@app.route('/fetch-log', methods=['GET'])
@jwt_required()
def eventlog():
    data = request.get_json()
    user_id = ObjectId(data.get('user_id'))
    # Check blacklist before processing the request
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Missing Authorization header'}), 401
    token = auth_header.split()[1]
    # Replace this with your actual blacklist check logic using MongoDB
    is_blacklisted = mongo.db.token_blacklist.find_one({'token': token})
    if is_blacklisted:
        return jsonify({'error': 'Token is blacklisted'}), 401
    logs = list(mongo.db.eventlogs.find({'user_id': user_id}))
    if not logs:
        return jsonify({'message': 'No event logs found for user ID'}), 404
    return json_util.dumps(logs)


# # Load the trained model with custom objects
# model = tf.keras.models.load_model(
#     'model/capstoneBETA.h5')


# def preprocess_input(data):
#     return data


# @app.route('/predict', methods=['POST'])
# def predict():
#     input_data = request.json['input']

#     preprocessed_data = preprocess_input(input_data)

#     prediction = model.predict(preprocessed_data)

#     response = {
#         'prediction': prediction.tolist()
#     }
#     return jsonify(response)


# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
