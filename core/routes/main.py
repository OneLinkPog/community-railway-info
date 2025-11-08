from flask import Blueprint, render_template, session
from core.config import config
from core.controller import LineController, OperatorController, StationController
from core.logger import Logger

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
