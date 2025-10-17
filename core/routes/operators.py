from flask import Blueprint, render_template, session, request, redirect, url_for
from core import main_dir
from core.config import config, allowed_tags, allowed_attributes
from core.logger import Logger
from datetime import datetime
from bleach import clean

import json
import requests
import os
import time

logger = Logger("requests")
operators = Blueprint('operators', __name__)


"""
    --- Routes ---
    - /operators
    - /operators/<string:uid>
    - /operators/request
"""


@operators.route('/operators')
def operators_route():
    user = session.get('user')

    with open(main_dir + '/lines.json') as f:
        lines = json.load(f)

    with open(main_dir + '/operators.json') as f:
        operators = json.load(f)

    for operator in operators:
        train_count = sum(1 for line in lines if line.get('operator_uid') == operator['uid'])
        operator['train_count'] = train_count

    operator = None
    admin = False

    if user and 'id' in user:
        operator = [op for op in operators if user['id'] in op['users']]

    if user and user["id"] in config.web_admins:
        admin = True

    return render_template(
        'operators/operators.html',
        user=user,
        admin=admin,
        operator=operator,
        operators=operators,
        lines=lines
    )


@operators.route('/operators/<string:uid>')
def operator_route(uid):
    user = session.get('user')

    with open(main_dir + '/lines.json') as f:
        lines = json.load(f)

    with open(main_dir + '/operators.json') as f:
        operators = json.load(f)

    operator = next((op for op in operators if op['uid'] == uid), None)

    user_operator = None
    admin = False
    member = False
    
    if user and 'id' in user:
        user_operator = [op for op in operators if user['id'] in op['users']]
    
    operator_obj = next((op for op in operators if op['uid'] == uid), None)
    if operator_obj and user and user['id'] in operator_obj['users']:
        member = True
    
    if user and user["id"] in config.web_admins:
        admin = True

    operator_lines = []
    operator_lines = [
        line for line in lines
        if 'operator_uid' in line and line['operator_uid'] == uid
    ]

    default_avatar = "https://cdn.discordapp.com/embed/avatars/0.png"

    AVATAR_CACHE_FILE = os.path.join(main_dir, "operator_avatar_cache.json")
    AVATAR_CACHE_TTL = 60 * 60 * 24

    def get_cached_user_data(user_id):
        if not os.path.exists(AVATAR_CACHE_FILE):
            return None
        try:
            with open(AVATAR_CACHE_FILE) as f:
                cache = json.load(f)
        except Exception:
            return None
        entry = cache.get(user_id)
        if entry and time.time() - entry.get("timestamp", 0) < AVATAR_CACHE_TTL:
            return entry["data"]
        return None

    def set_cached_user_data(user_id, data):
        if os.path.exists(AVATAR_CACHE_FILE):
            try:
                with open(AVATAR_CACHE_FILE) as f:
                    cache = json.load(f)
            except Exception:
                cache = {}
        else:
            cache = {}
        cache[user_id] = {"data": data, "timestamp": time.time()}
        with open(AVATAR_CACHE_FILE, "w") as f:
            json.dump(cache, f)

    if operator and 'users' in operator:
        operator['user_datas'] = []
        
        for user_id in operator['users']:
            user_data = get_cached_user_data(user_id)
            
            if not user_data:
                try:
                    user_data = requests.get(f"https://avatar-cyan.vercel.app/api/{user_id}", timeout=4).json()
                except Exception:
                    user_data = {
                        "avatarUrl": default_avatar,
                        "username": user_id,
                        "display_name": user_id
                    }
                set_cached_user_data(user_id, user_data)
                
            operator['user_datas'].append({
                'id': user_id,
                'avatar_url': user_data.get("avatarUrl", default_avatar).replace("?size=512", "?size=32"),
                'username': user_data.get("username", user_id),
                'display_name': user_data.get("display_name", user_id),
            })

    for line in operator_lines:
        line['notice'] = clean(
            line['notice'],
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )

        line['notice'] = line['notice'].rstrip()

        if 'stations' in line:
            line['stations'] = [clean(station, tags=allowed_tags, attributes=allowed_attributes,
                                      strip=True) for station in line['stations']]

    return render_template(
        'operators/overview.html',
        user=user,
        operator=user_operator,
        operator_overview=operator,
        admin=admin,
        operator_lines=operator_lines,
        member=member,
    )


@operators.route('/request')
def request_operator_page():
    user = session.get('user')

    if not user:
        return redirect(url_for('auth.login'))

    with open(main_dir + '/operators.json') as f:
        operators = json.load(f)

    operator = next((op for op in operators if user['id'] in op['users']), None)

    if operator:
        return render_template('operators/request.html', error="You are already part of an operator")

    return render_template('operators/request.html', user=user)


"""
    --- API Endpoints ---
    - /api/operators/request
"""


@operators.route('/api/operators/request', methods=['POST'])
def request_operator():
    if not session.get('user'):
        return {'error': 'Not authorized'}, 401

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
