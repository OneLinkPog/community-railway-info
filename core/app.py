from flask import Flask
from core.utils import load_secret
from core.config import config
from core.sql import sql

from core.routes.oauth2 import auth
from core.routes.api import api
from core.routes.main import main
from core.routes.admin import admin
from core.routes.operators import operators

import os
import json

def run_migrations():
    sql.execute_query("ALTER TABLE operator ADD COLUMN IF NOT EXISTS description TEXT NULL")
    sql.execute_query("ALTER TABLE operator ADD COLUMN IF NOT EXISTS image_path VARCHAR(255) NULL")

run_migrations()

app = Flask(
    __name__,
    static_url_path="/static",
    static_folder="../static",
    template_folder="../layouts"
)

app.config["SECRET_KEY"] = load_secret()
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


app.register_blueprint(auth)
app.register_blueprint(api)
app.register_blueprint(main)
app.register_blueprint(operators)
app.register_blueprint(admin)


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
