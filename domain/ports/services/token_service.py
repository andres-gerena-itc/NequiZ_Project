# domain/ports/services/token_service.py
# Puerto de salida: contrato para generación/verificación de tokens

from abc import ABC, abstractmethod
from typing import Optional, Dict


class TokenService(ABC):
    """
    Puerto de salida para el servicio de tokens JWT.
    El dominio solo conoce esta interfaz; nunca importa PyJWT directamente.
    """

    @abstractmethod
    def generar_access_token(self, numero_telefono: str, nombre: str) -> str:
        """Genera un token de acceso de corta duración."""

    @abstractmethod
    def generar_refresh_token(self, numero_telefono: str) -> str:
        """Genera un token de refresco de larga duración."""

    @abstractmethod
    def verificar_token(self, token: str) -> Optional[Dict]:
        """
        Verifica y decodifica el token.
        Retorna el payload si es válido, None si expiró o es inválido.
        """
