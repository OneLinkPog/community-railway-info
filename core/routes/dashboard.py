from flask import Blueprint, session, redirect, url_for, render_template, request
from requests_oauthlib import OAuth2Session
from core.config import config, allowed_tags
from core.url import *
from core import main_dir
from core.logger import Logger
from bleach import clean

import json
import requests

dashboard = Blueprint('dashboard', __name__)

logger = Logger("@dashboard")


@dashboard.route('/dashboard')
async def dashboard_view():
    user = session.get('user')

    if not user:
        return redirect(url_for('auth.login'))

    with open(main_dir + '/lines.json') as f:
        lines = json.load(f)

    with open(main_dir + '/operators.json') as f:
        operators = json.load(f)

    operator = None
    admin = False

    if user and 'id' in user:
        operator = next(
            (op for op in operators if user['id'] in op['users']), None)

    if user and user["id"] in config.web_admins:
        admin = True

    if operator is None and not admin:
        return redirect(url_for('index'))

    operator_lines = []
    if operator:
        operator_lines = [
            line for line in lines
            if 'operator_uid' in line and line['operator_uid'] == operator['uid']
        ]

    operators.sort(key=lambda x: x['name'])

    default_avatar = "https://cdn.discordapp.com/embed/avatars/0.png"

    if operator and 'users' in operator:
        operator['user_datas'] = []
        for user_id in operator['users']:
            user_data = "https://avatar-cyan.vercel.app/api/" + user_id

            try:
                user_data = requests.get(user_data).json()
            except Exception:
                user_data = {"avatarUrl": default_avatar}

            operator['user_datas'].append({
                'id': user_id,
                'avatar_url': user_data["avatarUrl"].replace("?size=512", "?size=32"),
                'username': user_data["username"],
                'display_name': user_data["display_name"],
            })
            
    for line in operator_lines:
        line['notice'] = clean(
            line['notice'],
            tags=allowed_tags,
            attributes={},
            strip=True
        )
        
        if 'stations' in line:
            line['stations'] = [clean(station, tags=["del"], attributes={}, strip=True) for station in line['stations']]

    return render_template(
        'dashboard.html',
        user=user,
        operator=operator,
        admin=admin,
        operator_lines=operator_lines
    )


@dashboard.route('/api/lines', methods=['POST'])
async def add_line():
    if not session.get('user'):
        return {'error': 'Unauthorized'}, 401

    try:
        data = request.json

        required_fields = ['name', 'color', 'status', 'operator_uid']
        for field in required_fields:
            if field not in data:
                logger.error(f'[@{session.get("user")["username"]}] Missing field: {field}')
                return {'error': f'Missing field: {field}'}, 400

        with open(main_dir + '/lines.json', 'r+') as f:
            lines = json.load(f)

            if any(line.get('name') == data['name'] for line in lines):
                logger.error(f'[@{session.get("user")["username"]}] A line with that name already exists')
                return {'error': 'A line with that name already exists'}, 400

            logger.info(f'[@{session.get("user")["username"]}] Added new line: {data["name"]}')
            lines.append(data)
            f.seek(0)
            json.dump(lines, f, indent=2)
            f.truncate()

        return {'success': True}, 200
    except Exception as e:
        logger.error(f"[@{session.get("user")["username"]}] Error while adding line: {str(e)}")
        return {'error': str(e)}, 500


@dashboard.route('/api/lines/<name>', methods=['PUT'])
async def update_line(name):
    if not session.get('user'):
        return {'error': 'Not authorized'}, 401

    try:
        data = request.json
        logger.info(f"[@{session.get("user")["username"]}] Updating line {name} with data: {data}")

        with open(main_dir + '/lines.json', 'r+') as f:
            lines = json.load(f)

            line_updated = False
            for i, line in enumerate(lines):
                if line.get('name') == name:
                    data['operator'] = line.get('operator')
                    data['operator_uid'] = line.get('operator_uid')
                    lines[i] = data
                    line_updated = True
                    logger.info(f"[@{session.get("user")["username"]}] Line {name} updated successfully with new data: {lines[i]}")
                    break

            if not line_updated:
                logger.info(f"[@{session.get('user')['username']}] Line {name} not found")
                return {'error': f'Line {name} not found'}, 404

            f.seek(0)
            json.dump(lines, f, indent=2)
            f.truncate()

        return {'success': True}, 200
    
    except Exception as e:
        logger.error(f"[@{session.get('user')['username']}] Error while updating line {name}: {str(e)}")
        return {'error': str(e)}, 500


@dashboard.route('/api/lines/<name>', methods=['DELETE'])
async def delete_line(name):
    if not session.get('user'):
        return {'error': 'Not authorized'}, 401

    try:
        with open(main_dir + '/lines.json', 'r+') as f:
            lines = json.load(f)
            lines = [line for line in lines if line.get('name') != name]
            f.seek(0)
            json.dump(lines, f, indent=2)
            f.truncate()

        logger.info(f"[@{session.get('user')['username']}] Deleted line {name} successfully.")
        return {'success': True}, 200
    
    except Exception as e:
        logger.error(f"[@{session.get("user")["username"]}] Error while deleting line {name}: {str(e)}")
        return {'error': str(e)}, 500
