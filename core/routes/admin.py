from flask import Blueprint, jsonify, render_template, session, redirect, url_for
from core import main_dir
from core.logger import Logger
from core.config import config

import json

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

    return render_template(
        'admin_logs.html',
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
        logger.info(f'[@{session.get("user")["username"]}] Server logs cleared successfully.')
        return jsonify({'success': True})
    
    except Exception as e:
        logger.error(f'[@{session.get("user")["username"]}] Error clearing server logs: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500