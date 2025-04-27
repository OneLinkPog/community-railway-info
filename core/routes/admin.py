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
        operator = next((op for op in operators if user['id'] in op['users']), None)

    return render_template(
        'admin.html',
        user=user,
        operator=operator,
        admin=True,
        lines=lines
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
    

@admin.route("/admin/settings")
def admin_settings():
    user = session.get('user')

    if not user or user.get('id') not in config.web_admins:
        return redirect(url_for('index.index_route'))

    with open(main_dir + '/config.yml') as f:
        settings = yaml.safe_load(f)

    return render_template(
        'admin/settings.html',
        user=user,
        admin=True,
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

    return render_template(
        'admin/logs.html',
        user=user,
        admin=True,
        logs=logs
    )
    
    
    
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