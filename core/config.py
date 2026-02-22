from core import main_dir
import yaml

with open(main_dir + "/config.yml", "r") as _config:
    config_data = yaml.load(_config, Loader=yaml.SafeLoader)


class Config:
    def __init__(self):
        self.load()

    def load(self):
        with open(main_dir + "/config.yml", "r") as _config:
            config_data = yaml.load(_config, Loader=yaml.SafeLoader)

        # Discord configuration
        discord_config = config_data.get("discord", {})
        self.discord_client_id = discord_config.get("discord_client_id")
        self.discord_client_secret = discord_config.get("discord_client_secret")
        self.discord_redirect_uri = discord_config.get("discord_redirect_uri")
        self.discord_bot_token = discord_config.get("discord_bot_token")

        # Webserver configuration
        webserver_config = config_data.get("webserver", {})
        self.host = webserver_config.get("host", "0.0.0.0")
        self.port = webserver_config.get("port", 30789)
        self.debug = webserver_config.get("debug", False)

        # Administration configuration
        admin_config = config_data.get("administration", {})
        self.web_admins = admin_config.get("web_admins", [])
        self.maintenance_mode = admin_config.get("maintenance_mode", False)
        self.maintenance_message = admin_config.get("maintenance_message", "")
        self.readonly = admin_config.get("readonly", False)

        # Database configuration
        db_config = config_data.get("database", {})
        self.db_host = db_config.get("host", "localhost")
        self.db_port = db_config.get("port", 3306)
        self.db_user = db_config.get("user")
        self.db_password = db_config.get("password")
        self.db_database = db_config.get("database")


config = Config()

allowed_tags = [
    'p', 'br', 'strong', 'em', 'a', 'ul', 'li', 'h1',
    'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div', 'b', 'i',
    'u', 's', 'mark', 'pre', 'blockquote', 'strong', "hr",
    "style", "center", "svg", "path", "g", "rect", "circle",
    "ellipse", "line", "polyline", "polygon", "title", "desc", "defs", "use"
]


allowed_attributes = {
    "div": ["class", "style", "id"],
    "svg": [
        "width", "height", "viewBox", "fill", "xmlns", "class", "style", "id", "x", "y", "version",
        "aria-hidden", "focusable", "role", "preserveAspectRatio"
    ],
    "path": [
        "d", "fill", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin", "stroke-miterlimit",
        "stroke-dasharray", "stroke-dashoffset", "opacity", "class", "style", "id", "fill-rule", "clip-rule"
    ],
    "g": ["class", "style", "id", "fill", "stroke", "stroke-width", "opacity"],
    "rect": [
        "x", "y", "width", "height", "rx", "ry", "fill", "stroke", "stroke-width", "opacity", "class", "style", "id"
    ],
    "circle": [
        "cx", "cy", "r", "fill", "stroke", "stroke-width", "opacity", "class", "style", "id"
    ],
    "ellipse": [
        "cx", "cy", "rx", "ry", "fill", "stroke", "stroke-width", "opacity", "class", "style", "id"
    ],
    "line": [
        "x1", "y1", "x2", "y2", "stroke", "stroke-width", "opacity", "class", "style", "id"
    ],
    "polyline": [
        "points", "fill", "stroke", "stroke-width", "opacity", "class", "style", "id"
    ],
    "polygon": [
        "points", "fill", "stroke", "stroke-width", "opacity", "class", "style", "id"
    ],
    "title": ["class", "style", "id"],
    "desc": ["class", "style", "id"],
    "defs": ["class", "style", "id"],
    "use": ["href", "xlink:href", "class", "style", "id"]
}
