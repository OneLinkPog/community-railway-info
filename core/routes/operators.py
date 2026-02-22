from flask import Blueprint, render_template, session, redirect, url_for
from core import main_dir
from core.config import config, allowed_tags, allowed_attributes
from core.logger import Logger
from core.controller import LineController, OperatorController
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


# GET /operators
@operators.route('/operators')
def operators_route():
    user = session.get('user')

    lines = LineController.get_all_lines()
    operators = OperatorController.get_all_operators()

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


# GET /operators/<string:uid>
@operators.route('/operators/<string:uid>')
def operator_route(uid):
    user = session.get('user')

    lines = LineController.get_all_lines()
    operators = OperatorController.get_all_operators()

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
                    # Use Discord API directly
                    if not config.discord_bot_token or config.discord_bot_token == "YOUR_BOT_TOKEN_HERE":
                        raise Exception("Discord bot token not configured")
                    
                    headers = {
                        'Authorization': f'Bot {config.discord_bot_token}',
                        'Content-Type': 'application/json'
                    }
                    
                    response = requests.get(
                        f"https://discord.com/api/v10/users/{user_id}",
                        headers=headers,
                        timeout=4
                    )
                    
                    if response.status_code == 200:
                        discord_data = response.json()
                        
                        avatar_url = default_avatar
                        if discord_data.get('avatar'):
                            avatar_hash = discord_data['avatar']
                            extension = 'gif' if avatar_hash.startswith('a_') else 'png'
                            avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.{extension}?size=32"
                        else:
                            if discord_data.get('discriminator') and discord_data['discriminator'] != '0':
                                default_avatar_index = int(discord_data['discriminator']) % 5
                            else:
                                default_avatar_index = (int(user_id) >> 22) % 6
                            avatar_url = f"https://cdn.discordapp.com/embed/avatars/{default_avatar_index}.png"
                        
                        user_data = {
                            "avatar_url": avatar_url,
                            "username": discord_data.get("username", user_id),
                            "display_name": discord_data.get("global_name") or discord_data.get("username", user_id)
                        }
                    else:
                        raise Exception(f"Discord API returned {response.status_code}")
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch Discord user {user_id}: {str(e)}")
                    user_data = {
                        "avatar_url": default_avatar,
                        "username": user_id,
                        "display_name": user_id
                    }
                set_cached_user_data(user_id, user_data)
                
            operator['user_datas'].append({
                'id': user_id,
                'avatar_url': user_data.get("avatar_url", default_avatar),
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

# GET /operators/request
@operators.route('/request')
def request_operator_page():
    user = session.get('user')
    admin = False

    if not user:
        return redirect(url_for('auth.login'))

    operators = OperatorController.get_all_operators()
    
    if user and 'id' in user:
        operator = [op for op in operators if user['id'] in op['users']]
        
    if user and user["id"] in config.web_admins:
        admin = True

    return render_template(
        'operators/request.html',
        user=user,
        operator=operator,
        admin=admin,
    )
