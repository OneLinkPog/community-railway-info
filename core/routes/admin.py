from flask import render_template, session, redirect, url_for
from core import main_dir
from core.config import config
from core.data import Line, Operator

import json


def admin():
    user = session.get('user')

    if not user or user.get('id') not in config.web_admins:
        return redirect(url_for('index'))
    
    lines = Line.get_legacy()
    operators = Operator.get_legacy()

    operator = None
    if user and 'id' in user:
        operator = next((op for op in operators if user['id'] in op['users']), None)

    return render_template(
        'admin.html',
        user=user,
        operator=operator,
        admin=True,
        lines=lines
    )
