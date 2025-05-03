from flask import Flask
from core.utils import load_secret
from core.config import config

from core.routes.oauth2 import auth
from core.routes.dashboard import dashboard
from core.routes.index import index
from core.routes.admin import admin
from core.routes.operators import operators

import os
import json

app = Flask(
    __name__,
    static_url_path="/static",
    static_folder="../static",
    template_folder="../layouts"
)

app.config["SECRET_KEY"] = load_secret()
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


app.register_blueprint(auth)
app.register_blueprint(dashboard)
app.register_blueprint(index)
app.register_blueprint(operators)
app.register_blueprint(admin)


@app.route('/lines.json')
def lines_json():
    with open(os.path.join(os.path.dirname(__file__), '../lines.json')) as f:
        lines = json.load(f)
    return lines


@app.route('/operators.json')
def operators_json():
    with open(os.path.join(os.path.dirname(__file__), '../operators.json')) as f:
        operators = json.load(f)
    return operators


@app.route('/setup.lua')
def setup_lua():
    with open(os.path.join(os.path.dirname(__file__), '../static/assets/lua/setup.lua')) as f:
        lua = f.read()
    return lua, 200, {'Content-Type': 'text/plain', 'Content-Disposition': 'attachment; filename=setup.lua'}


class App:
    def __init__(self, flask_app: Flask):
        self.app = flask_app

    def run(self):
        self.app.run(
            host=config.host,
            port=config.port,
            debug=config.debug,
            threaded=True
        )
