from .base import Config


class LocalConfig(Config):
    TESTING = True
    DEBUG = True
