from flask import Blueprint, render_template, session
from core import main_dir
from core.config import config

import json
import re

index = Blueprint('index', __name__)

@index.route('/')
def index_route():
    user = session.get('user')
    
    with open(main_dir + '/lines.json') as f:
        lines = json.load(f)
    
    with open(main_dir + '/operators.json') as f:
        operators = json.load(f)
    
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
                ''.join([i for i in x['name'] if not i.isdigit()]),  # alphabetical part
                [int(''.join(g)) for g in re.findall(r'\d+', x['name'])] or [0]  # numerical part
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

@index.route('/computercraft-setup')
def computercraft_setup_route():
    user = session.get('user')
    
    with open(main_dir + '/lines.json') as f:
        lines = json.load(f)
    
    with open(main_dir + '/operators.json') as f:
        operators = json.load(f)
    
    operator = None
    if user and 'id' in user:
        operator = [op for op in operators if user['id'] in op['users']]
    
    return render_template(
        'computercraft-setup.html',
        user=user,
        operator=operator,
        lines=lines
    )