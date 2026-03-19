# infrastructure/adapters/primary/rest/middlewares.py
# Middlewares/decoradores Flask para proteger rutas con JWT

from functools import wraps
from flask import request, jsonify
from domain.ports.services.token_service import TokenService
import logging

logger = logging.getLogger(__name__)

# El token_service se inyecta al inicializar la app (ver container.py)
_token_service: TokenService = None


def init_middlewares(token_service: TokenService) -> None:
    """Inyecta el servicio de tokens en los middlewares."""
    global _token_service
    _token_service = token_service


def _extraer_token() -> str | None:
    auth = request.headers.get('Authorization', '')
    partes = auth.split()
    if len(partes) == 2 and partes[0].lower() == 'bearer':
        return partes[1]
    return None


def require_access_token(f):
    """Decorador: exige un access token válido en Authorization."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = _extraer_token()
        if not token:
            return jsonify({'error': 'Token no proporcionado', 'codigo': 'TOKEN_MISSING'}), 401

        payload = _token_service.verificar_token(token)
        if not payload:
            return jsonify({'error': 'Token inválido o expirado', 'codigo': 'TOKEN_INVALID'}), 401

        if payload.get('tipo') != 'access':
            return jsonify({'error': 'Tipo de token incorrecto', 'codigo': 'TOKEN_TYPE_INVALID'}), 401

        request.user_data = {
            'numeroTelefono': payload.get('numeroTelefono'),
            'nombre': payload.get('nombre'),
        }
        return f(*args, **kwargs)
    return wrapper


def require_refresh_token_middleware(f):
    """Decorador: exige un refresh token válido en Authorization."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = _extraer_token()
        if not token:
            return jsonify({'error': 'Refresh token no proporcionado'}), 401

        payload = _token_service.verificar_token(token)
        if not payload:
            return jsonify({'error': 'Refresh token inválido o expirado'}), 401

        if payload.get('tipo') != 'refresh':
            return jsonify({'error': 'Tipo de token incorrecto'}), 401

        request.user_data = {'numeroTelefono': payload.get('numeroTelefono')}
        return f(*args, **kwargs)
    return wrapper


def obtener_numero_desde_request() -> str | None:
    """Helper para rutas protegidas: extrae el número del user_data."""
    if hasattr(request, 'user_data'):
        return request.user_data.get('numeroTelefono')
    return None
