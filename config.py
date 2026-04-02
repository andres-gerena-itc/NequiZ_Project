# config.py

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    DATABASE_NAME = 'nequiz_db'

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'nequiz-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_ALGORITHM = 'HS256'

    SECRET_KEY = os.getenv('SECRET_KEY', 'flask-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True') == 'True'

    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

    BCRYPT_LOG_ROUNDS = 12
    SALDO_INICIAL = 100_000.0

    APP_NAME = 'NequiZ'
    APP_VERSION = '1.0.0'


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


_configs = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}


def get_config():
    env = os.getenv('FLASK_ENV', 'development')
    return _configs.get(env, _configs['default'])
