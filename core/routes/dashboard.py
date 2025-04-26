from flask import Blueprint, session, redirect, url_for, render_template, request
from requests_oauthlib import OAuth2Session
from core.config import config
from core.url import *
from core import main_dir
from core.data import *

import json


dashboard = Blueprint('dashboard', __name__)


@dashboard.route('/dashboard')
async def dashboard_view():
    user = session.get('user')

    if not user:
        return redirect(url_for('auth.login'))

    lines = Line.get_legacy()
    operators = Operator.get_legacy()

    operator = None
    admin = False

    if user and 'id' in user:
        operator = next((op for op in operators if user['id'] in op['users']), None)

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
                print(f'Missing field: {field}')
                return {'error': f'Missing field: {field}'}, 400
            
        with Session(engine) as db:
            if Line.exists(db, data["name"]):
                return {'error': 'A line with that name already exists'}, 400
            
            new_line = Line(
                name=data["name"],
                status=LineStatus.from_legacy(data["status"]),
                color=int(data["color"][1:], 16),
                operator_id=data["operator_uid"],
                stations=lmap(lambda id: db.exec(select(Station).where(Station.id == id)).one(), data["stations"])
            )
            db.add(new_line)
            db.commit()

            return {'success': True}, 200
    except Exception as e:
        raise (e)
        return {'error': str(e)}, 500


@dashboard.route('/api/lines/<name>', methods=['PUT'])
async def update_line(name):
    if not session.get('user'):
        return {'error': 'Not authorized'}, 401

    try:
        data = request.json
        print(f"Updating line {name} with data:", data) 

        with Session(engine) as session:
            line = session.exec(select(Line).where(Line.name == name)).one_or_none()

            if line == None:
                return {'error': f'Line {name} not found'}, 404
            
            if line.name != data["name"] and Line.exists(session, data["name"]) != None:
                return {'error': 'A line with that name already exists'}, 400
            
            line.name = data["name"]
            line.color = int(data["color"][1:], 16)
            line.status = LineStatus.from_legacy(data["status"])
            line.notice = data["notice"] or None
            line.stations = lmap(lambda id: session.exec(select(Station).where(Station.id == id)).one(), data["stations"])
            
            session.add(line)
            session.commit()
                
            return {'success': True}, 200
    except Exception as e:
        print(f"Error while updating line {name}:", str(e))  
        return {'error': str(e)}, 500


@dashboard.route('/api/lines/<name>', methods=['DELETE'])
async def delete_line(name):
    if not session.get('user'):
        return {'error': 'Not authorized'}, 401

    try:
        with Session(engine) as session:
            line = session.exec(select(Line).where(Line.name == name))
            session.delete(line)
            session.commit()

            return {'success': True}, 200
    except Exception as e:
        return {'error': str(e)}, 500
