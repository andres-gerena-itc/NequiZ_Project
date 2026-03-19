# tests/test_casos_de_uso_real.py
# Pruebas con repositorios REALES (MongoDB Atlas).
# Objetivo: verificar que la conexión con la infraestructura funciona correctamente.
# No repiten la lógica ya cubierta por test_casos_de_uso.py (fakes).
#
# Ejecutar con: python -m pytest tests/test_casos_de_uso_real.py -v
# Requiere: conexión activa a MongoDB y archivo .env configurado.

import pytest

from application.use_cases.auth.registrar_usuario import (
    RegistrarUsuarioUseCase, RegistrarUsuarioInput,
)
from application.use_cases.auth.login_usuario import (
    LoginUsuarioUseCase, LoginInput,
)
from application.use_cases.perfil.obtener_perfil import (
    ObtenerPerfilUseCase, ActualizarPerfilUseCase, ActualizarPerfilInput,
    ObtenerSaldoUseCase,
)
from application.use_cases.transferencias.enviar_dinero import (
    EnviarDineroUseCase, EnviarDineroInput,
)
from application.use_cases.movimientos.obtener_movimientos import (
    ObtenerMovimientosUseCase, ObtenerMovimientosInput,
)
from domain.entities.transaccion import TipoMovimiento
from domain.exceptions import CredencialesInvalidasError, UsuarioNoEncontradoError

from infrastructure.adapters.secondary.mongodb.usuario_repository import MongoUsuarioRepository
from infrastructure.adapters.secondary.mongodb.transaccion_repository import MongoTransaccionRepository
from infrastructure.adapters.secondary.mongodb.sesion_repository import MongoSesionRepository
from infrastructure.adapters.secondary.jwt.jwt_token_service import JwtTokenService
from infrastructure.adapters.secondary.bcrypt.bcrypt_password_service import BcryptPasswordService

# Números exclusivos para pruebas automáticas — no colisionan con usuarios reales
TELEFONO_TEST_1 = '3099999991'
TELEFONO_TEST_2 = '3099999992'
EMAIL_TEST_1 = 'test_real_1@nequiz.com'
EMAIL_TEST_2 = 'test_real_2@nequiz.com'


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def limpiar_usuarios_test():
    """Elimina los usuarios de prueba antes y después de cada test."""
    try:
        from infrastructure.adapters.secondary.mongodb.connection import usuarios_col, transacciones_col
        usuarios_col.delete_many({'numeroTelefono': {'$in': [TELEFONO_TEST_1, TELEFONO_TEST_2]}})
        transacciones_col.delete_many({'$or': [
            {'numeroOrigen': {'$in': [TELEFONO_TEST_1, TELEFONO_TEST_2]}},
            {'numeroDestino': {'$in': [TELEFONO_TEST_1, TELEFONO_TEST_2]}},
        ]})
    except Exception:
        pass
    yield
    try:
        from infrastructure.adapters.secondary.mongodb.connection import usuarios_col, transacciones_col
        usuarios_col.delete_many({'numeroTelefono': {'$in': [TELEFONO_TEST_1, TELEFONO_TEST_2]}})
        transacciones_col.delete_many({'$or': [
            {'numeroOrigen': {'$in': [TELEFONO_TEST_1, TELEFONO_TEST_2]}},
            {'numeroDestino': {'$in': [TELEFONO_TEST_1, TELEFONO_TEST_2]}},
        ]})
    except Exception:
        pass


@pytest.fixture
def repos():
    """Repositorios reales de MongoDB."""
    return {
        'usuario': MongoUsuarioRepository(),
        'transaccion': MongoTransaccionRepository(),
        'sesion': MongoSesionRepository(),
        'password': BcryptPasswordService(),
        'token': JwtTokenService(),
    }


@pytest.fixture
def usuario_registrado(repos):
    """Registra un usuario de prueba en MongoDB y lo retorna."""
    uc = RegistrarUsuarioUseCase(
        usuario_repo=repos['usuario'],
        sesion_repo=repos['sesion'],
        password_service=repos['password'],
        token_service=repos['token'],
    )
    resultado = uc.ejecutar(RegistrarUsuarioInput(
        nombre='Usuario Test Real',
        numero_telefono=TELEFONO_TEST_1,
        email=EMAIL_TEST_1,
        password='test123',
    ))
    return resultado, repos


@pytest.fixture
def dos_usuarios_registrados(repos):
    """Registra dos usuarios de prueba en MongoDB."""
    uc = RegistrarUsuarioUseCase(
        usuario_repo=repos['usuario'],
        sesion_repo=repos['sesion'],
        password_service=repos['password'],
        token_service=repos['token'],
    )
    uc.ejecutar(RegistrarUsuarioInput(
        nombre='Usuario Test 1',
        numero_telefono=TELEFONO_TEST_1,
        email=EMAIL_TEST_1,
        password='test123',
    ))
    uc.ejecutar(RegistrarUsuarioInput(
        nombre='Usuario Test 2',
        numero_telefono=TELEFONO_TEST_2,
        email=EMAIL_TEST_2,
        password='test456',
    ))
    return repos


# ═══════════════════════════════════════════════════════════════════════════
# BLOQUE 1 — Auth con MongoDB real
# ═══════════════════════════════════════════════════════════════════════════

def test_01_registrar_usuario_persiste_en_mongodb(repos):
    """Registrar un usuario debe guardarlo realmente en MongoDB."""
    uc = RegistrarUsuarioUseCase(
        usuario_repo=repos['usuario'],
        sesion_repo=repos['sesion'],
        password_service=repos['password'],
        token_service=repos['token'],
    )
    resultado = uc.ejecutar(RegistrarUsuarioInput(
        nombre='Usuario Test Real',
        numero_telefono=TELEFONO_TEST_1,
        email=EMAIL_TEST_1,
        password='test123',
    ))

    # Verifica que el token es un JWT real (no un fake)
    assert resultado.access_token is not None
    assert len(resultado.access_token) > 20

    # Verifica que realmente se guardó en MongoDB
    assert repos['usuario'].existe_telefono(TELEFONO_TEST_1)


def test_02_login_exitoso_contra_mongodb(usuario_registrado):
    """Login con credenciales correctas debe funcionar contra MongoDB real."""
    _, repos = usuario_registrado
    uc = LoginUsuarioUseCase(
        usuario_repo=repos['usuario'],
        sesion_repo=repos['sesion'],
        password_service=repos['password'],
        token_service=repos['token'],
    )
    resultado = uc.ejecutar(LoginInput(
        numero_telefono=TELEFONO_TEST_1,
        password='test123',
    ))
    assert resultado.access_token is not None
    assert resultado.usuario['numeroTelefono'] == TELEFONO_TEST_1


def test_03_login_contrasena_incorrecta_contra_mongodb(usuario_registrado):
    """Contraseña incorrecta debe fallar contra el hash real de bcrypt."""
    _, repos = usuario_registrado
    uc = LoginUsuarioUseCase(
        usuario_repo=repos['usuario'],
        sesion_repo=repos['sesion'],
        password_service=repos['password'],
        token_service=repos['token'],
    )
    with pytest.raises(CredencialesInvalidasError):
        uc.ejecutar(LoginInput(
            numero_telefono=TELEFONO_TEST_1,
            password='contrasena_incorrecta',
        ))


# ═══════════════════════════════════════════════════════════════════════════
# BLOQUE 2 — Perfil con MongoDB real
# ═══════════════════════════════════════════════════════════════════════════

def test_04_obtener_perfil_desde_mongodb(usuario_registrado):
    """Los datos del perfil deben recuperarse correctamente desde MongoDB."""
    _, repos = usuario_registrado
    uc = ObtenerPerfilUseCase(usuario_repo=repos['usuario'])
    perfil = uc.ejecutar(TELEFONO_TEST_1)

    assert perfil['nombre'] == 'Usuario Test Real'
    assert perfil['email'] == EMAIL_TEST_1
    assert perfil['saldo'] == 100_000.0


def test_05_actualizar_perfil_persiste_en_mongodb(usuario_registrado):
    """Actualizar el nombre debe reflejarse en MongoDB al volver a consultar."""
    _, repos = usuario_registrado
    uc = ActualizarPerfilUseCase(usuario_repo=repos['usuario'])
    uc.ejecutar(ActualizarPerfilInput(
        numero_telefono=TELEFONO_TEST_1,
        nombre='Nombre Actualizado Real',
        biografia='Bio de prueba real',
    ))

    # Volver a consultar desde MongoDB para confirmar persistencia
    perfil = ObtenerPerfilUseCase(usuario_repo=repos['usuario']).ejecutar(TELEFONO_TEST_1)
    assert perfil['nombre'] == 'Nombre Actualizado Real'
    assert perfil['perfil']['biografia'] == 'Bio de prueba real'


def test_06_obtener_saldo_desde_mongodb(usuario_registrado):
    """El saldo debe leerse correctamente desde MongoDB."""
    _, repos = usuario_registrado
    uc = ObtenerSaldoUseCase(usuario_repo=repos['usuario'])
    resultado = uc.ejecutar(TELEFONO_TEST_1)
    assert resultado['saldo'] == 100_000.0
    assert resultado['numeroTelefono'] == TELEFONO_TEST_1


# ═══════════════════════════════════════════════════════════════════════════
# BLOQUE 3 — Transferencias y movimientos con MongoDB real
# ═══════════════════════════════════════════════════════════════════════════

def test_07_transferencia_actualiza_saldos_en_mongodb(dos_usuarios_registrados):
    """Una transferencia real debe actualizar los saldos en MongoDB."""
    repos = dos_usuarios_registrados
    uc = EnviarDineroUseCase(
        usuario_repo=repos['usuario'],
        transaccion_repo=repos['transaccion'],
    )
    uc.ejecutar(EnviarDineroInput(
        numero_origen=TELEFONO_TEST_1,
        numero_destino=TELEFONO_TEST_2,
        monto=25_000.0,
        mensaje='Pago prueba real',
    ))

    # Verificar saldos directamente en MongoDB
    origen = repos['usuario'].buscar_por_telefono(TELEFONO_TEST_1)
    destino = repos['usuario'].buscar_por_telefono(TELEFONO_TEST_2)
    assert origen.saldo == 75_000.0
    assert destino.saldo == 125_000.0


def test_08_transferencia_guarda_transaccion_en_mongodb(dos_usuarios_registrados):
    """La transacción debe quedar registrada en la colección de MongoDB."""
    repos = dos_usuarios_registrados
    uc = EnviarDineroUseCase(
        usuario_repo=repos['usuario'],
        transaccion_repo=repos['transaccion'],
    )
    uc.ejecutar(EnviarDineroInput(
        numero_origen=TELEFONO_TEST_1,
        numero_destino=TELEFONO_TEST_2,
        monto=10_000.0,
    ))

    total = repos['transaccion'].contar_por_usuario(TELEFONO_TEST_1)
    assert total == 1


def test_09_obtener_movimientos_desde_mongodb(dos_usuarios_registrados):
    """Los movimientos deben recuperarse correctamente desde MongoDB."""
    repos = dos_usuarios_registrados
    enviar_uc = EnviarDineroUseCase(
        usuario_repo=repos['usuario'],
        transaccion_repo=repos['transaccion'],
    )
    enviar_uc.ejecutar(EnviarDineroInput(
        numero_origen=TELEFONO_TEST_1,
        numero_destino=TELEFONO_TEST_2,
        monto=15_000.0,
    ))

    movimientos_uc = ObtenerMovimientosUseCase(transaccion_repo=repos['transaccion'])
    movimientos = movimientos_uc.ejecutar(ObtenerMovimientosInput(
        numero_telefono=TELEFONO_TEST_1,
        tipo=TipoMovimiento.ENVIADO,
    ))

    assert len(movimientos) == 1
    assert movimientos[0]['monto'] == 15_000.0
    assert movimientos[0]['tipo'] == 'ENVIADO'