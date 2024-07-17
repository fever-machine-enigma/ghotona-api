from flask import Blueprint
from app import jwt_required, request, jsonify, mongo, datetime
bp = Blueprint('logout', __name__)


def blacklist_token(token):
    mongo.db.token_blacklist.insert_one({
        'token': token,
        'blacklisted_at': datetime.utcnow()
    })


@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Missing Authorization header'}), 401
    token = auth_header.split()[1]  # Assuming 'Bearer token' format
    # Blacklist the token
    blacklist_token(token)
    return jsonify({'message': 'Logged out successfully'}), 200
