from flask import Blueprint, session, request
from core.url import *
from core import main_dir
from core.logger import Logger
from core.config import config

import json

api = Blueprint('api', __name__)

logger = Logger("@api")

"""
    --- API Routes ---
    - /api/lines [POST]
    - /api/lines/<name> [PUT]
    - /api/lines/<name> [DELETE]
    - /api/operators/<name> [PUT]
"""


@api.route('/api/lines', methods=['POST'])
async def add_line():
    if not session.get('user'):
        return {'error': 'Unauthorized'}, 401
    
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
                    logger.error(f'[@{session.get("user")["username"]}] Line not found')
                    return {'error': 'Line not found'}, 404
                    
            operator = next((op for op in operators if op['uid'] == line['operator_uid']), None)
            if not operator:
                logger.error(f'[@{session.get("user")["username"]}] Operator not found')
                return {'error': 'Operator not found'}, 404
                
            if session.get('user')['id'] not in operator.get('users', []) and session.get('user')['id'] not in config.web_admins:
                logger.error(f'[@{session.get("user")["username"]}] Not a member of the rail company')
                return {'error': 'Not authorized - must be member of the rail company'}, 401

        return {'success': True}, 200
    except Exception as e:
        logger.error(
            f"[@{session.get("user")["username"]}] Error while adding line: {str(e)}")
        return {'error': str(e)}, 500


@api.route('/api/lines/<name>', methods=['PUT'])
async def update_line(name):
    if not session.get('user'):
        return {'error': 'Not authorized'}, 401
    
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
        
    if session.get('user')['id'] not in operator.get('users', []) and session.get('user')['id'] not in config.web_admins:
        logger.error(f'[@{session.get("user")["username"]}] Not a member of the rail company')
        return {'error': 'Not authorized - must be member of the rail company'}, 401

    try:
        data = request.json

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
                    logger.info(f"[@{session.get('user')['username']}] Updated line {name}. Changes: {change_log}")
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


@api.route('/api/lines/<name>', methods=['DELETE'])
async def delete_line(name):
    if not session.get('user'):
        return {'error': 'Not authorized'}, 401
    
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
        
    if session.get('user')['id'] not in operator.get('users', []) and session.get('user')['id'] not in config.web_admins:
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
        logger.error(
            f"[@{session.get("user")["username"]}] Error while deleting line {name}: {str(e)}")
        return {'error': str(e)}, 500


@api.route('/api/operators/<name>', methods=['PUT'])
async def update_operator(name):
    if not session.get('user'):
        return {'error': 'Not authorized'}, 401
    
    with open(main_dir + '/operators.json', 'r') as f:
        operators = json.load(f)
        
    operator = next((op for op in operators if op['uid'] == name), None)
    if not operator:
        logger.error(f'[@{session.get("user")["username"]}] Operator not found')
        return {'error': 'Operator not found'}, 404
        
    if session.get('user')['id'] not in operator.get('users', []) and session.get('user')['id'] not in config.web_admins:
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
