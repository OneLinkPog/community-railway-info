from flask import Blueprint, jsonify, render_template, session, redirect, url_for, request
from core import main_dir
from core.logger import Logger
from core.config import config

import json
import yaml

admin = Blueprint('admin', __name__)

logger = Logger('admin')


@admin.route('/admin')
def admin_route():
    user = session.get('user')

    if not user or user.get('id') not in config.web_admins:
        return redirect(url_for('index.index_route'))

    with open(main_dir + '/lines.json') as f:
        lines = json.load(f)

    with open(main_dir + '/operators.json') as f:
        operators = json.load(f)

    operator = None
    if user and 'id' in user:
        operator = [op for op in operators if user['id'] in op['users']]

    return render_template(
        'admin/admin.html',
        user=user,
        operator=operator,
        admin=True,
        lines=lines
    )
    
    
@admin.route("/admin/settings")
def admin_settings():
    user = session.get('user')

    if not user or user.get('id') not in config.web_admins:
        return redirect(url_for('index.index_route'))

    with open(main_dir + '/config.yml') as f:
        settings = yaml.safe_load(f)
        
    with open(main_dir + '/operators.json') as f:
        operators = json.load(f)

    operator = None
    if user and 'id' in user:
        operator = [op for op in operators if user['id'] in op['users']]

    return render_template(
        'admin/settings.html',
        user=user,
        admin=True,
        operator=operator,
        config=settings
    )


@admin.route('/admin/logs')
def admin_logs():
    user = session.get('user')

    if not user or user.get('id') not in config.web_admins:
        return redirect(url_for('index.index_route'))

    with open(main_dir + '/server.log') as f:
        logs = f.readlines()
        
    logs = [log.strip() for log in logs if log.strip()]
    logs = [log.split(' - ', 1) for log in logs]
    logs = [(log[0], log[1].split(' - ', 1)[1] if len(log) > 1 else '') for log in logs]
    
    logger.admin(f'[@{session.get("user")["username"]}] Accessed server logs')
    
    with open(main_dir + '/operators.json') as f:
        operators = json.load(f)

    operator = None
    if user and 'id' in user:
        operator = [op for op in operators if user['id'] in op['users']]

    return render_template(
        'admin/logs.html',
        user=user,
        admin=True,
        operator=operator,
        logs=logs
    )
    
@admin.route('/admin/companies')
def admin_companies():
    user = session.get('user')

    if not user or user.get('id') not in config.web_admins:
        return redirect(url_for('index.index_route'))
    
    with open(main_dir + '/operators.json') as f:
        operators = json.load(f)

    operator = None
    if user and 'id' in user:
        operator = [op for op in operators if user['id'] in op['users']]

    try:
        with open(main_dir + '/operator_requests.json', 'r') as f:
            requests = json.load(f)
        
        requests.sort(key=lambda x: x['timestamp'], reverse=True)
        
        with open(main_dir + '/operators.json') as f:
            operators = json.load(f)

        return render_template(
            'admin/companies.html',
            user=user,
            admin=True,
            operator=operator,
            requests=requests
        )
    except FileNotFoundError:
        return render_template(
            'admin/companies.html',
            user=user,
            admin=True,
            operator=operator,
            requests=[]
        )
        
    
@admin.route('/admin/settings/update', methods=['POST'])
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
            config_data = yaml.safe_load(f)

        config_data['port'] = data['port']
        config_data['debug'] = data['debug']
        config_data['web_admins'] = data['web_admins']
        config_data['maintenance_mode'] = data['maintenance_mode']
        config_data['maintenance_message'] = data['maintenance_message']

        with open(main_dir + '/config.yml', 'w') as f:
            yaml.safe_dump(config_data, f, default_flow_style=False)
            
        config.load()

        logger.admin(f'[@{session.get("user")["username"]}] Updated application settings')
        return jsonify({'success': True})

    except Exception as e:
        logger.error(f'[@{session.get("user")["username"]}] Error updating settings: {str(e)}')
        return jsonify({'error': str(e)}), 500
    
@admin.route('/admin/clear-logs', methods=['POST'])
def clear_logs():
    user = session.get('user')
    
    if not user or user.get('id') not in config.web_admins:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        open(main_dir + '/server.log', 'w').close()
        logger.admin(f'[@{session.get("user")["username"]}] Server logs cleared successfully.')
        return jsonify({'success': True})
    
    except Exception as e:
        logger.admin(f'[@{session.get("user")["username"]}] Error clearing server logs: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500
    
    
@admin.route('/admin/update-logs')
def update_logs():
    user = session.get('user')

    if not user or user.get('id') not in config.web_admins:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        with open(main_dir + '/server.log') as f:
            logs = f.readlines()
            
        logs = [log.strip() for log in logs if log.strip()]
        logs = [log.split(' - ', 1) for log in logs]
        logs = [(log[0], log[1].split(' - ', 1)[1] if len(log) > 1 else '') for log in logs]
        
        return jsonify({'success': True, 'logs': logs})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin.route('/admin/companies/handle-request', methods=['POST'])
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

        request_data = next((req for req in requests if req['timestamp'] == timestamp), None)
        
        if not request_data:
            return jsonify({'error': 'Request not found'}), 404

        if action == 'accept':
            new_operator = {
                'name': request_data['company_name'],
                'short_code': request_data['short_code'].lower(),
                'uid': request_data['short_code'].lower(),
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
