# infrastructure/config/container.py
# Contenedor de Inyección de Dependencias
# Este es el único lugar donde se ensamblan los adaptadores con los casos de uso.
# El dominio nunca sabe qué implementaciones concretas se usan.

from infrastructure.adapters.secondary.mongodb.usuario_repository import MongoUsuarioRepository
from infrastructure.adapters.secondary.mongodb.transaccion_repository import MongoTransaccionRepository
from infrastructure.adapters.secondary.mongodb.sesion_repository import MongoSesionRepository
from infrastructure.adapters.secondary.jwt.jwt_token_service import JwtTokenService
from infrastructure.adapters.secondary.bcrypt.bcrypt_password_service import BcryptPasswordService
from config import Config

from application.use_cases.auth.registrar_usuario import RegistrarUsuarioUseCase
from application.use_cases.auth.login_usuario import LoginUsuarioUseCase
from application.use_cases.auth.logout_usuario import LogoutUsuarioUseCase, RefreshTokenUseCase
from application.use_cases.perfil.obtener_perfil import (
    ObtenerPerfilUseCase, ActualizarPerfilUseCase, ObtenerSaldoUseCase
)
from application.use_cases.transferencias.enviar_dinero import (
    EnviarDineroUseCase, ValidarDestinatarioUseCase
)
from application.use_cases.movimientos.obtener_movimientos import (
    ObtenerMovimientosUseCase, ObtenerEstadisticasUseCase
)


class Container:
    """
    Contenedor de dependencias: instancia adaptadores y casos de uso,
    y los conecta respetando la dirección de dependencias hexagonales.

    Flujo:
      Adaptadores secundarios (Mongo, JWT, Bcrypt)
          ↓  implementan puertos del dominio
      Casos de uso (Application layer)
          ↓  reciben puertos por constructor
      Adaptadores primarios (REST, GraphQL)
          ↓  reciben casos de uso por factory
    """

    def __init__(self):
        # ── Adaptadores secundarios ──────────────────────────────────────
        self.usuario_repo = MongoUsuarioRepository()
        self.transaccion_repo = MongoTransaccionRepository()
        self.sesion_repo = MongoSesionRepository()
        self.token_service = JwtTokenService()
        self.password_service = BcryptPasswordService()

        # ── Casos de uso: Auth ───────────────────────────────────────────
        self.registrar_usuario_uc = RegistrarUsuarioUseCase(
            usuario_repo=self.usuario_repo,
            sesion_repo=self.sesion_repo,
            password_service=self.password_service,
            token_service=self.token_service,
            saldo_inicial=Config.SALDO_INICIAL,
            duracion_sesion=Config.JWT_REFRESH_TOKEN_EXPIRES,
        )
        self.login_usuario_uc = LoginUsuarioUseCase(
            usuario_repo=self.usuario_repo,
            sesion_repo=self.sesion_repo,
            password_service=self.password_service,
            token_service=self.token_service,
            duracion_sesion=Config.JWT_REFRESH_TOKEN_EXPIRES,
        )
        self.logout_usuario_uc = LogoutUsuarioUseCase(sesion_repo=self.sesion_repo)
        self.refresh_token_uc = RefreshTokenUseCase(
            usuario_repo=self.usuario_repo,
            token_service=self.token_service,
        )

        # ── Casos de uso: Perfil ─────────────────────────────────────────
        self.obtener_perfil_uc = ObtenerPerfilUseCase(usuario_repo=self.usuario_repo)
        self.actualizar_perfil_uc = ActualizarPerfilUseCase(usuario_repo=self.usuario_repo)
        self.obtener_saldo_uc = ObtenerSaldoUseCase(usuario_repo=self.usuario_repo)

        # ── Casos de uso: Transferencias ─────────────────────────────────
        self.enviar_dinero_uc = EnviarDineroUseCase(
            usuario_repo=self.usuario_repo,
            transaccion_repo=self.transaccion_repo,
        )
        self.validar_destinatario_uc = ValidarDestinatarioUseCase(
            usuario_repo=self.usuario_repo
        )

        # ── Casos de uso: Movimientos ────────────────────────────────────
        self.obtener_movimientos_uc = ObtenerMovimientosUseCase(
            transaccion_repo=self.transaccion_repo
        )
        self.obtener_estadisticas_uc = ObtenerEstadisticasUseCase(
            transaccion_repo=self.transaccion_repo
        )
