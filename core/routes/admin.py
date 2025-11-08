from flask import Blueprint, render_template, redirect, url_for, session
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
        settings = yaml.load(f, Loader=yaml.SafeLoader)

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

    parsed_logs = []
    for log in logs:
        parts = log.split(' - ', 1)
        if len(parts) == 2:
            timestamp = parts[0]
            rest = parts[1].split(' - ', 1)
            message = rest[1] if len(rest) > 1 else rest[0]
            parsed_logs.append((timestamp, message))
        else:
            parsed_logs.append(('', log))

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
        logs=parsed_logs
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


