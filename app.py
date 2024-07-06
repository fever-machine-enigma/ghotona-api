from flask import Flask, request, jsonify, render_template
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_pymongo import PyMongo
from bson import json_util, ObjectId
from dotenv import load_dotenv
from datetime import datetime, timedelta
from flask_cors import CORS
import tensorflow as tf
from tensorflow import keras
from custom_layer import TokenAndPositionEmbedding, TransformerEncoder
from huggingface_hub import InferenceClient
import numpy as np
import pytz
import re
import requests
import string
import os
import chardet
load_dotenv()
app = Flask(__name__)

# CORS Validation
CORS(app, resources={
     r"/*": {"origins": ["http://localhost:5173", 'http://127.0.0.1:5500', 'https://ghotona-chitro.vercel.app']}})

client = InferenceClient(model="csebuetnlp/banglat5")

# App Configuration
mongo_uri = os.getenv('MONGO_URI')
app.config["MONGO_URI"] = mongo_uri
if not app.config["MONGO_URI"]:
    raise ValueError(
        "No MongoDB URI found. Please set the MONGO_URI environment variable in the .env file.")
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=6)
mongo = PyMongo(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)


# Function to log requests


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


@app.route('/fetch-log', methods=['POST'])
@jwt_required()
def eventlog():
    data = request.get_json()
    user_id = ObjectId(data.get('user_id'))
    # Check blacklist before processing the request
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Missing Authorization header'}), 401
    token = auth_header.split()[1]
    is_blacklisted = mongo.db.token_blacklist.find_one({'token': token})
    if is_blacklisted:
        return jsonify({'error': 'Token is blacklisted'}), 401
    logs = list(mongo.db.eventlogs.find({'user_id': user_id}))
    if not logs:
        return jsonify({'message': 'No event logs found for user ID'}), 404
    data = []
    for log in logs:
        data.append({
            'corpus': log.get('corpus'),
            'event': log.get('event'),
            'title': log.get('title'),
            'created': log.get('created')
        })
    return json_util.dumps(data), 201


# @app.route('/test')
# def test():
#     return render_template('test.html')


# Load the trained model with custom objects
# with keras.utils.custom_object_scope({'TokenAndPositionEmbedding': TokenAndPositionEmbedding, 'TransformerEncoder': TransformerEncoder}):
#     model = keras.models.load_model('model/transformer.h5')
# model = keras.models.load_model('saved_model')
# with keras.utils.custom_object_scope({'TokenAndPositionEmbedding': TokenAndPositionEmbedding, 'TransformerEncoder': TransformerEncoder}):
model = tf.saved_model.load('saved_model')
# with keras.utils.custom_object_scope({'TokenAndPositionEmbedding': TokenAndPositionEmbedding, 'TransformerEncoder': TransformerEncoder}):
# model = keras.models.load_model('model/model3.h5')


def custom_standardization(input_data):
    lowercase = tf.strings.lower(input_data)
    stripped_html = tf.strings.regex_replace(lowercase, '<br />', ' ')
    return tf.strings.regex_replace(stripped_html, '[%s]' % re.escape(string.punctuation), '')


# Load vectorization layer and vocabulary
vectorize_layer = tf.keras.layers.TextVectorization(
    standardize=custom_standardization,
    max_tokens=20000,
    output_mode='int',
    output_sequence_length=500
)
# Use raw string or double backslashes
vocab_path = r"model/vocab2.txt"

with open(vocab_path, 'rb') as file:
    raw_data = file.read()
    result = chardet.detect(raw_data)
    encoding = result['encoding']

with open(vocab_path, 'r', encoding=encoding) as file:
    vocab = [line.strip() for line in file]
unique_vocab = list(dict.fromkeys(vocab))
vectorize_layer.set_vocabulary(unique_vocab)

# Mapping dictionaries
# int_to_str = {
#     0: 'বাংলাদেশ', 1: 'ব্যবসা', 2: 'অপরাধ',
#     3: 'বিপর্যয়', 4: 'বিনোদন', 5: 'আন্তর্জাতিক',
#     6: 'মতামত', 7: 'খেলাধুলা', 8: 'প্রযুক্তি', 9: 'রাজনীতি'
# }

int_to_str = {
    0: 'বাংলাদেশ', 1: 'ব্যবসা', 2: 'অপরাধ',
    3: 'খেলাধুলা', 4: 'বিনোদন', 5: 'আন্তর্জাতিক',
}

API_URL = "https://api-inference.huggingface.co/models/csebuetnlp/mT5_multilingual_XLSum"
headers = {"Authorization": f"Bearer {os.getenv('SUMMARIZER_API_TOKEN')} "}


def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()


def titlefinder(s):
    words = s.split()
    return ' '.join(words[:2])


@app.route('/predict', methods=['POST'])
@jwt_required()
def predict():
    data = request.json
    if 'input' not in data:
        return jsonify({'error': 'No text provided'}), 400
    # Token Validation
    # Check blacklist before processing the request
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Missing Authorization header'}), 401
    token = auth_header.split()[1]
    is_blacklisted = mongo.db.token_blacklist.find_one({'token': token})
    if is_blacklisted:
        return jsonify({'error': 'Token is blacklisted'}), 401
    # Input Assignment
    user_input = data['input']
    user_id = ObjectId(data.get('user_id'))
    # Prediction
    processed_input = custom_standardization(tf.constant([user_input]))
    vectorized_input = vectorize_layer(processed_input)
    prediction = model.predict(vectorized_input)
    predicted_class_index = np.argmax(prediction)
    output = int_to_str[predicted_class_index]
    summary = query(user_input)
    formatted_summary = summary[0]['summary_text']
    # Current Time
    current_time = datetime.now(pytz.utc)
    formatted_time = current_time.strftime(
        '%Y-%m-%dT%H:%M:%S.%f')[:-3] + current_time.strftime('%z')
    formatted_time = formatted_time[:-2] + ':' + formatted_time[-2:]
    # Event Log structure
    log = {
        'corpus': user_input,
        'event': output,
        'title': titlefinder(formatted_summary),
        'summary': formatted_summary,
        'user_id': user_id,
        'created': formatted_time
    }

    mongo.db.eventlogs.insert_one(log)
    return jsonify({
        'result': output,
        'summary': formatted_summary
    })


# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
