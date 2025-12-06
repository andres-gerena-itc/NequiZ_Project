# config.py - Configuración Central de NequiZ

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuración principal de la aplicación"""
    
    # MongoDB
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    DATABASE_NAME = 'nequiz_db'
    
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'nequiz-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)  # Token de acceso expira en 1 hora
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)  # Refresh token expira en 30 días
    JWT_ALGORITHM = 'HS256'
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'flask-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True') == 'True'
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Seguridad
    BCRYPT_LOG_ROUNDS = 12  # Nivel de encriptación bcrypt
    
    # Aplicación
    APP_NAME = 'NequiZ'
    APP_VERSION = '1.0.0'
    
    # Saldo inicial para nuevos usuarios
    SALDO_INICIAL = 100000.0  # $100,000 COP de bienvenida


class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True


class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    # En producción, asegurarse de usar variables de entorno reales


# Configuración a usar
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Obtiene la configuración según el entorno"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])