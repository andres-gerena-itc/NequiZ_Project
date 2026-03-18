# infrastructure/adapters/secondary/mongodb/sesion_repository.py

from datetime import datetime
from domain.ports.repositories.sesion_repository import SesionRepository
from infrastructure.adapters.secondary.mongodb.connection import sesiones_col


class MongoSesionRepository(SesionRepository):
    def guardar_sesion(
        self,
        numero_telefono: str,
        refresh_token: str,
        fecha_expiracion: datetime,
        dispositivo: str = '',
        ip: str = '',
    ) -> None:
        sesiones_col.insert_one({
            'numeroTelefono': numero_telefono,
            'refreshToken': refresh_token,
            'fechaCreacion': datetime.utcnow(),
            'fechaExpiracion': fecha_expiracion,
            'dispositivo': dispositivo[:200],
            'ip': ip,
        })

    def eliminar_sesion(self, numero_telefono: str, refresh_token: str) -> bool:
        result = sesiones_col.delete_one({
            'numeroTelefono': numero_telefono,
            'refreshToken': refresh_token,
        })
        return result.deleted_count > 0

    def existe_sesion(self, numero_telefono: str, refresh_token: str) -> bool:
        return sesiones_col.find_one({
            'numeroTelefono': numero_telefono,
            'refreshToken': refresh_token,
        }) is not None
