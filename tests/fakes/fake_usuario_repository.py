# tests/fakes/fake_usuario_repository.py
# Repositorio en memoria que implementa el puerto UsuarioRepository.
# No usa MongoDB. Solo un diccionario de Python.
# Sirve para probar casos de uso sin levantar infraestructura.

from typing import Dict, Optional

from domain.entities.usuario import Usuario
from domain.ports.repositories.usuario_repository import UsuarioRepository


class FakeUsuarioRepository(UsuarioRepository):
    """
    Implementación falsa del puerto UsuarioRepository.
    Almacena usuarios en un diccionario en RAM.
    Se reinicia sola en cada prueba al instanciarse de nuevo.
    """

    def __init__(self):
        self._store: Dict[str, Usuario] = {}

    def guardar(self, usuario: Usuario) -> None:
        self._store[usuario.numero_telefono] = usuario

    def actualizar(self, usuario: Usuario) -> None:
        self._store[usuario.numero_telefono] = usuario

    def buscar_por_telefono(self, numero_telefono: str) -> Optional[Usuario]:
        return self._store.get(numero_telefono)

    def buscar_por_email(self, email: str) -> Optional[Usuario]:
        return next(
            (u for u in self._store.values() if u.email == email),
            None,
        )

    def existe_telefono(self, numero_telefono: str) -> bool:
        return numero_telefono in self._store

    def existe_email(self, email: str) -> bool:
        return any(u.email == email for u in self._store.values())
