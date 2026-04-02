# tests/fakes/fake_sesion_repository.py

from datetime import datetime
from typing import Dict, Optional

from domain.ports.repositories.sesion_repository import SesionRepository


class FakeSesionRepository(SesionRepository):
    """Implementación falsa del puerto SesionRepository."""

    def __init__(self):
        # clave: "numero_telefono:refresh_token"
        self._store: Dict[str, bool] = {}

    def guardar_sesion(
        self,
        numero_telefono: str,
        refresh_token: str,
        fecha_expiracion: datetime,
        dispositivo: str = '',
        ip: str = '',
    ) -> None:
        self._store[f"{numero_telefono}:{refresh_token}"] = True

    def eliminar_sesion(self, numero_telefono: str, refresh_token: str) -> bool:
        clave = f"{numero_telefono}:{refresh_token}"
        if clave in self._store:
            del self._store[clave]
            return True
        return False

    def existe_sesion(self, numero_telefono: str, refresh_token: str) -> bool:
        return f"{numero_telefono}:{refresh_token}" in self._store
