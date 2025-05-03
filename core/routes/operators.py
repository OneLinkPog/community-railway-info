from flask import Blueprint, render_template, session, redirect, url_for
from core import main_dir
from core.config import config, allowed_tags

import json
import requests
from bleach import clean

operators = Blueprint('operators', __name__)


@operators.route('/operators')
def operators_route():
    user = session.get('user')

    with open(main_dir + '/lines.json') as f:
        lines = json.load(f)

    with open(main_dir + '/operators.json') as f:
        operators = json.load(f)

    for operator in operators:
        train_count = sum(1 for line in lines if line.get(
            'operator_uid') == operator['uid'])
        operator['train_count'] = train_count

    operator = None
    if user and 'id' in user:
        operator = next(
            (op for op in operators if user['id'] in op['users']), None)

    admin = False
    if user and user["id"] in config.web_admins:
        admin = True

    return render_template(
        'operators.html',
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

    operator = None
    admin = False

    operator = next((op for op in operators if op['uid'] == uid), None)

    if user and user["id"] in config.web_admins:
        admin = True

    operator_lines = []
    operator_lines = [
        line for line in lines
        if 'operator_uid' in line and line['operator_uid'] == uid
    ]

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
        'operator_lines.html',
        user=user,
        operator=operator,
        admin=admin,
        operator_lines=operator_lines
    )
