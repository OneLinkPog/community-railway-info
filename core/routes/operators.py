from flask import render_template, session, redirect, url_for
from core import main_dir
from core.config import config
from core.data import Line, Operator

import json


def operators():
    user = session.get('user')

    lines = Line.get_legacy()
    operators = Operator.get_legacy()

    operator = None
    if user and 'id' in user:
        operator = next((op for op in operators if user['id'] in op['users']), None)
    
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
