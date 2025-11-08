from flask import Blueprint, jsonify, session, request
from core import main_dir
from core.logger import Logger
from core.config import config
from core.controller import LineController, OperatorController, StationController, OperatorRequestController

import yaml

api = Blueprint('api', __name__)
logger = Logger("@api")

"""
    --- API Routes ---
    - /api/lines [GET]
    - /api/lines [POST]
    - /api/lines/<name> [PUT]
    - /api/lines/<name> [DELETE]
    - /api/operators [GET]
    - /api/operators/<name> [PUT]
    - /api/operators/request [POST]
    - /api/stations [GET]
    - /api/admin/logs [GET]     
    - /api/admin/settings/update [POST]
    - /api/admin/companies/handle-request [POST]
"""


"""
    --- LINE ROUTES ---
"""


# GET /api/lines
@api.route('/api/lines', methods=['GET'])
async def get_lines():
    try:
        lines = LineController.get_all_lines()
        return jsonify({'success': True, 'lines': lines}), 200
    except Exception as e:
        logger.error(f"Error while fetching lines: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# POST /api/lines
@api.route('/api/lines', methods=['POST'])
async def add_line():
    if not session.get('user'):
        return {'error': 'Unauthorized'}, 401
    
    if config.readonly:
        logger.warning(f'[@{session.get("user")["username"]}] Attempted to add line in readonly mode')
        return {'error': 'System is in readonly mode'}, 403

    try:
        data = request.json

        required_fields = ['name', 'color', 'status', 'operator_uid', 'type']
        for field in required_fields:
            if field not in data:
                logger.error(f'[@{session.get("user")["username"]}] Missing field: {field}')
                return {'error': f'Missing field: {field}'}, 400

        allowed_types = ['public', 'private', 'metro', 'tram', 'bus']
        if data['type'] not in allowed_types:
            logger.error(f'[@{session.get("user")["username"]}] Invalid line type: {data["type"]}')
            return {'error': f'Invalid line type. Must be one of: {", ".join(allowed_types)}'}, 400

        if 'composition' in data and 'compositions' not in data:
            if data['composition']:
                data['compositions'] = [data['composition']]
            else:
                data['compositions'] = []
            del data['composition']

        if LineController.line_exists(data['name']):
            logger.error(f'[@{session.get("user")["username"]}] A line with that name already exists')
            return {'error': 'A line with that name already exists'}, 400
        
        operator = OperatorController.get_operator_by_uid(data['operator_uid'])
        if not operator:
            logger.error(f'[@{session.get("user")["username"]}] Operator not found')
            return {'error': 'Operator not found'}, 404
        
        # Check if user is admin or member of the rail company
        user_id = session.get('user')['id']
        is_admin = user_id in config.web_admins
        is_member = user_id in operator.get('users', [])
        
        if not is_admin and not is_member:
            logger.error(f'[@{session.get("user")["username"]}] Not a member of the rail company')
            return {'error': 'Not authorized - must be member of the rail company'}, 401

        line_id = LineController.create_line(data)
        if not line_id:
            logger.error(f"[@{session.get('user')['username']}] Failed to create line")
            return {'error': 'Failed to create line'}, 500

        logger.info(f'[@{session.get("user")["username"]}] Added new line: {data["name"]} (Type: {data["type"]})')
        return {'success': True}, 200

    except Exception as e:
        logger.error(f"[@{session.get('user')['username']}] Error while adding line: {str(e)}")
        return {'error': str(e)}, 500


# PUT /api/lines/<name>
@api.route('/api/lines/<name>', methods=['PUT'])
async def update_line(name):
    if not session.get('user'):
        return {'error': 'Not authorized'}, 401
    
    if config.readonly:
        logger.warning(f'[@{session.get("user")["username"]}] Attempted to update line in readonly mode')
        return {'error': 'System is in readonly mode'}, 403

    try:
        line = LineController.get_line_by_name(name)
        if not line:
            logger.error(f'[@{session.get("user")["username"]}] Line not found')
            return {'error': 'Line not found'}, 404
        
        operator = OperatorController.get_operator_by_uid(line['operator_uid'])
        if not operator:
            logger.error(f'[@{session.get("user")["username"]}] Operator not found')
            return {'error': 'Operator not found'}, 404
        
        # Check if user is admin or member of the rail company
        user_id = session.get('user')['id']
        is_admin = user_id in config.web_admins
        is_member = user_id in operator.get('users', [])
        
        if not is_admin and not is_member:
            logger.error(f'[@{session.get("user")["username"]}] Not a member of the rail company')
            return {'error': 'Not authorized - must be member of the rail company'}, 401

        data = request.json

        if 'composition' in data and 'compositions' not in data:
            if data['composition']:
                data['compositions'] = [data['composition']]
            else:
                data['compositions'] = []
            del data['composition']

        if 'operator_uid' not in data:
            data['operator_uid'] = line['operator_uid']

        changes = []
        for key in data:
            if key in line and data[key] != line[key]:
                old_val = str(line[key])[:50]
                new_val = str(data[key])[:50]
                changes.append(f"{key}: {old_val} -> {new_val}")
        
        change_log = ", ".join(changes) if changes else "no changes"
        
        success = LineController.update_line(name, data)
        if not success:
            logger.error(f"[@{session.get('user')['username']}] Failed to update line {name}")
            return {'error': 'Failed to update line'}, 500

        logger.info(f"[@{session.get('user')['username']}] Updated line {name}. Changes: {change_log.replace(chr(10), ' ').replace(chr(13), ' ')}")
        return {'success': True}, 200

    except Exception as e:
        logger.error(f"[@{session.get('user')['username']}] Error while updating line {name}: {str(e)}")
        return {'error': str(e)}, 500


# DELETE /api/lines/<name>
@api.route('/api/lines/<name>', methods=['DELETE'])
async def delete_line(name):
    if not session.get('user'):
        return {'error': 'Not authorized'}, 401
    
    if config.readonly:
        logger.warning(f'[@{session.get("user")["username"]}] Attempted to delete line in readonly mode')
        return {'error': 'System is in readonly mode'}, 403

    try:
        line = LineController.get_line_by_name(name)
        if not line:
            logger.error(f'[@{session.get("user")["username"]}] Line not found')
            return {'error': 'Line not found'}, 404
        
        operator = OperatorController.get_operator_by_uid(line['operator_uid'])
        if not operator:
            logger.error(f'[@{session.get("user")["username"]}] Operator not found')
            return {'error': 'Operator not found'}, 404
        
        # Check if user is admin or member of the rail company
        user_id = session.get('user')['id']
        is_admin = user_id in config.web_admins
        is_member = user_id in operator.get('users', [])
        
        if not is_admin and not is_member:
            logger.error(f'[@{session.get("user")["username"]}] Not a member of the rail company')
            return {'error': 'Not authorized - must be member of the rail company'}, 401

        success = LineController.delete_line(name)
        if not success:
            logger.error(f"[@{session.get('user')['username']}] Failed to delete line {name}")
            return {'error': 'Failed to delete line'}, 500

        logger.info(f"[@{session.get('user')['username']}] Deleted line {name} successfully.")
        return {'success': True}, 200

    except Exception as e:
        logger.error(f"[@{session.get('user')['username']}] Error while deleting line {name}: {str(e)}")
        return {'error': str(e)}, 500



"""
    --- OPERATOR ROUTES ---
"""

# GET /api/operators
@api.route('/api/operators', methods=['GET'])
async def get_operators():
    try:
        operators = OperatorController.get_all_operators()
        return jsonify(operators), 200
    except Exception as e:
        logger.error(f"Error while fetching operators: {str(e)}")
        return jsonify({'error': str(e)}), 500


# PUT /api/operators/<name>
@api.route('/api/operators/<name>', methods=['PUT'])
async def update_operator(name):
    if not session.get('user'):
        return {'error': 'Not authorized'}, 401
    
    if config.readonly:
        logger.warning(f'[@{session.get("user")["username"]}] Attempted to update operator in readonly mode')
        return {'error': 'System is in readonly mode'}, 403

    try:
        operator = OperatorController.get_operator_by_uid(name)
        if not operator:
            logger.error(f'[@{session.get("user")["username"]}] Operator not found')
            return {'error': 'Operator not found'}, 404
        
        # Check if user is admin or member of the rail company
        user_id = session.get('user')['id']
        is_admin = user_id in config.web_admins
        is_member = user_id in operator.get('users', [])
        
        if not is_admin and not is_member:
            logger.error(f'[@{session.get("user")["username"]}] Not a member of the rail company')
            return {'error': 'Not authorized - must be member of the rail company'}, 401

        data = request.json
        logger.info(f"[@{session.get('user')['username']}] Updating operator {name} with data: {data}")

        success = OperatorController.update_operator(name, data)
        if not success:
            logger.error(f"[@{session.get('user')['username']}] Failed to update operator {name}")
            return {'error': 'Failed to update operator'}, 500

        logger.info(f"[@{session.get('user')['username']}] Operator {name} updated successfully")
        return {'success': True}, 200

    except Exception as e:
        logger.error(f"[@{session.get('user')['username']}] Error while updating operator {name}: {str(e)}")
        return {'error': str(e)}, 500
    

# POST /api/operators/request
@api.route('/api/operators/request', methods=['POST'])
def request_operator():
    if not session.get('user'):
        return {'error': 'Not authorized'}, 401

    if config.readonly:
        logger.warning(f'[@{session.get("user")["username"]}] Attempted to request operator in readonly mode')
        return {'error': 'System is in readonly mode'}, 403

    try:
        data = request.json
        user = session.get('user')

        request_data = {
            'requester': {
                'id': user['id'],
                'username': user['username']
            },
            'company_name': data['companyName'],
            'short_code': data['shortCode'],
            'color': data['color'],
            'additional_users': data['additionalUsers'],
            'company_uid': data['companyUid']
        }

        success = OperatorRequestController.create_request(request_data)
        
        if not success:
            logger.error(f"[@{user['username']}] Failed to create operator request")
            return {'error': 'Failed to create request'}, 500

        logger.info(f"New Company request by @{user['username']}")
        return {'success': True}, 200

    except Exception as e:
        logger.error(f"Error while requesting new company: {str(e)}")
        return {'error': str(e)}, 500



"""
    --- STATION ROUTES ---
"""

# GET /api/stations
@api.route('/api/stations', methods=['GET'])
def get_stations():
    try:
        stations = StationController.get_all_stations()
        return jsonify(stations)
    except Exception as e:
        logger.error(f"Error while fetching stations: {str(e)}")
        return jsonify({'error': str(e)}), 500


# GET /api/stations/<name>
@api.route('/api/stations/<name>', methods=['GET'])
def get_station_details(name):
    try:
        station = StationController.get_station_by_name(name)
        if not station:
            return jsonify({'error': 'Station not found'}), 404
        
        # Get lines at this station
        lines = StationController.get_lines_at_station(name)
        
        # Get statistics
        stats = StationController.get_station_statistics(name)
        
        return jsonify({
            'station': station,
            'lines': lines,
            'statistics': stats
        }), 200
    except Exception as e:
        logger.error(f"Error while fetching station details: {str(e)}")
        return jsonify({'error': str(e)}), 500


# GET /api/stations/search/<term>
@api.route('/api/stations/search/<term>', methods=['GET'])
def search_stations(term):
    try:
        stations = StationController.search_stations(term)
        return jsonify({'stations': stations}), 200
    except Exception as e:
        logger.error(f"Error while searching stations: {str(e)}")
        return jsonify({'error': str(e)}), 500



"""
    --- ADMIN ROUTES ---
"""

# GET /api/admin/logs
@api.route('/api/admin/logs')
def update_logs():
    user = session.get('user')

    if not user or user.get('id') not in config.web_admins:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        with open(main_dir + '/server.log') as f:
            logs = f.readlines()

        logs = [log.strip() for log in logs if log.strip()]
        logs = [log.split(' - ', 1) for log in logs]
        logs = [(log[0], log[1].split(' - ', 1)[1] if len(log) > 1 else '')
                for log in logs]

        return jsonify({'success': True, 'logs': logs})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# POST /api/admin/companies/handle-request
@api.route('/api/admin/companies/handle-request', methods=['POST'])
def handle_company_request():
    user = session.get('user')

    if not user or user.get('id') not in config.web_admins:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        data = request.json
        timestamp = data.get('timestamp')
        action = data.get('action')

        if not timestamp or action not in ['accept', 'reject']:
            return jsonify({'error': 'Invalid request'}), 400

        request_data = OperatorRequestController.get_request_by_timestamp(timestamp)
        
        if not request_data:
            return jsonify({'error': 'Request not found'}), 404

        if action == 'accept':
            new_operator_data = {
                'name': request_data['company_name'],
                'short': request_data['short_code'],
                'uid': request_data['company_uid'].lower(),
                'color': request_data['color'],
                'users': [request_data['requester']['id']] + request_data['additional_users']
            }

            operator_id = OperatorController.create_operator(new_operator_data)
            if not operator_id:
                logger.error(f"[@{user['username']}] Failed to create operator for request")
                return jsonify({'error': 'Failed to create operator'}), 500

        success = OperatorRequestController.update_request_status(timestamp, 'accepted' if action == 'accept' else 'rejected')
        
        if not success:
            logger.error(f"[@{user['username']}] Failed to update request status")
            return jsonify({'error': 'Failed to update request status'}), 500

        logger.admin(f"[@{user['username']}] {action.capitalize()}ed operator request for {request_data['company_name']}")
        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"[@{user['username']}] Error handling operator request: {str(e)}")
        return jsonify({'error': str(e)}), 500


# POST /api/admin/settings/update
@api.route('/api/admin/settings/update', methods=['POST'])
def save_settings():
    user = session.get('user')

    if not user or user.get('id') not in config.web_admins:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        data = request.json

        if not isinstance(data.get('port'), int) or data['port'] < 1 or data['port'] > 65535:
            return jsonify({'error': 'Invalid port number'}), 400

        if not isinstance(data.get('web_admins'), list):
            return jsonify({'error': 'Invalid web_admins format'}), 400

        with open(main_dir + '/config.yml', 'r') as f:
            config_data = yaml.load(f, Loader=yaml.SafeLoader)

        # Update webserver settings
        if 'webserver' not in config_data:
            config_data['webserver'] = {}
        config_data['webserver']['port'] = data['port']
        config_data['webserver']['debug'] = data['debug']

        # Update administration settings
        if 'administration' not in config_data:
            config_data['administration'] = {}
        config_data['administration']['readonly'] = data['readonly']
        config_data['administration']['web_admins'] = data['web_admins']
        config_data['administration']['maintenance_mode'] = data['maintenance_mode']
        config_data['administration']['maintenance_message'] = data['maintenance_message']

        with open(main_dir + '/config.yml', 'w') as f:
            yaml.dump(
                config_data, 
                f, 
                default_flow_style=False, 
                allow_unicode=True,
                sort_keys=False,
                width=float("inf")
            )

        config.load()

        logger.admin(
            f'[@{session.get("user")["username"]}] Updated application settings')
        return jsonify({'success': True})

    except Exception as e:
        logger.error(
            f'[@{session.get("user")["username"]}] Error updating settings: {str(e)}')
        return jsonify({'error': str(e)}), 500


