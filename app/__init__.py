from flask import Flask, request, jsonify, render_template
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from flask_pymongo import PyMongo
from bson import json_util, ObjectId
from dotenv import load_dotenv
from datetime import datetime, timedelta
from flask_cors import CORS
import tensorflow as tf
from tensorflow import keras
from urllib.parse import urlparse
from newspaper import Article
import numpy as np
import logging
import pytz
import re
import requests
import string
import os
import chardet
import json
load_dotenv()

mongo = PyMongo()
bcrypt = Bcrypt()
jwt = JWTManager()


def create_app():
    app = Flask(__name__)

    # CORS Validation
    CORS(app, resources={
        r"/*": {"origins": ["http://localhost:5173", 'http://127.0.0.1:5500', 'https://ghotona-chitro.vercel.app']}})

    # App Configuration
    mongo_uri = os.getenv('MONGO_URI')
    app.config["MONGO_URI"] = mongo_uri
    if not app.config["MONGO_URI"]:
        raise ValueError(
            "No MongoDB URI found. Please set the MONGO_URI environment variable in the .env file.")
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=6)
    mongo.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    with app.app_context():
        from .routes import register, login, logout, fetch_log, predict

        # Registering Blueprints
        app.register_blueprint(register.bp)
        app.register_blueprint(login.bp)
        app.register_blueprint(logout.bp)
        app.register_blueprint(fetch_log.bp)
        app.register_blueprint(predict.bp)

    return app
