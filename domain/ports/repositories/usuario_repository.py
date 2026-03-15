# domain/ports/repositories/usuario_repository.py
# Puerto de salida: contrato que debe cumplir cualquier repositorio de usuarios

from abc import ABC, abstractmethod
from typing import Optional

from domain.entities.usuario import Usuario


class UsuarioRepository(ABC):
    """
    Puerto de salida para persistencia de usuarios.
    El dominio depende de esta abstracción; la infraestructura la implementa.
    """

    @abstractmethod
    def guardar(self, usuario: Usuario) -> None:
        """Persiste un usuario nuevo."""

    @abstractmethod
    def actualizar(self, usuario: Usuario) -> None:
        """Actualiza los datos de un usuario existente."""

    @abstractmethod
    def buscar_por_telefono(self, numero_telefono: str) -> Optional[Usuario]:
        """Retorna el usuario con ese número o None si no existe."""

    @abstractmethod
    def buscar_por_email(self, email: str) -> Optional[Usuario]:
        """Retorna el usuario con ese email o None si no existe."""

    @abstractmethod
    def existe_telefono(self, numero_telefono: str) -> bool:
        """Verifica si ya hay un usuario con ese número."""

    @abstractmethod
    def existe_email(self, email: str) -> bool:
        """Verifica si ya hay un usuario con ese email."""
