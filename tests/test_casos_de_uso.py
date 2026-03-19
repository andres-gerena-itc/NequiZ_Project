# tests/test_casos_de_uso.py
# Pruebas de integración ligera: casos de uso reales + repositorios en memoria.
# Demuestra el checklist de salida de la Fase 3:
#   "Los mismos casos de uso funcionan con repositorio en memoria
#    y con el repositorio real cambiando solo la configuración."
#
# Ejecutar con: python -m pytest tests/test_casos_de_uso.py -v
# NO requiere MongoDB, internet ni ninguna infraestructura.

import pytest
from datetime import datetime

from application.use_cases.auth.registrar_usuario import (
    RegistrarUsuarioUseCase, RegistrarUsuarioInput,
)
from application.use_cases.auth.login_usuario import (
    LoginUsuarioUseCase, LoginInput,
)
from application.use_cases.auth.logout_usuario import (
    LogoutUsuarioUseCase, RefreshTokenUseCase,
)
from application.use_cases.perfil.obtener_perfil import (
    ObtenerPerfilUseCase, ActualizarPerfilUseCase,
    ObtenerSaldoUseCase, ActualizarPerfilInput,
)
from application.use_cases.transferencias.enviar_dinero import (
    EnviarDineroUseCase, EnviarDineroInput,
    ValidarDestinatarioUseCase,
)
from application.use_cases.movimientos.obtener_movimientos import (
    ObtenerMovimientosUseCase, ObtenerMovimientosInput,
    ObtenerEstadisticasUseCase, ObtenerEstadisticasInput,
)
from domain.entities.transaccion import TipoMovimiento
from domain.exceptions import (
    UsuarioYaExisteError, CredencialesInvalidasError,
    UsuarioNoEncontradoError, SaldoInsuficienteError,
)

from tests.fakes.fake_usuario_repository import FakeUsuarioRepository
from tests.fakes.fake_transaccion_repository import FakeTransaccionRepository
from tests.fakes.fake_sesion_repository import FakeSesionRepository
from tests.fakes.fake_password_service import FakePasswordService
from tests.fakes.fake_token_service import FakeTokenService


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES — fábricas de casos de uso con repositorios en memoria
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def repos():
    """Repositorios en memoria compartidos entre casos de uso del mismo test."""
    return {
        'usuario': FakeUsuarioRepository(),
        'transaccion': FakeTransaccionRepository(),
        'sesion': FakeSesionRepository(),
        'password': FakePasswordService(),
        'token': FakeTokenService(),
    }


@pytest.fixture
def registrar_uc(repos):
    return RegistrarUsuarioUseCase(
        usuario_repo=repos['usuario'],
        sesion_repo=repos['sesion'],
        password_service=repos['password'],
        token_service=repos['token'],
    )


@pytest.fixture
def login_uc(repos):
    return LoginUsuarioUseCase(
        usuario_repo=repos['usuario'],
        sesion_repo=repos['sesion'],
        password_service=repos['password'],
        token_service=repos['token'],
    )


@pytest.fixture
def usuario_registrado(registrar_uc, repos):
    """Registra un usuario de prueba y lo retorna junto con los repos."""
    resultado = registrar_uc.ejecutar(RegistrarUsuarioInput(
        nombre='Juan Pérez',
        numero_telefono='3001234567',
        email='juan@nequiz.com',
        password='password123',
    ))
    return resultado, repos


# ═══════════════════════════════════════════════════════════════════════════
# BLOQUE 1 — Caso de uso: Registrar Usuario
# ═══════════════════════════════════════════════════════════════════════════

class TestRegistrarUsuario:

    def test_01_registrar_usuario_retorna_tokens(self, registrar_uc):
        """El caso de uso debe retornar access y refresh token al registrar."""
        resultado = registrar_uc.ejecutar(RegistrarUsuarioInput(
            nombre='Ana Torres',
            numero_telefono='3001111111',
            email='ana@nequiz.com',
            password='pass123',
        ))
        assert resultado.access_token == 'fake_access_3001111111'
        assert resultado.refresh_token == 'fake_refresh_3001111111'

    def test_02_registrar_usuario_guarda_en_repositorio(self, registrar_uc, repos):
        """Después de registrar, el usuario debe existir en el repositorio."""
        registrar_uc.ejecutar(RegistrarUsuarioInput(
            nombre='Carlos Ruiz',
            numero_telefono='3002222222',
            email='carlos@nequiz.com',
            password='pass123',
        ))
        assert repos['usuario'].existe_telefono('3002222222')

    def test_03_registrar_usuario_hashea_la_contrasena(self, registrar_uc, repos):
        """La contraseña guardada no debe ser el texto plano."""
        registrar_uc.ejecutar(RegistrarUsuarioInput(
            nombre='Luis Mora',
            numero_telefono='3003333333',
            email='luis@nequiz.com',
            password='mipassword',
        ))
        usuario = repos['usuario'].buscar_por_telefono('3003333333')
        assert usuario.password_hash != 'mipassword'
        assert usuario.password_hash == 'hashed_mipassword'

    def test_04_registrar_usuario_duplicado_lanza_error(self, registrar_uc):
        """Registrar dos veces el mismo número debe lanzar UsuarioYaExisteError."""
        datos = RegistrarUsuarioInput(
            nombre='Pedro Gil',
            numero_telefono='3004444444',
            email='pedro@nequiz.com',
            password='pass123',
        )
        registrar_uc.ejecutar(datos)
        with pytest.raises(UsuarioYaExisteError):
            registrar_uc.ejecutar(datos)

    def test_05_registrar_guarda_sesion(self, registrar_uc, repos):
        """Al registrar, debe crearse una sesión activa con el refresh token."""
        registrar_uc.ejecutar(RegistrarUsuarioInput(
            nombre='Sofia Paz',
            numero_telefono='3005555555',
            email='sofia@nequiz.com',
            password='pass123',
        ))
        assert repos['sesion'].existe_sesion('3005555555', 'fake_refresh_3005555555')

    def test_06_email_duplicado_lanza_error(self, registrar_uc):
        """Registrar con email ya existente debe lanzar UsuarioYaExisteError."""
        registrar_uc.ejecutar(RegistrarUsuarioInput(
            nombre='Mario López',
            numero_telefono='3006666666',
            email='duplicado@nequiz.com',
            password='pass123',
        ))
        with pytest.raises(UsuarioYaExisteError):
            registrar_uc.ejecutar(RegistrarUsuarioInput(
                nombre='Otro Usuario',
                numero_telefono='3007777777',
                email='duplicado@nequiz.com',
                password='pass456',
            ))


# ═══════════════════════════════════════════════════════════════════════════
# BLOQUE 2 — Caso de uso: Login
# ═══════════════════════════════════════════════════════════════════════════

class TestLoginUsuario:

    def test_07_login_exitoso_retorna_tokens(self, usuario_registrado, login_uc):
        """Login con credenciales correctas debe retornar tokens válidos."""
        resultado = login_uc.ejecutar(LoginInput(
            numero_telefono='3001234567',
            password='password123',
        ))
        assert resultado.access_token == 'fake_access_3001234567'
        assert resultado.refresh_token == 'fake_refresh_3001234567'

    def test_08_login_contrasena_incorrecta_lanza_error(self, usuario_registrado, login_uc):
        """Login con contraseña incorrecta debe lanzar CredencialesInvalidasError."""
        with pytest.raises(CredencialesInvalidasError):
            login_uc.ejecutar(LoginInput(
                numero_telefono='3001234567',
                password='wrongpassword',
            ))

    def test_09_login_usuario_inexistente_lanza_error(self, login_uc):
        """Login con número no registrado debe lanzar CredencialesInvalidasError."""
        with pytest.raises(CredencialesInvalidasError):
            login_uc.ejecutar(LoginInput(
                numero_telefono='3009999999',
                password='password123',
            ))

    def test_10_login_retorna_datos_del_usuario(self, usuario_registrado, login_uc):
        """El resultado del login debe incluir nombre, teléfono y email."""
        resultado = login_uc.ejecutar(LoginInput(
            numero_telefono='3001234567',
            password='password123',
        ))
        assert resultado.usuario['nombre'] == 'Juan Pérez'
        assert resultado.usuario['numeroTelefono'] == '3001234567'


# ═══════════════════════════════════════════════════════════════════════════
# BLOQUE 3 — Caso de uso: Perfil
# ═══════════════════════════════════════════════════════════════════════════

class TestPerfil:

    def test_11_obtener_perfil_retorna_datos_correctos(self, usuario_registrado):
        _, repos = usuario_registrado
        uc = ObtenerPerfilUseCase(usuario_repo=repos['usuario'])
        perfil = uc.ejecutar('3001234567')
        assert perfil['nombre'] == 'Juan Pérez'
        assert perfil['email'] == 'juan@nequiz.com'

    def test_12_obtener_perfil_inexistente_lanza_error(self, repos):
        uc = ObtenerPerfilUseCase(usuario_repo=repos['usuario'])
        with pytest.raises(UsuarioNoEncontradoError):
            uc.ejecutar('3009999999')

    def test_13_actualizar_nombre_persiste_cambio(self, usuario_registrado):
        _, repos = usuario_registrado
        uc = ActualizarPerfilUseCase(usuario_repo=repos['usuario'])
        uc.ejecutar(ActualizarPerfilInput(
            numero_telefono='3001234567',
            nombre='Juan Pérez González',
        ))
        usuario = repos['usuario'].buscar_por_telefono('3001234567')
        assert usuario.nombre == 'Juan Pérez González'

    def test_14_obtener_saldo_retorna_valor_correcto(self, usuario_registrado):
        _, repos = usuario_registrado
        uc = ObtenerSaldoUseCase(usuario_repo=repos['usuario'])
        resultado = uc.ejecutar('3001234567')
        assert resultado['saldo'] == 100_000.0


# ═══════════════════════════════════════════════════════════════════════════
# BLOQUE 4 — Caso de uso: Transferencias
# ═══════════════════════════════════════════════════════════════════════════

class TestTransferencias:

    @pytest.fixture
    def dos_usuarios(self, registrar_uc, repos):
        """Registra dos usuarios para pruebas de transferencia."""
        registrar_uc.ejecutar(RegistrarUsuarioInput(
            nombre='Juan Pérez', numero_telefono='3001234567',
            email='juan@nequiz.com', password='pass123',
        ))
        registrar_uc.ejecutar(RegistrarUsuarioInput(
            nombre='María García', numero_telefono='3009876543',
            email='maria@nequiz.com', password='pass456',
        ))
        return repos

    def test_15_enviar_dinero_descuenta_saldo_origen(self, dos_usuarios):
        uc = EnviarDineroUseCase(
            usuario_repo=dos_usuarios['usuario'],
            transaccion_repo=dos_usuarios['transaccion'],
        )
        uc.ejecutar(EnviarDineroInput(
            numero_origen='3001234567',
            numero_destino='3009876543',
            monto=30_000.0,
        ))
        origen = dos_usuarios['usuario'].buscar_por_telefono('3001234567')
        assert origen.saldo == 70_000.0

    def test_16_enviar_dinero_acredita_saldo_destino(self, dos_usuarios):
        uc = EnviarDineroUseCase(
            usuario_repo=dos_usuarios['usuario'],
            transaccion_repo=dos_usuarios['transaccion'],
        )
        uc.ejecutar(EnviarDineroInput(
            numero_origen='3001234567',
            numero_destino='3009876543',
            monto=50_000.0,
        ))
        destino = dos_usuarios['usuario'].buscar_por_telefono('3009876543')
        assert destino.saldo == 150_000.0

    def test_17_enviar_dinero_registra_transaccion(self, dos_usuarios):
        uc = EnviarDineroUseCase(
            usuario_repo=dos_usuarios['usuario'],
            transaccion_repo=dos_usuarios['transaccion'],
        )
        uc.ejecutar(EnviarDineroInput(
            numero_origen='3001234567',
            numero_destino='3009876543',
            monto=20_000.0,
        ))
        total = dos_usuarios['transaccion'].contar_por_usuario('3001234567')
        assert total == 1

    def test_18_enviar_dinero_insuficiente_lanza_error(self, dos_usuarios):
        uc = EnviarDineroUseCase(
            usuario_repo=dos_usuarios['usuario'],
            transaccion_repo=dos_usuarios['transaccion'],
        )
        with pytest.raises(SaldoInsuficienteError):
            uc.ejecutar(EnviarDineroInput(
                numero_origen='3001234567',
                numero_destino='3009876543',
                monto=999_999.0,
            ))

    def test_19_validar_destinatario_existente(self, dos_usuarios):
        uc = ValidarDestinatarioUseCase(usuario_repo=dos_usuarios['usuario'])
        resultado = uc.ejecutar('3009876543')
        assert resultado.existe is True
        assert resultado.nombre == 'María García'

    def test_20_validar_destinatario_inexistente(self, dos_usuarios):
        uc = ValidarDestinatarioUseCase(usuario_repo=dos_usuarios['usuario'])
        resultado = uc.ejecutar('3001111111')
        assert resultado.existe is False


# ═══════════════════════════════════════════════════════════════════════════
# BLOQUE 5 — Caso de uso: Movimientos y Estadísticas
# ═══════════════════════════════════════════════════════════════════════════

class TestMovimientos:

    @pytest.fixture
    def escenario_con_transacciones(self, registrar_uc, repos):
        """Registra dos usuarios y realiza dos transferencias."""
        registrar_uc.ejecutar(RegistrarUsuarioInput(
            nombre='Juan Pérez', numero_telefono='3001234567',
            email='juan@nequiz.com', password='pass123',
        ))
        registrar_uc.ejecutar(RegistrarUsuarioInput(
            nombre='María García', numero_telefono='3009876543',
            email='maria@nequiz.com', password='pass456',
        ))
        enviar_uc = EnviarDineroUseCase(
            usuario_repo=repos['usuario'],
            transaccion_repo=repos['transaccion'],
        )
        enviar_uc.ejecutar(EnviarDineroInput(
            numero_origen='3001234567', numero_destino='3009876543', monto=20_000.0
        ))
        enviar_uc.ejecutar(EnviarDineroInput(
            numero_origen='3001234567', numero_destino='3009876543', monto=10_000.0
        ))
        return repos

    def test_21_obtener_movimientos_retorna_lista(self, escenario_con_transacciones):
        uc = ObtenerMovimientosUseCase(
            transaccion_repo=escenario_con_transacciones['transaccion']
        )
        movimientos = uc.ejecutar(ObtenerMovimientosInput(
            numero_telefono='3001234567',
            tipo=TipoMovimiento.TODOS,
        ))
        assert len(movimientos) == 2

    def test_22_movimientos_filtrados_por_tipo_enviado(self, escenario_con_transacciones):
        uc = ObtenerMovimientosUseCase(
            transaccion_repo=escenario_con_transacciones['transaccion']
        )
        movimientos = uc.ejecutar(ObtenerMovimientosInput(
            numero_telefono='3001234567',
            tipo=TipoMovimiento.ENVIADO,
        ))
        assert all(m['tipo'] == 'ENVIADO' for m in movimientos)

    def test_23_estadisticas_calcula_total_enviado(self, escenario_con_transacciones):
        uc = ObtenerEstadisticasUseCase(
            transaccion_repo=escenario_con_transacciones['transaccion']
        )
        stats = uc.ejecutar(ObtenerEstadisticasInput(
            numero_telefono='3001234567',
            periodo='TODO',
        ))
        assert stats['total_enviado'] == 30_000.0

    def test_24_estadisticas_calcula_total_recibido(self, escenario_con_transacciones):
        uc = ObtenerEstadisticasUseCase(
            transaccion_repo=escenario_con_transacciones['transaccion']
        )
        stats = uc.ejecutar(ObtenerEstadisticasInput(
            numero_telefono='3009876543',
            periodo='TODO',
        ))
        assert stats['total_recibido'] == 30_000.0

    def test_25_estadisticas_calcula_balance(self, escenario_con_transacciones):
        uc = ObtenerEstadisticasUseCase(
            transaccion_repo=escenario_con_transacciones['transaccion']
        )
        stats = uc.ejecutar(ObtenerEstadisticasInput(
            numero_telefono='3001234567',
            periodo='TODO',
        ))
        # Juan envió 30k y no recibió nada → balance negativo
        assert stats['balance'] == -30_000.0
