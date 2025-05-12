from core import main_dir

def load_secret():
    with open(main_dir + "/secret.key", "r") as _secret:
        return _secret.read()