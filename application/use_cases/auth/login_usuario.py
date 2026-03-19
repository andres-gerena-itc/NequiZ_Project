# application/use_cases/auth/login_usuario.py

from datetime import datetime
from dataclasses import dataclass
from typing import Dict

from domain.exceptions import (
    CredencialesInvalidasError,
    UsuarioInactivoError,
)
from domain.ports.repositories.usuario_repository import UsuarioRepository
from domain.ports.repositories.sesion_repository import SesionRepository
from domain.ports.services.password_service import PasswordService
from domain.ports.services.token_service import TokenService
from config import Config


@dataclass
class LoginInput:
    numero_telefono: str
    password: str
    dispositivo: str = ''
    ip: str = ''


@dataclass
class LoginOutput:
    access_token: str
    refresh_token: str
    usuario: Dict


class LoginUsuarioUseCase:
    """
    Caso de uso: autenticar un usuario con número de teléfono y contraseña.
    """

    def __init__(
        self,
        usuario_repo: UsuarioRepository,
        sesion_repo: SesionRepository,
        password_service: PasswordService,
        token_service: TokenService,
    ):
        self._usuario_repo = usuario_repo
        self._sesion_repo = sesion_repo
        self._password_service = password_service
        self._token_service = token_service

    def ejecutar(self, datos: LoginInput) -> LoginOutput:
        usuario = self._usuario_repo.buscar_por_telefono(datos.numero_telefono)

        # Mensaje genérico para no revelar si el número existe
        if not usuario:
            raise CredencialesInvalidasError("Credenciales incorrectas")

        if not usuario.activo:
            raise UsuarioInactivoError("Usuario inactivo. Contacta a soporte")

        if not self._password_service.verificar(datos.password, usuario.password_hash):
            raise CredencialesInvalidasError("Credenciales incorrectas")

        # Generar tokens
        access_token = self._token_service.generar_access_token(
            usuario.numero_telefono, usuario.nombre
        )
        refresh_token = self._token_service.generar_refresh_token(usuario.numero_telefono)

        # Guardar sesión
        self._sesion_repo.guardar_sesion(
            numero_telefono=usuario.numero_telefono,
            refresh_token=refresh_token,
            fecha_expiracion=datetime.utcnow() + Config.JWT_REFRESH_TOKEN_EXPIRES,
            dispositivo=datos.dispositivo,
            ip=datos.ip,
        )

        return LoginOutput(
            access_token=access_token,
            refresh_token=refresh_token,
            usuario={
                'nombre': usuario.nombre,
                'numeroTelefono': usuario.numero_telefono,
                'email': usuario.email,
                'saldo': usuario.saldo,
            },
        )
