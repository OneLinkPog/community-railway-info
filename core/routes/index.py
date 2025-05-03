from flask import Blueprint, render_template, session
from core import main_dir
from core.config import config

import json

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
        operator = next((op for op in operators if user['id'] in op['users']), None)
        
    if user and user["id"] in config.web_admins:
        admin = True
    
    suspended_lines = []
    running_lines = []
    possible_delays_lines = []
    no_scheduled_service = []
    
    for line in lines:
        line_info = {
            'name': line['name'],
            'status': line['status'],
            'color': line.get('color'), 
            'notice': line.get('notice', ''),
            'stations': line.get('stations', [])
        }
        
        match line["status"]:
            case "Suspended":
                suspended_lines.append(line_info)
            case "Running":
                running_lines.append(line_info)
            case "Possible delays":
                possible_delays_lines.append(line_info)
            case "No scheduled service":
                no_scheduled_service.append(line_info)
            case _:
                print(f"{line['name']} has an invalid status")
    
    return render_template(
        'index.html',
        user=user,
        operator=operator,
        admin=admin,
        suspended_lines=suspended_lines,
        running_lines=running_lines,
        possible_delays_lines=possible_delays_lines,
        no_scheduled_service=no_scheduled_service,
        lines=lines,
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
    admin = False
    
    if user and 'id' in user:
        operator = next((op for op in operators if user['id'] in op['users']), None)
        
    if user and user["id"] in config.web_admins:
        admin = True
    
    return render_template(
        'computercraft-setup.html',
        user=user,
        operator=operator,
        admin=admin,
        lines=lines
    )