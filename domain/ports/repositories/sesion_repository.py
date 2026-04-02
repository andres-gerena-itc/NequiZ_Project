# domain/ports/repositories/sesion_repository.py
# Puerto de salida: contrato para el repositorio de sesiones

from abc import ABC, abstractmethod
from datetime import datetime


class SesionRepository(ABC):
    """
    Puerto de salida para gestión de sesiones (refresh tokens).
    """

    @abstractmethod
    def guardar_sesion(
        self,
        numero_telefono: str,
        refresh_token: str,
        fecha_expiracion: datetime,
        dispositivo: str = '',
        ip: str = '',
    ) -> None:
        """Persiste una nueva sesión activa."""

    @abstractmethod
    def eliminar_sesion(self, numero_telefono: str, refresh_token: str) -> bool:
        """Elimina la sesión (logout). Retorna True si existía."""

    @abstractmethod
    def existe_sesion(self, numero_telefono: str, refresh_token: str) -> bool:
        """Verifica si la sesión todavía es válida."""
