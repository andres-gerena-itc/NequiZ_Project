# application/use_cases/auth/registrar_usuario.py

from datetime import datetime
from dataclasses import dataclass
from typing import Dict

from domain.entities.usuario import Usuario, PerfilUsuario
from domain.exceptions import UsuarioYaExisteError
from domain.ports.repositories.usuario_repository import UsuarioRepository
from domain.ports.repositories.sesion_repository import SesionRepository
from domain.ports.services.password_service import PasswordService
from domain.ports.services.token_service import TokenService
from datetime import timedelta


@dataclass
class RegistrarUsuarioInput:
    nombre: str
    numero_telefono: str
    email: str
    password: str
    dispositivo: str = ''
    ip: str = ''


@dataclass
class RegistrarUsuarioOutput:
    access_token: str
    refresh_token: str
    usuario: Dict


class RegistrarUsuarioUseCase:
    """
    Caso de uso: registrar un nuevo usuario en el sistema.
    Solo depende de abstracciones (puertos), nunca de detalles concretos.
    """

    def __init__(
        self,
        usuario_repo,
        sesion_repo,
        password_service,
        token_service,
        saldo_inicial: float = 100_000.0,
        duracion_sesion: timedelta = timedelta(days=30),
    ):
        self._usuario_repo = usuario_repo
        self._sesion_repo = sesion_repo
        self._password_service = password_service
        self._token_service = token_service
        self._saldo_inicial = saldo_inicial
        self._duracion_sesion = duracion_sesion

    def ejecutar(self, datos: RegistrarUsuarioInput) -> RegistrarUsuarioOutput:
        # Verificar duplicados
        if self._usuario_repo.existe_telefono(datos.numero_telefono):
            raise UsuarioYaExisteError("Este número de teléfono ya está registrado")
        if self._usuario_repo.existe_email(datos.email.lower()):
            raise UsuarioYaExisteError("Este email ya está registrado")

        # Crear entidad de dominio
        password_hash = self._password_service.hashear(datos.password)
        usuario = Usuario(
            numero_telefono=datos.numero_telefono,
            nombre=datos.nombre,
            email=datos.email.lower(),
            password_hash=password_hash,
            saldo=self._saldo_inicial,
            fecha_registro=datetime.utcnow(),
            perfil=PerfilUsuario(),
        )

        # Persistir
        self._usuario_repo.guardar(usuario)

        # Generar tokens
        access_token = self._token_service.generar_access_token(
            usuario.numero_telefono, usuario.nombre
        )
        refresh_token = self._token_service.generar_refresh_token(usuario.numero_telefono)

        # Guardar sesión
        self._sesion_repo.guardar_sesion(
            numero_telefono=usuario.numero_telefono,
            refresh_token=refresh_token,
            fecha_expiracion=datetime.utcnow() + self._duracion_sesion,
            dispositivo=datos.dispositivo,
            ip=datos.ip,
        )

        return RegistrarUsuarioOutput(
            access_token=access_token,
            refresh_token=refresh_token,
            usuario={
                'nombre': usuario.nombre,
                'numeroTelefono': usuario.numero_telefono,
                'email': usuario.email,
                'saldo': usuario.saldo,
            },
        )
