from flask import Blueprint, render_template, session, redirect, url_for
from core import main_dir
from core.config import config, allowed_tags
from core.data import *

import json
import requests
from bleach import clean

operators = Blueprint('operators', __name__)


@operators.route('/operators')
def operators_route():
    user = session.get('user')

    lines = Line.get_legacy()
    operators = Operator.get_legacy()

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

    lines = Line.get_legacy()
    operators = Operator.get_legacy()

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
            with Session(engine) as db:
                user = db.exec(select(User).where(User.id == user_id)).one_or_none()

                if user == None:
                    operator['user_datas'].append({
                        "id": user_id,
                        "avatar_url": User.get_default_avatar_url(),
                    })
                else:
                    operator['user_datas'].append({
                        "id": user_id,
                        "username": user.username or f"id:{user_id}",
                        "display_name": user.display_name or "Unknown",
                        "avatar_url": user.get_avatar_url(),
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
