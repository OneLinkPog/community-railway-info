from core import main_dir

import logging
from logging.handlers import RotatingFileHandler
import os


class Logger:
    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        log_file = os.path.join(main_dir, "server.log")

        file_handler = RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=5)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - [%(levelname)s] - %(message)s', 
                                                  datefmt='%Y-%m-%d %H:%M:%S'))
        self.logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
                                                     datefmt='%Y-%m-%d %H:%M:%S'))
        self.logger.addHandler(console_handler)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)


logger = Logger("@main")