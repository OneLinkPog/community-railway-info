from flask import Blueprint, session, redirect, url_for, render_template, request
from requests_oauthlib import OAuth2Session
from core.config import config, allowed_tags
from core.url import *
from core import main_dir
from core.data import *
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

    lines = Line.get_legacy()
    operators = Operator.get_legacy()

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
                        "username": user.username,
                        "display_name": user.display_name,
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
            
        with Session(engine) as db:
            if Line.exists(db, data["name"]):
                logger.error(f'[@{session.get("user")["username"]}] A line with that name already exists')
                return {'error': 'A line with that name already exists'}, 400
            
            logger.info(f'[@{session.get("user")["username"]}] Added new line: {data["name"]}')
            new_line = Line(
                name=data["name"],
                status=LineStatus.from_legacy(data["status"]),
                color=int(data["color"][1:], 16),
                operator_id=data["operator_uid"]
            )

            order = 0
            for id in data["stations"]:
                station = db.exec(select(Station).where(Station.id == id)).one_or_none()

                if station == None:
                    logger.error(f'[@{session.get("user")["username"]}] The station "{id}" does not exist')
                    return {'error': f'The station "{id}" does not exist'}, 400
                
                link = LineStationLink(line=new_line, station=station, order=order)
                new_line.stations.append(link)
                order += 1

            db.add(new_line)
            db.add_all(new_line.stations)
            db.commit()

            return {'success': True}, 200
    except Exception as e:
        logger.error(f'[@{session.get("user")["username"]}] Error while adding line: {str(e)}')
        return {'error': str(e)}, 500


@dashboard.route('/api/lines/<name>', methods=['PUT'])
async def update_line(name):
    if not session.get('user'):
        return {'error': 'Not authorized'}, 401

    try:
        data = request.json
        logger.info(f'[@{session.get("user")["username"]}] Updating line {name} with data: {data}')

        with Session(engine) as db:
            line = db.exec(select(Line).where(Line.name == name)).one_or_none()

            if line == None:
                logger.info(f"[@{session.get('user')['username']}] Line {name} not found")
                return {'error': f'Line {name} not found'}, 404
            
            if line.name != data["name"] and Line.exists(db, data["name"]) != None:
                logger.error(f'[@{session.get("user")["username"]}] A line with that name already exists')
                return {'error': 'A line with that name already exists'}, 400
            
            line.name = data["name"]
            line.color = int(data["color"][1:], 16)
            line.status = LineStatus.from_legacy(data["status"])
            line.notice = data["notice"] or None
            
            for link in line.stations:
                db.delete(link)
            line.stations = []

            order = 0
            for id in data["stations"]:
                station = db.exec(select(Station).where(Station.id == id)).one_or_none()

                if station == None:
                    logger.error(f'[@{session.get("user")["username"]}] The station "{id}" does not exist')
                    return {'error': f'The station "{id}" does not exist'}, 400
                
                link = LineStationLink(line=line, station=station, order=order)
                line.stations.append(link)
                order += 1

            logger.info(f'[@{session.get("user")["username"]}] Line {name} updated successfully with new data: {line}') # TODO: `line` probably needs serialization to be logged
            
            db.add(line)
            db.add_all(line.stations)
            db.commit()
                
            return {'success': True}, 200
    except Exception as e:
        logger.error(f"[@{session.get('user')['username']}] Error while updating line {name}: {str(e)}")
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

            logger.info(f"[@{session.get('user')['username']}] Deleted line {name} successfully.")
            return {'success': True}, 200
    except Exception as e:
        logger.error(f'[@{session.get("user")["username"]}] Error while deleting line {name}: {str(e)}')
        return {'error': str(e)}, 500
