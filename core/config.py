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

        self.discord_client_id = config_data["discord_client_id"]
        self.discord_client_secret = config_data["discord_client_secret"]
        self.discord_redirect_uri = config_data["discord_redirect_uri"]

        self.host = config_data["host"]
        self.port = config_data["port"]
        self.debug = config_data["debug"]

        self.web_admins = config_data["web_admins"]

        self.maintenance_mode = config_data["maintenance_mode"]
        self.maintenance_message = config_data["maintenance_message"]
        self.readonly = config_data["readonly"]


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
