from core import main_dir
import yaml

with open(main_dir + "/config.yml", "r") as _config:
    config_data = yaml.load(_config, Loader=yaml.SafeLoader)


class Config:
    def __init__(self):
        self.discord_client_id = config_data["discord_client_id"]
        self.discord_client_secret = config_data["discord_client_secret"]
        self.discord_redirect_uri = config_data["discord_redirect_uri"]
        
        self.host = config_data["host"]
        self.port = config_data["port"]
        self.debug = config_data["debug"]
        
        self.web_admins = config_data["web_admins"]
        
        self.maintenance_mode = config_data["maintenance_mode"]
        self.maintenance_message = config_data["maintenance_message"]

config = Config()

allowed_tags = [
    'p', 'br', 'strong', 'em', 'a', 'ul', 'li', 'h1',
    'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div', 'b', 'i',
    'u', 's', 'mark', 'pre', 'blockquote', 'strong'
]
