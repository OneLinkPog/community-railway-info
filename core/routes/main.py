from flask import Blueprint, render_template, session, redirect, url_for
from core.config import config
from core.controller import LineController, OperatorController, StationController, OperatorRequestController
from core.logger import Logger
from core.utils import fetch_discord_user

import re

main = Blueprint('index', __name__)
logger = Logger("@main")


@main.route('/')
def index_route():
    user = session.get('user')

    lines = LineController.get_all_lines()
    operators = OperatorController.get_all_operators()

    operator = None
    admin = False

    if user and 'id' in user:
        operator = [op for op in operators if user['id'] in op['users']]

    if user and user["id"] in config.web_admins:
        admin = True

    line_types = {
        'public': {'suspended': [], 'partially_suspended': [], 'running': [], 'possible_delays': [], 'no_scheduled': []},
        'private': {'suspended': [], 'partially_suspended': [], 'running': [], 'possible_delays': [], 'no_scheduled': []},
        'metro': {'suspended': [], 'partially_suspended': [], 'running': [], 'possible_delays': [], 'no_scheduled': []},
        'tram': {'suspended': [], 'partially_suspended': [], 'running': [], 'possible_delays': [], 'no_scheduled': []},
        "bus": {'suspended': [], 'partially_suspended': [], 'running': [], 'possible_delays': [], 'no_scheduled': []},
    }

    for line in lines:
        if 'notice' in line:
            if line['notice'] is None or line['notice'].strip() == '':
                line['notice'] = None
            else:
                line['notice'] = line['notice'].strip()
        else:
            line['notice'] = None

        line_type = line.get('type', 'public')
        status_key = {
            'Suspended': 'suspended',
            'Partially suspended': 'partially_suspended',
            'Running': 'running',
            'Possible delays': 'possible_delays',
            'No scheduled service': 'no_scheduled'
        }.get(line['status'])

        if status_key and line_type in line_types:
            line_types[line_type][status_key].append(line)

    # Sort each status list in each line type
    for line_type in line_types.values():
        for status in line_type.values():
            status.sort(key=lambda x: (
                # alphabetical part
                ''.join([i for i in x['name'] if not i.isdigit()]),
                [int(''.join(g)) for g in re.findall(
                    r'\d+', x['name'])] or [0]  # numerical part
            ))

    return render_template(
        'index.html',
        user=user,
        operator=operator,
        admin=admin,
        line_types=line_types,
        maintenance_mode=config.maintenance_mode,
        maintenance_message=config.maintenance_message
    )


@main.route('/computercraft-setup')
def computercraft_setup_route():
    user = session.get('user')

    operators = OperatorController.get_all_operators()

    operator = None
    admin = False

    if user and 'id' in user:
        operator = [op for op in operators if user['id'] in op['users']]

    if user and user["id"] in config.web_admins:
        admin = True

    return render_template(
        'computercraft-setup.html',
        user=user,
        admin=admin,
        operator=operator,
    )


@main.route('/stations')
def stations_route():
    user = session.get('user')

    operators = OperatorController.get_all_operators()
    stations = StationController.get_all_stations()
    total_stations = len(stations)
    active_stations = len([s for s in stations if s['status'] == 'open'])
    connecting_lines = LineController.get_all_line_stations_count()

    operator = None
    admin = False

    if user and 'id' in user:
        operator = [op for op in operators if user['id'] in op['users']]

    if user and user["id"] in config.web_admins:
        admin = True

    return render_template(
        'stations.html',
        user=user,
        admin=admin,
        operator=operator,
        stations=stations,
        total_stations=total_stations,
        active_stations=active_stations,
        connecting_lines=connecting_lines
    )


@main.route('/api-docs')
def api_docs_route():
    user = session.get('user')

    operators = OperatorController.get_all_operators()

    operator = None
    admin = False

    if user and 'id' in user:
        operator = [op for op in operators if user['id'] in op['users']]

    if user and user['id'] in config.web_admins:
        admin = True

    return render_template(
        'api-docs.html',
        user=user,
        admin=admin,
        operator=operator,
    )


@main.route('/me')
def my_profile_route():
    user = session.get('user')

    if not user or 'id' not in user:
        return redirect(url_for('auth.login'))

    return redirect(url_for('index.user_profile_route', user_id=user['id']))


@main.route('/users/<string:user_id>')
def user_profile_route(user_id):
    current_user = session.get('user')

    all_operators = OperatorController.get_all_operators() or []
    all_lines = LineController.get_all_lines() or []
    all_requests = OperatorRequestController.get_all_requests() or []

    nav_operator = None
    admin = False

    if current_user and 'id' in current_user:
        nav_operator = [op for op in all_operators if current_user['id'] in op.get('users', [])]

    if current_user and current_user['id'] in config.web_admins:
        admin = True

    member_operators = [op for op in all_operators if str(user_id) in op.get('users', [])]
    member_operator_uids = {op.get('uid') for op in member_operators}
    member_lines = [line for line in all_lines if line.get('operator_uid') in member_operator_uids]

    user_requests = [
        req for req in all_requests
        if str(req.get('requester', {}).get('id')) == str(user_id)
    ]

    request_stats = {
        'total': len(user_requests),
        'pending': len([r for r in user_requests if r.get('status') == 'pending']),
        'accepted': len([r for r in user_requests if r.get('status') == 'accepted']),
        'rejected': len([r for r in user_requests if r.get('status') == 'rejected'])
    }

    discord_user = fetch_discord_user(user_id, config.discord_bot_token) or {
        'id': user_id,
        'username': user_id,
        'display_name': user_id,
        'avatar_url': 'https://cdn.discordapp.com/embed/avatars/0.png',
        'bot': False,
        'system': False,
    }

    is_self = bool(current_user and str(current_user.get('id')) == str(user_id))

    return render_template(
        'users.html',
        user=current_user,
        admin=admin,
        operator=nav_operator,
        profile_user=discord_user,
        is_self=is_self,
        member_operators=member_operators,
        member_lines=member_lines,
        request_stats=request_stats,
        user_requests=user_requests[:10],
    )
