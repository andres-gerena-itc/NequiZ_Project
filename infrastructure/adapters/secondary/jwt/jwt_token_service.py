# infrastructure/adapters/secondary/jwt/jwt_token_service.py
# Adaptador secundario: implementa el puerto TokenService usando PyJWT

import jwt
import secrets
from datetime import datetime
from typing import Optional, Dict

from domain.ports.services.token_service import TokenService
from config import Config


class JwtTokenService(TokenService):
    """
    Implementación concreta del puerto TokenService.
    Solo este archivo conoce PyJWT.
    """

    def generar_access_token(self, numero_telefono: str, nombre: str) -> str:
        payload = {
            'numeroTelefono': numero_telefono,
            'nombre': nombre,
            'tipo': 'access',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + Config.JWT_ACCESS_TOKEN_EXPIRES,
            'jti': secrets.token_urlsafe(16),
        }
        return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm=Config.JWT_ALGORITHM)

    def generar_refresh_token(self, numero_telefono: str) -> str:
        payload = {
            'numeroTelefono': numero_telefono,
            'tipo': 'refresh',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + Config.JWT_REFRESH_TOKEN_EXPIRES,
            'jti': secrets.token_urlsafe(32),
        }
        return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm=Config.JWT_ALGORITHM)

    def verificar_token(self, token: str) -> Optional[Dict]:
        try:
            return jwt.decode(
                token,
                Config.JWT_SECRET_KEY,
                algorithms=[Config.JWT_ALGORITHM],
            )
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
