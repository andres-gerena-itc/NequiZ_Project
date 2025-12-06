# utils/jwt_handler.py - Manejo de JSON Web Tokens

import jwt
from datetime import datetime, timedelta
from config import Config
from functools import wraps
from flask import request, jsonify
import secrets
import logging

logger = logging.getLogger(__name__)


def generar_access_token(numero_telefono, nombre):
    """
    Generar Access Token JWT (corta duración)
    
    Args:
        numero_telefono (str): Número de teléfono del usuario
        nombre (str): Nombre del usuario
        
    Returns:
        str: JWT token
    """
    try:
        payload = {
            'numeroTelefono': numero_telefono,
            'nombre': nombre,
            'tipo': 'access',
            'iat': datetime.utcnow(),  # Issued at
            'exp': datetime.utcnow() + Config.JWT_ACCESS_TOKEN_EXPIRES,  # Expiration
            'jti': secrets.token_urlsafe(16)  # JWT ID único
        }
        
        token = jwt.encode(
            payload,
            Config.JWT_SECRET_KEY,
            algorithm=Config.JWT_ALGORITHM
        )
        
        return token
        
    except Exception as e:
        logger.error(f"Error generando access token: {e}")
        return None


def generar_refresh_token(numero_telefono):
    """
    Generar Refresh Token JWT (larga duración)
    
    Args:
        numero_telefono (str): Número de teléfono del usuario
        
    Returns:
        str: JWT refresh token
    """
    try:
        payload = {
            'numeroTelefono': numero_telefono,
            'tipo': 'refresh',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + Config.JWT_REFRESH_TOKEN_EXPIRES,
            'jti': secrets.token_urlsafe(32)  # ID único más largo para refresh
        }
        
        token = jwt.encode(
            payload,
            Config.JWT_SECRET_KEY,
            algorithm=Config.JWT_ALGORITHM
        )
        
        return token
        
    except Exception as e:
        logger.error(f"Error generando refresh token: {e}")
        return None


def verificar_token(token):
    """
    Verificar y decodificar JWT token
    
    Args:
        token (str): JWT token a verificar
        
    Returns:
        dict: Payload del token si es válido, None si es inválido
    """
    try:
        payload = jwt.decode(
            token,
            Config.JWT_SECRET_KEY,
            algorithms=[Config.JWT_ALGORITHM]
        )
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token expirado")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token inválido: {e}")
        return None
    except Exception as e:
        logger.error(f"Error verificando token: {e}")
        return None


def extraer_token_de_header():
    """
    Extraer token JWT del header Authorization
    
    Returns:
        str: Token JWT o None si no existe
    """
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header:
        return None
    
    # Formato esperado: "Bearer <token>"
    parts = auth_header.split()
    
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    return parts[1]


def require_jwt(f):
    """
    Decorador para proteger rutas con JWT
    
    Uso:
        @app.route('/api/perfil')
        @require_jwt
        def perfil():
            # request.user_data contendrá los datos del token
            return jsonify(request.user_data)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = extraer_token_de_header()
        
        if not token:
            return jsonify({
                'error': 'Token no proporcionado',
                'codigo': 'TOKEN_MISSING'
            }), 401
        
        payload = verificar_token(token)
        
        if not payload:
            return jsonify({
                'error': 'Token inválido o expirado',
                'codigo': 'TOKEN_INVALID'
            }), 401
        
        # Verificar que sea un access token
        if payload.get('tipo') != 'access':
            return jsonify({
                'error': 'Tipo de token incorrecto',
                'codigo': 'TOKEN_TYPE_INVALID'
            }), 401
        
        # Agregar datos del usuario al request
        request.user_data = {
            'numeroTelefono': payload.get('numeroTelefono'),
            'nombre': payload.get('nombre'),
            'jti': payload.get('jti')
        }
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_refresh_token(f):
    """
    Decorador para rutas que requieren refresh token
    
    Uso:
        @app.route('/api/refresh')
        @require_refresh_token
        def refresh():
            return generar_nuevo_access_token()
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = extraer_token_de_header()
        
        if not token:
            return jsonify({
                'error': 'Refresh token no proporcionado',
                'codigo': 'REFRESH_TOKEN_MISSING'
            }), 401
        
        payload = verificar_token(token)
        
        if not payload:
            return jsonify({
                'error': 'Refresh token inválido o expirado',
                'codigo': 'REFRESH_TOKEN_INVALID'
            }), 401
        
        # Verificar que sea un refresh token
        if payload.get('tipo') != 'refresh':
            return jsonify({
                'error': 'Tipo de token incorrecto',
                'codigo': 'TOKEN_TYPE_INVALID'
            }), 401
        
        # Agregar datos del usuario al request
        request.user_data = {
            'numeroTelefono': payload.get('numeroTelefono'),
            'jti': payload.get('jti')
        }
        
        return f(*args, **kwargs)
    
    return decorated_function


def obtener_usuario_desde_token():
    """
    Obtener número de teléfono del usuario desde el token en el request actual
    
    Returns:
        str: Número de teléfono o None
    """
    if hasattr(request, 'user_data'):
        return request.user_data.get('numeroTelefono')
    return None


def token_info(token):
    """
    Obtener información de un token sin verificar firma (solo decodificar)
    Útil para debugging
    
    Args:
        token (str): JWT token
        
    Returns:
        dict: Payload del token
    """
    try:
        # Decodificar sin verificar (útil para debugging)
        payload = jwt.decode(
            token,
            options={"verify_signature": False}
        )
        return payload
    except Exception as e:
        logger.error(f"Error decodificando token: {e}")
        return None


def tiempo_expiracion(token):
    """
    Obtener tiempo restante hasta que expire un token
    
    Args:
        token (str): JWT token
        
    Returns:
        timedelta: Tiempo restante o None si el token es inválido
    """
    payload = verificar_token(token)
    
    if not payload or 'exp' not in payload:
        return None
    
    exp_timestamp = payload['exp']
    exp_datetime = datetime.fromtimestamp(exp_timestamp)
    ahora = datetime.utcnow()
    
    if exp_datetime < ahora:
        return timedelta(0)  # Ya expiró
    
    return exp_datetime - ahora


# Exportar funciones principales
__all__ = [
    'generar_access_token',
    'generar_refresh_token',
    'verificar_token',
    'extraer_token_de_header',
    'require_jwt',
    'require_refresh_token',
    'obtener_usuario_desde_token',
    'token_info',
    'tiempo_expiracion'
]