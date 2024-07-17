from flask import Blueprint
from app import jwt_required, request, ObjectId, jsonify, mongo, json_util

bp = Blueprint('fetchlog', __name__)


@bp.route('/fetchlog', methods=['POST'])
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
            'summary': log.get('summary'),
            'created': log.get('created')
        })
    return json_util.dumps(data), 201
