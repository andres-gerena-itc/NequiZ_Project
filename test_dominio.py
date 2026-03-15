# Pruebas unitarias del dominio NequiZ
# Cubre: Usuario, Transaccion, Enums y Excepciones

import pytest
from datetime import datetime

from domain.entities.usuario import Usuario, PerfilUsuario
from domain.entities.transaccion import (
    Transaccion, EstadoTransaccion, TipoTransaccion, TipoMovimiento
)
from domain.exceptions import (
    SaldoInsuficienteError, MontoInvalidoError, TransaccionInvalidaError,
    DomainError, UsuarioNoEncontradoError, UsuarioYaExisteError,
    UsuarioInactivoError, CredencialesInvalidasError, TokenInvalidoError,
)


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES — datos base reutilizables en múltiples pruebas
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def usuario_base():
    """Usuario estándar con saldo de $500.000 para reutilizar en pruebas."""
    return Usuario(
        numero_telefono='3001234567',
        nombre='Juan Pérez',
        email='juan@nequiz.com',
        password_hash='hash_seguro_123',
        saldo=500_000.0,
        fecha_registro=datetime(2025, 1, 15, 10, 30),
    )


@pytest.fixture
def transaccion_base():
    """Transacción válida entre dos usuarios distintos."""
    return Transaccion(
        numero_origen='3001234567',
        nombre_origen='Juan Pérez',
        numero_destino='3009876543',
        nombre_destino='María García',
        monto=50_000.0,
        fecha=datetime(2025, 6, 1, 12, 0),
    )


# ═══════════════════════════════════════════════════════════════════════════
# BLOQUE 1 — Entidad Usuario: saldo
# ═══════════════════════════════════════════════════════════════════════════

class TestUsuarioSaldo:

    def test_01_debitar_descuenta_saldo_correctamente(self, usuario_base):
        """Después de debitar, el saldo debe reducirse exactamente en el monto."""
        usuario_base.debitar(100_000.0)
        assert usuario_base.saldo == 400_000.0

    def test_02_acreditar_suma_saldo_correctamente(self, usuario_base):
        """Después de acreditar, el saldo debe aumentar exactamente en el monto."""
        usuario_base.acreditar(200_000.0)
        assert usuario_base.saldo == 700_000.0

    def test_03_tiene_saldo_suficiente_retorna_true_cuando_alcanza(self, usuario_base):
        """Con saldo igual al monto requerido, debe retornar True."""
        assert usuario_base.tiene_saldo_suficiente(500_000.0) is True

    def test_04_tiene_saldo_suficiente_retorna_false_cuando_no_alcanza(self, usuario_base):
        """Con saldo menor al monto requerido, debe retornar False."""
        assert usuario_base.tiene_saldo_suficiente(600_000.0) is False

    def test_05_debitar_lanza_error_si_saldo_insuficiente(self, usuario_base):
        """Intentar debitar más del saldo disponible debe lanzar SaldoInsuficienteError."""
        with pytest.raises(SaldoInsuficienteError):
            usuario_base.debitar(999_999.0)

    def test_06_debitar_lanza_error_si_monto_es_cero(self, usuario_base):
        """Debitar con monto cero debe lanzar MontoInvalidoError."""
        with pytest.raises(MontoInvalidoError):
            usuario_base.debitar(0)

    def test_07_debitar_lanza_error_si_monto_es_negativo(self, usuario_base):
        """Debitar con monto negativo debe lanzar MontoInvalidoError."""
        with pytest.raises(MontoInvalidoError):
            usuario_base.debitar(-10_000.0)

    def test_08_acreditar_lanza_error_si_monto_es_cero(self, usuario_base):
        """Acreditar con monto cero debe lanzar MontoInvalidoError."""
        with pytest.raises(MontoInvalidoError):
            usuario_base.acreditar(0)

    def test_09_acreditar_lanza_error_si_monto_es_negativo(self, usuario_base):
        """Acreditar con monto negativo debe lanzar MontoInvalidoError."""
        with pytest.raises(MontoInvalidoError):
            usuario_base.acreditar(-5_000.0)

    def test_10_debitar_y_acreditar_son_consistentes(self, usuario_base):
        """Debitar y luego acreditar el mismo monto debe dejar el saldo igual."""
        saldo_original = usuario_base.saldo
        usuario_base.debitar(100_000.0)
        usuario_base.acreditar(100_000.0)
        assert usuario_base.saldo == saldo_original


# ═══════════════════════════════════════════════════════════════════════════
# BLOQUE 2 — Entidad Usuario: datos personales y estado
# ═══════════════════════════════════════════════════════════════════════════

class TestUsuarioDatos:

    def test_11_desactivar_cambia_activo_a_false(self, usuario_base):
        """Después de desactivar, el campo activo debe ser False."""
        usuario_base.desactivar()
        assert usuario_base.activo is False

    def test_12_usuario_nuevo_esta_activo_por_defecto(self, usuario_base):
        """Un usuario recién creado debe tener activo=True por defecto."""
        assert usuario_base.activo is True

    def test_13_actualizar_nombre_cambia_el_nombre(self, usuario_base):
        """Actualizar el nombre debe reflejarse en el atributo nombre."""
        usuario_base.actualizar_nombre('Carlos López')
        assert usuario_base.nombre == 'Carlos López'

    def test_14_actualizar_nombre_elimina_espacios_extremos(self, usuario_base):
        """Actualizar nombre con espacios al inicio/fin debe eliminarlos."""
        usuario_base.actualizar_nombre('  Ana Torres  ')
        assert usuario_base.nombre == 'Ana Torres'

    def test_15_actualizar_nombre_lanza_error_si_es_muy_corto(self, usuario_base):
        """Nombre con menos de 2 caracteres debe lanzar ValueError."""
        with pytest.raises(ValueError):
            usuario_base.actualizar_nombre('A')

    def test_16_actualizar_nombre_lanza_error_si_esta_vacio(self, usuario_base):
        """Nombre vacío debe lanzar ValueError."""
        with pytest.raises(ValueError):
            usuario_base.actualizar_nombre('')

    def test_17_actualizar_biografia_guarda_el_texto(self, usuario_base):
        """La biografía debe guardarse correctamente en el perfil."""
        usuario_base.actualizar_biografia('Amante del café y el código.')
        assert usuario_base.perfil.biografia == 'Amante del café y el código.'

    def test_18_actualizar_biografia_lanza_error_si_supera_500_caracteres(self, usuario_base):
        """Biografía con más de 500 caracteres debe lanzar ValueError."""
        bio_larga = 'x' * 501
        with pytest.raises(ValueError):
            usuario_base.actualizar_biografia(bio_larga)

    def test_19_biografia_exactamente_500_caracteres_es_valida(self, usuario_base):
        """Biografía con exactamente 500 caracteres debe aceptarse sin error."""
        bio_exacta = 'a' * 500
        usuario_base.actualizar_biografia(bio_exacta)
        assert len(usuario_base.perfil.biografia) == 500

    def test_20_perfil_usuario_tiene_valores_por_defecto(self):
        """Un PerfilUsuario nuevo debe tener foto=None y biografia vacía."""
        perfil = PerfilUsuario()
        assert perfil.foto is None
        assert perfil.biografia == ''


# ═══════════════════════════════════════════════════════════════════════════
# BLOQUE 3 — Entidad Transacción
# ═══════════════════════════════════════════════════════════════════════════

class TestTransaccion:

    def test_21_transaccion_valida_se_crea_sin_errores(self, transaccion_base):
        """Una transacción con datos correctos debe crearse exitosamente."""
        assert transaccion_base.monto == 50_000.0
        assert transaccion_base.estado == EstadoTransaccion.EXITOSA

    def test_22_transaccion_genera_id_automaticamente(self, transaccion_base):
        """Una transacción nueva debe tener un ID generado automáticamente."""
        assert transaccion_base.id is not None
        assert len(transaccion_base.id) > 0

    def test_23_dos_transacciones_tienen_ids_distintos(self):
        """Dos transacciones creadas independientemente deben tener IDs únicos."""
        datos = dict(
            numero_origen='3001234567', nombre_origen='Juan',
            numero_destino='3009876543', nombre_destino='María',
            monto=10_000.0, fecha=datetime.utcnow()
        )
        t1 = Transaccion(**datos)
        t2 = Transaccion(**datos)
        assert t1.id != t2.id

    def test_24_transaccion_lanza_error_si_monto_es_cero(self):
        """Crear una transacción con monto cero debe lanzar MontoInvalidoError."""
        with pytest.raises(MontoInvalidoError):
            Transaccion(
                numero_origen='3001234567', nombre_origen='Juan',
                numero_destino='3009876543', nombre_destino='María',
                monto=0, fecha=datetime.utcnow()
            )

    def test_25_transaccion_lanza_error_si_monto_es_negativo(self):
        """Crear una transacción con monto negativo debe lanzar MontoInvalidoError."""
        with pytest.raises(MontoInvalidoError):
            Transaccion(
                numero_origen='3001234567', nombre_origen='Juan',
                numero_destino='3009876543', nombre_destino='María',
                monto=-1_000.0, fecha=datetime.utcnow()
            )

    def test_26_transaccion_lanza_error_si_origen_igual_a_destino(self):
        """Un usuario no puede enviarse dinero a sí mismo."""
        with pytest.raises(TransaccionInvalidaError):
            Transaccion(
                numero_origen='3001234567', nombre_origen='Juan',
                numero_destino='3001234567', nombre_destino='Juan',
                monto=50_000.0, fecha=datetime.utcnow()
            )

    def test_27_transaccion_lanza_error_si_monto_supera_limite(self):
        """Monto mayor a 50 millones debe lanzar MontoInvalidoError."""
        with pytest.raises(MontoInvalidoError):
            Transaccion(
                numero_origen='3001234567', nombre_origen='Juan',
                numero_destino='3009876543', nombre_destino='María',
                monto=50_000_001.0, fecha=datetime.utcnow()
            )

    def test_28_tipo_para_usuario_retorna_enviado_al_origen(self, transaccion_base):
        """Para el número origen, el tipo de movimiento debe ser ENVIADO."""
        tipo = transaccion_base.tipo_para_usuario('3001234567')
        assert tipo == TipoMovimiento.ENVIADO

    def test_29_tipo_para_usuario_retorna_recibido_al_destino(self, transaccion_base):
        """Para el número destino, el tipo de movimiento debe ser RECIBIDO."""
        tipo = transaccion_base.tipo_para_usuario('3009876543')
        assert tipo == TipoMovimiento.RECIBIDO

    def test_30_tipo_para_usuario_retorna_recibido_para_tercero(self, transaccion_base):
        """Para un número que no es origen, debe retornar RECIBIDO."""
        tipo = transaccion_base.tipo_para_usuario('3001111111')
        assert tipo == TipoMovimiento.RECIBIDO

    def test_31_marcar_como_fallida_cambia_el_estado(self, transaccion_base):
        """Después de marcarla como fallida, el estado debe ser FALLIDA."""
        transaccion_base.marcar_como_fallida()
        assert transaccion_base.estado == EstadoTransaccion.FALLIDA

    def test_32_transaccion_exactamente_en_limite_es_valida(self):
        """Una transacción con exactamente 50 millones debe ser válida."""
        t = Transaccion(
            numero_origen='3001234567', nombre_origen='Juan',
            numero_destino='3009876543', nombre_destino='María',
            monto=50_000_000.0, fecha=datetime.utcnow()
        )
        assert t.monto == 50_000_000.0


# ═══════════════════════════════════════════════════════════════════════════
# BLOQUE 4 — Excepciones de dominio
# ═══════════════════════════════════════════════════════════════════════════

class TestExcepcionesDominio:

    def test_33_todas_las_excepciones_heredan_de_domain_error(self):
        """Todas las excepciones de dominio deben ser subclases de DomainError."""
        excepciones = [
            UsuarioNoEncontradoError, UsuarioYaExisteError,
            UsuarioInactivoError, CredencialesInvalidasError,
            SaldoInsuficienteError, MontoInvalidoError,
            TransaccionInvalidaError, TokenInvalidoError,
        ]
        for exc in excepciones:
            assert issubclass(exc, DomainError), f"{exc.__name__} no hereda de DomainError"

    def test_34_domain_error_hereda_de_exception(self):
        """DomainError debe ser una excepción estándar de Python."""
        assert issubclass(DomainError, Exception)

    def test_35_excepcion_conserva_su_mensaje(self):
        """El mensaje de error debe ser recuperable desde la excepción."""
        mensaje = "Saldo insuficiente para la operación"
        with pytest.raises(SaldoInsuficienteError) as info:
            raise SaldoInsuficienteError(mensaje)
        assert mensaje in str(info.value)
