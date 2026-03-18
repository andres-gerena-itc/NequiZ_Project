# application/use_cases/perfil/obtener_perfil.py

from typing import Dict
from domain.exceptions import UsuarioNoEncontradoError
from domain.ports.repositories.usuario_repository import UsuarioRepository


class ObtenerPerfilUseCase:
    def __init__(self, usuario_repo: UsuarioRepository):
        self._usuario_repo = usuario_repo

    def ejecutar(self, numero_telefono: str) -> Dict:
        usuario = self._usuario_repo.buscar_por_telefono(numero_telefono)
        if not usuario:
            raise UsuarioNoEncontradoError("Usuario no encontrado")

        return {
            'nombre': usuario.nombre,
            'numeroTelefono': usuario.numero_telefono,
            'email': usuario.email,
            'saldo': usuario.saldo,
            'fechaRegistro': usuario.fecha_registro.isoformat(),
            'activo': usuario.activo,
            'perfil': {
                'foto': usuario.perfil.foto,
                'biografia': usuario.perfil.biografia,
            },
        }


# ─────────────────────────────────────────────────────────────────────────────


# application/use_cases/perfil/actualizar_perfil.py

from dataclasses import dataclass
from typing import Optional, Dict
from domain.exceptions import UsuarioNoEncontradoError
from domain.ports.repositories.usuario_repository import UsuarioRepository


@dataclass
class ActualizarPerfilInput:
    numero_telefono: str
    nombre: Optional[str] = None
    biografia: Optional[str] = None


class ActualizarPerfilUseCase:
    def __init__(self, usuario_repo: UsuarioRepository):
        self._usuario_repo = usuario_repo

    def ejecutar(self, datos: ActualizarPerfilInput) -> Dict:
        usuario = self._usuario_repo.buscar_por_telefono(datos.numero_telefono)
        if not usuario:
            raise UsuarioNoEncontradoError("Usuario no encontrado")

        if datos.nombre is not None:
            usuario.actualizar_nombre(datos.nombre)

        if datos.biografia is not None:
            usuario.actualizar_biografia(datos.biografia)

        self._usuario_repo.actualizar(usuario)

        return {
            'nombre': usuario.nombre,
            'numeroTelefono': usuario.numero_telefono,
            'email': usuario.email,
            'saldo': usuario.saldo,
            'fechaRegistro': usuario.fecha_registro.isoformat(),
            'perfil': {
                'foto': usuario.perfil.foto,
                'biografia': usuario.perfil.biografia,
            },
        }


# ─────────────────────────────────────────────────────────────────────────────


# application/use_cases/perfil/obtener_saldo.py

from typing import Dict
from domain.exceptions import UsuarioNoEncontradoError
from domain.ports.repositories.usuario_repository import UsuarioRepository


class ObtenerSaldoUseCase:
    def __init__(self, usuario_repo: UsuarioRepository):
        self._usuario_repo = usuario_repo

    def ejecutar(self, numero_telefono: str) -> Dict:
        usuario = self._usuario_repo.buscar_por_telefono(numero_telefono)
        if not usuario:
            raise UsuarioNoEncontradoError("Usuario no encontrado")

        return {
            'saldo': usuario.saldo,
            'numeroTelefono': usuario.numero_telefono,
        }
