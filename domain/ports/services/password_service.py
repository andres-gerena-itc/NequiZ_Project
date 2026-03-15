# domain/ports/services/password_service.py
# Puerto de salida: contrato para hashing de contraseñas

from abc import ABC, abstractmethod


class PasswordService(ABC):
    """
    Puerto de salida para el servicio de contraseñas.
    El dominio nunca importa bcrypt directamente.
    """

    @abstractmethod
    def hashear(self, password: str) -> str:
        """Genera el hash seguro de una contraseña en texto plano."""

    @abstractmethod
    def verificar(self, password: str, password_hash: str) -> bool:
        """Compara una contraseña en texto plano con su hash almacenado."""
