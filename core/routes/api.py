from flask import Blueprint, jsonify, session, request
from core import main_dir
from core.logger import Logger
from core.config import config
from core.sql import sql
from datetime import datetime

import json
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
        query = """
        SELECT 
            l.id,
            l.name,
            l.color,
            l.status,
            l.type,
            l.notice,
            o.name as operator_name,
            o.uid as operator_uid,
            GROUP_CONCAT(DISTINCT s.name ORDER BY ls.station_order SEPARATOR '||') as stations
        FROM line l
        LEFT JOIN operator o ON l.operator_id = o.id
        LEFT JOIN line_station ls ON l.id = ls.line_id
        LEFT JOIN station s ON ls.station_id = s.id
        GROUP BY l.id, l.name, l.color, l.status, l.type, l.notice, o.name, o.uid
        ORDER BY l.name
        """
        
        results = sql.execute_query(query)
        
        lines = []
        for row in results:
            comp_query = """
            SELECT c.parts, c.name as comp_name
            FROM line_composition lc
            JOIN composition c ON lc.composition_id = c.id
            WHERE lc.line_id = %s
            ORDER BY c.id
            """
            compositions_raw = sql.execute_query(comp_query, (row['id'],))
            
            compositions = []
            for comp in compositions_raw:
                compositions.append({
                    'name': comp['comp_name'] or '',
                    'parts': comp['parts']
                })
            
            line = {
                'name': row['name'],
                'color': row['color'],
                'status': row['status'] or 'Running',
                'type': row['type'] or 'public',
                'notice': row['notice'] or '',
                'stations': row['stations'].split('||') if row['stations'] else [],
                'compositions': compositions,
                'operator': row['operator_name'] or '',
                'operator_uid': row['operator_uid'] or ''
            }
            lines.append(line)
        
        return jsonify({'success': True, 'lines': lines}), 200
    
    except Exception as e:
        logger.error(f"Error while fetching lines from database: {str(e)}")
        try:
            with open(main_dir + '/lines.json', 'r') as f:
                lines = json.load(f)
            return jsonify({'success': True, 'lines': lines}), 200
        
        except Exception as json_error:
            logger.error(f"Error while fetching lines from JSON: {str(json_error)}")
            return jsonify({'success': False, 'error': str(e)}), 500


# POST /api/lines
@api.route('/api/lines', methods=['POST'])
async def add_line():
    if not session.get('user'):
        return {'error': 'Unauthorized'}, 401
    
    if config.readonly:
        logger.warning(f'[@{session.get("user")["username"]}] Attempted to add line in readonly mode')
        return {'error': 'System is in readonly mode'}, 403
    
    with open(main_dir + '/operators.json', 'r') as f:
        operators = json.load(f)

    try:
        data = request.json

        required_fields = ['name', 'color', 'status', 'operator_uid', 'type']
        for field in required_fields:
            if field not in data:
                logger.error(
                    f'[@{session.get("user")["username"]}] Missing field: {field}')
                return {'error': f'Missing field: {field}'}, 400

        allowed_types = ['public', 'private', 'metro', 'tram', 'bus']
        if data['type'] not in allowed_types:
            logger.error(
                f'[@{session.get("user")["username"]}] Invalid line type: {data["type"]}')
            return {'error': f'Invalid line type. Must be one of: {", ".join(allowed_types)}'}, 400

        # Handle both old 'composition' and new 'compositions' format
        if 'composition' in data and 'compositions' not in data:
            # Convert old single composition to new array format
            if data['composition']:
                data['compositions'] = [data['composition']]
            else:
                data['compositions'] = []
            del data['composition']

        with open(main_dir + '/lines.json', 'r+') as f:
            lines = json.load(f)

            if any(line.get('name') == data['name'] for line in lines):
                logger.error(
                    f'[@{session.get("user")["username"]}] A line with that name already exists')
                return {'error': 'A line with that name already exists'}, 400

            logger.info(f'[@{session.get("user")["username"]}] Added new line: {data["name"]} (Type: {data["type"]})')
            lines.append(data)
            f.seek(0)
            json.dump(lines, f, indent=2)
            f.truncate()
            
            with open(main_dir + '/lines.json', 'r') as f:
                lines = json.load(f)
                line = next((line for line in lines if line.get('name') == data["name"]), None)
                if not line:
                    logger.error(
                        f'[@{session.get("user")["username"]}] Line "{data["name"]}" not found after adding. '
                        'Possible write error or corrupted lines.json.'
                    )
                    return {
                        'error': (
                            f'Line "{data["name"]}" was not found after adding. '
                            'Please check if lines.json is valid and writable.'
                        )
                    }, 500
                    
            operator = next((op for op in operators if op['uid'] == line['operator_uid']), None)
            if not operator:
                logger.error(f'[@{session.get("user")["username"]}] Operator not found')
                return {'error': 'Operator not found'}, 404
                
            if session.get('user')['id'] not in operator.get('users', []):
                logger.error(f'[@{session.get("user")["username"]}] Not a member of the rail company')
                return {'error': 'Not authorized - must be member of the rail company'}, 401

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
    
    with open(main_dir + '/operators.json', 'r') as f:
        operators = json.load(f)
    
    with open(main_dir + '/lines.json', 'r') as f:
        lines = json.load(f)
        line = next((line for line in lines if line.get('name') == name), None)
        if not line:
            logger.error(f'[@{session.get("user")["username"]}] Line not found')
            return {'error': 'Line not found'}, 404
            
    operator = next((op for op in operators if op['uid'] == line['operator_uid']), None)
    if not operator:
        logger.error(f'[@{session.get("user")["username"]}] Operator not found')
        return {'error': 'Operator not found'}, 404
        
    if session.get('user')['id'] not in operator.get('users', []):
        logger.error(f'[@{session.get("user")["username"]}] Not a member of the rail company')
        return {'error': 'Not authorized - must be member of the rail company'}, 401

    try:
        data = request.json

        if 'composition' in data and 'compositions' not in data:
            if data['composition']:
                data['compositions'] = [data['composition']]
            else:
                data['compositions'] = []
            del data['composition']

        with open(main_dir + '/lines.json', 'r+') as f:
            lines = json.load(f)
            
            old_line = None
            for line in lines:
                if line.get('name') == name:
                    old_line = line.copy()
                    break

            line_updated = False
            for i, line in enumerate(lines):
                if line.get('name') == name:
                    # Preserve operator data
                    data['operator'] = line.get('operator')
                    data['operator_uid'] = line.get('operator_uid')
                    lines[i] = data
                    line_updated = True
                    
                    changes = []
                    for key in data:
                        if key in old_line and data[key] != old_line[key]:
                            changes.append(f"{key}: {old_line[key]} -> {data[key]}")
                    
                    change_log = ", ".join(changes) if changes else "no changes"
                    logger.info(f"[@{session.get('user')['username']}] Updated line {name}. Changes: {change_log.replace(chr(10), ' ').replace(chr(13), ' ')}")
                    break

            if not line_updated:
                logger.info(
                    f"[@{session.get('user')['username']}] Line {name} not found")
                return {'error': f'Line {name} not found'}, 404

            f.seek(0)
            json.dump(lines, f, indent=2)
            f.truncate()

        return {'success': True}, 200

    except Exception as e:
        logger.error(
            f"[@{session.get('user')['username']}] Error while updating line {name}: {str(e)}")
        return {'error': str(e)}, 500


# DELETE /api/lines/<name>
@api.route('/api/lines/<name>', methods=['DELETE'])
async def delete_line(name):
    if not session.get('user'):
        return {'error': 'Not authorized'}, 401
    
    
    if config.readonly:
        logger.warning(f'[@{session.get("user")["username"]}] Attempted to delete line in readonly mode')
        return {'error': 'System is in readonly mode'}, 403
    
    with open(main_dir + '/operators.json', 'r') as f:
        operators = json.load(f)
        
    with open(main_dir + '/lines.json', 'r') as f:
        lines = json.load(f)
        line = next((line for line in lines if line.get('name') == name), None)
        if not line:
            logger.error(f'[@{session.get("user")["username"]}] Line not found')
            return {'error': 'Line not found'}, 404
            
    operator = next((op for op in operators if op['uid'] == line['operator_uid']), None)
    if not operator:
        logger.error(f'[@{session.get("user")["username"]}] Operator not found')
        return {'error': 'Operator not found'}, 404
        
    if session.get('user')['id'] not in operator.get('users', []):
        logger.error(f'[@{session.get("user")["username"]}] Not a member of the rail company')
        return {'error': 'Not authorized - must be member of the rail company'}, 401

    try:
        with open(main_dir + '/lines.json', 'r+') as f:
            lines = json.load(f)
            lines = [line for line in lines if line.get('name') != name]
            f.seek(0)
            json.dump(lines, f, indent=2)
            f.truncate()

        logger.info(
            f"[@{session.get('user')['username']}] Deleted line {name} successfully.")
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
        operators_query = """
        SELECT o.id, o.name, o.color, o.short, o.uid
        FROM operator o
        ORDER BY o.name
        """
        operators_raw = sql.execute_query(operators_query)
        
        operators = []
        for op in operators_raw:
            users_query = """
            SELECT u.id
            FROM operator_user ou
            JOIN user u ON ou.user_id = u.id
            WHERE ou.operator_id = %s
            """
            users_raw = sql.execute_query(users_query, (op['id'],))
            
            operator = {
                'name': op['name'],
                'color': op['color'] or '#808080',
                'users': [str(user['id']) for user in users_raw],
                'short': op['short'] or '',
                'uid': op['uid']
            }
            operators.append(operator)
        
        return jsonify(operators), 200
    
    except Exception as e:
        logger.error(f"Error while fetching operators from database: {str(e)}")


# PUT /api/operators/<name>
@api.route('/api/operators/<name>', methods=['PUT'])
async def update_operator(name):
    if not session.get('user'):
        return {'error': 'Not authorized'}, 401
    
    
    if config.readonly:
        logger.warning(f'[@{session.get("user")["username"]}] Attempted to update operator in readonly mode')
        return {'error': 'System is in readonly mode'}, 403
    
    with open(main_dir + '/operators.json', 'r') as f:
        operators = json.load(f)
        
    operator = next((op for op in operators if op['uid'] == name), None)
    if not operator:
        logger.error(f'[@{session.get("user")["username"]}] Operator not found')
        return {'error': 'Operator not found'}, 404
        
    if session.get('user')['id'] not in operator.get('users', []):
        logger.error(f'[@{session.get("user")["username"]}] Not a member of the rail company')
        return {'error': 'Not authorized - must be member of the rail company'}, 401

    try:
        data = request.json
        logger.info(
            f"[@{session.get('user')['username']}] Updating operator {name} with data: {data}")

        with open(main_dir + '/operators.json', 'r+') as f:
            operators = json.load(f)

            operator_updated = False
            for i, operator in enumerate(operators):
                if operator.get('uid') == name:
                    data['uid'] = operator['uid']
                    operators[i] = data
                    operator_updated = True
                    logger.info(
                        f"[@{session.get('user')['username']}] Operator {name} updated successfully with new data: {operators[i]}")
                    break

            if not operator_updated:
                logger.info(
                    f"[@{session.get('user')['username']}] Operator {name} not found")
                return {'error': f'Operator {name} not found'}, 404

            f.seek(0)
            json.dump(operators, f, indent=2)
            f.truncate()

        return {'success': True}, 200

    except Exception as e:
        logger.error(
            f"[@{session.get('user')['username']}] Error while updating operator {name}: {str(e)}")
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
            'timestamp': datetime.now().isoformat(),
            'status': 'pending',
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

        requests_file = main_dir + '/operator_requests.json'

        try:
            with open(requests_file, 'r') as f:
                requests = json.load(f)
        except FileNotFoundError:
            requests = []

        requests.append(request_data)

        with open(requests_file, 'w') as f:
            json.dump(requests, f, indent=2)

        logger.info(f"New Company request by @{user['username']}")
        return {'success': True}, 200

    except Exception as e:
        logger.error(f"Error while requesting new company: {str(e)}")
        return {'error': str(e)}, 500



"""
    --- STATION ROUTES ---
"""

# GET /api/stations
@api.route('/api/stations')
def get_stations():
    query = """SELECT * FROM station ORDER BY id"""
    try:
        results = sql.execute_query(query)
        return {'stations': results}, 200
    except Exception as e:
        logger.error(f"[@{session.get('user')['username']}] Error while fetching stations: {str(e)}")
        return {'error': str(e)}, 500



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

        with open(main_dir + '/operator_requests.json', 'r') as f:
            requests = json.load(f)

        request_data = next(
            (req for req in requests if req['timestamp'] == timestamp), None)

        if not request_data:
            return jsonify({'error': 'Request not found'}), 404

        if action == 'accept':
            new_operator = {
                'name': request_data['company_name'],
                'short_code': request_data['short_code'],
                'uid': request_data['company_uid'].lower(),
                'color': request_data['color'],
                'users': [request_data['requester']['id']] + request_data['additional_users']
            }

            with open(main_dir + '/operators.json', 'r+') as f:
                operators = json.load(f)
                operators.append(new_operator)
                f.seek(0)
                json.dump(operators, f, indent=2)
                f.truncate()

        request_data['status'] = 'accepted' if action == 'accept' else 'rejected'

        with open(main_dir + '/operator_requests.json', 'w') as f:
            json.dump(requests, f, indent=2)

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


