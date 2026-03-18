# application/use_cases/auth/logout_usuario.py

from domain.ports.repositories.sesion_repository import SesionRepository


class LogoutUsuarioUseCase:
    """
    Caso de uso: cerrar sesión invalidando el refresh token.
    """

    def __init__(self, sesion_repo: SesionRepository):
        self._sesion_repo = sesion_repo

    def ejecutar(self, numero_telefono: str, refresh_token: str) -> None:
        self._sesion_repo.eliminar_sesion(numero_telefono, refresh_token)


# ─────────────────────────────────────────────────────────────────────────────


# application/use_cases/auth/refresh_token.py

from domain.exceptions import (
    UsuarioNoEncontradoError,
    UsuarioInactivoError,
    TokenInvalidoError,
)
from domain.ports.repositories.usuario_repository import UsuarioRepository
from domain.ports.services.token_service import TokenService


class RefreshTokenUseCase:
    """
    Caso de uso: renovar el access token usando un refresh token válido.
    """

    def __init__(
        self,
        usuario_repo: UsuarioRepository,
        token_service: TokenService,
    ):
        self._usuario_repo = usuario_repo
        self._token_service = token_service

    def ejecutar(self, numero_telefono: str) -> str:
        usuario = self._usuario_repo.buscar_por_telefono(numero_telefono)

        if not usuario:
            raise UsuarioNoEncontradoError("Usuario no encontrado")

        if not usuario.activo:
            raise UsuarioInactivoError("Usuario inactivo")

        return self._token_service.generar_access_token(
            usuario.numero_telefono, usuario.nombre
        )
