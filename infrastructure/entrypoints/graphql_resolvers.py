# infrastructure/entrypoints/graphql_resolvers.py
# Adaptador de entrada GraphQL para NequiZ - Fase 4 (Puertos y Adaptadores)

import graphene
from graphene import ObjectType, String, Int, Float, Field, List, Boolean, Enum as GEnum
import logging

from application.use_cases.perfil.obtener_perfil import ObtenerPerfilUseCase
from application.use_cases.movimientos.obtener_movimientos import (
    ObtenerMovimientosUseCase, ObtenerMovimientosInput, ObtenerEstadisticasUseCase,
    ObtenerEstadisticasInput,
)
from application.use_cases.transferencias.enviar_dinero import ValidarDestinatarioUseCase
from domain.entities.transaccion import TipoMovimiento
from infrastructure.adapters.mongodb_repository import MongoUsuarioRepository, MongoTransaccionRepository

logger = logging.getLogger(__name__)


# ── GraphQL Types ────────────────────────────────────────────────────────────

class TipoMovimientoEnum(GEnum):
    class Meta:
        enum = TipoMovimiento


class PeriodoEnum(graphene.Enum):
    HOY = 'HOY'
    SEMANA_ACTUAL = 'SEMANA_ACTUAL'
    MES_ACTUAL = 'MES_ACTUAL'
    TODO = 'TODO'


class UsuarioType(ObjectType):
    numero_telefono = String()
    nombre = String()
    email = String()
    saldo = Float()
    fecha_registro = String()
    biografia = String()

    def resolve_biografia(root, info):
        perfil = root.get('perfil', {})
        return perfil.get('biografia', '')


class MovimientoType(ObjectType):
    id = String()
    tipo = String()
    numero_origen = String()
    nombre_origen = String()
    numero_destino = String()
    nombre_destino = String()
    monto = Float()
    mensaje = String()
    fecha = String()
    estado = String()


class EstadisticasType(ObjectType):
    total_enviado = Float()
    total_recibido = Float()
    cantidad_transacciones = Int()
    promedio_transaccion = Float()
    periodo = String()
    balance = Float()


class BuscarUsuarioResult(ObjectType):
    numero_telefono = String()
    nombre = String()
    existe = Boolean()


# ── Helpers ──────────────────────────────────────────────────────────────────

def _extraer_numero(info) -> str | None:
    """Extrae el número de teléfono del token JWT en el contexto GraphQL."""
    try:
        context = info.context
        headers = context.get('headers') if isinstance(context, dict) else None
        if headers is None:
            return None

        auth = headers.get('Authorization', '')
        partes = auth.split()
        if len(partes) != 2 or partes[0].lower() != 'bearer':
            return None

        from infrastructure.adapters.secondary.jwt.jwt_token_service import JwtTokenService
        token_service = JwtTokenService()
        payload = token_service.verificar_token(partes[1])
        if not payload or payload.get('tipo') != 'access':
            return None

        return payload.get('numeroTelefono')
    except Exception as e:
        logger.error(f"Error extrayendo número desde contexto GraphQL: {e}")
        return None


# ── Resolvers ─────────────────────────────────────────────────────────────────

class Query(ObjectType):
    """
    Fase 4: Los resolvers asumen el control de instanciar los repositorios 
    y pasarlos a los casos de uso, quitando esta responsabilidad de un Factory global.
    """

    mi_perfil = Field(UsuarioType)
    buscar_usuario = Field(
        BuscarUsuarioResult,
        numero_telefono=String(required=True),
    )
    mis_movimientos = List(
        MovimientoType,
        limite=Int(default_value=10),
        offset=Int(default_value=0),
        tipo=String(default_value='TODOS'),
        fecha_desde=String(),
        fecha_hasta=String(),
    )
    mis_estadisticas = Field(EstadisticasType, periodo=String(default_value='MES_ACTUAL'))
    ultimas_transacciones = List(MovimientoType, limite=Int(default_value=5))

    def resolve_mi_perfil(root, info):
        numero = _extraer_numero(info)
        if not numero:
            raise Exception("No autenticado. Token JWT requerido")
            
        usuario_repo = MongoUsuarioRepository()
        use_case = ObtenerPerfilUseCase(usuario_repo)
        return use_case.ejecutar(numero)

    def resolve_buscar_usuario(root, info, numero_telefono):
        if not _extraer_numero(info):
            raise Exception("No autenticado. Token JWT requerido")
            
        usuario_repo = MongoUsuarioRepository()
        use_case = ValidarDestinatarioUseCase(usuario_repo)
        resultado = use_case.ejecutar(numero_telefono)
        
        return {
            'existe': resultado.existe,
            'numero_telefono': resultado.numero_telefono,
            'nombre': resultado.nombre,
        }

    def resolve_mis_movimientos(
        root, info,
        limite=10, offset=0, tipo='TODOS',
        fecha_desde=None, fecha_hasta=None,
    ):
        numero = _extraer_numero(info)
        if not numero:
            raise Exception("No autenticado. Token JWT requerido")

        from datetime import datetime
        tipo_enum = TipoMovimiento(tipo) if tipo in TipoMovimiento._value2member_map_ else TipoMovimiento.TODOS
        fd = datetime.fromisoformat(fecha_desde) if fecha_desde else None
        fh = datetime.fromisoformat(fecha_hasta) if fecha_hasta else None

        transaccion_repo = MongoTransaccionRepository()
        use_case = ObtenerMovimientosUseCase(transaccion_repo)
        
        return use_case.ejecutar(ObtenerMovimientosInput(
            numero_telefono=numero,
            limite=limite,
            offset=offset,
            tipo=tipo_enum,
            fecha_desde=fd,
            fecha_hasta=fh,
        ))

    def resolve_mis_estadisticas(root, info, periodo='MES_ACTUAL'):
        numero = _extraer_numero(info)
        if not numero:
            raise Exception("No autenticado. Token JWT requerido")
            
        transaccion_repo = MongoTransaccionRepository()
        use_case = ObtenerEstadisticasUseCase(transaccion_repo)
        
        return use_case.ejecutar(
            ObtenerEstadisticasInput(numero_telefono=numero, periodo=periodo)
        )

    def resolve_ultimas_transacciones(root, info, limite=5):
        numero = _extraer_numero(info)
        if not numero:
            raise Exception("No autenticado. Token JWT requerido")
            
        transaccion_repo = MongoTransaccionRepository()
        use_case = ObtenerMovimientosUseCase(transaccion_repo)
        
        return use_case.ejecutar(ObtenerMovimientosInput(
            numero_telefono=numero,
            limite=min(limite, 20),
            tipo=TipoMovimiento.TODOS,
        ))
