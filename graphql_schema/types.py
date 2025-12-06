# graphql/types.py - Tipos GraphQL

import graphene
from graphene import ObjectType, String, Float, Int, Field, List, Enum


# ============= ENUMS =============

class TipoMovimiento(Enum):
    """Tipo de movimiento en el historial"""
    ENVIADO = 'ENVIADO'
    RECIBIDO = 'RECIBIDO'
    TODOS = 'TODOS'


class EstadoTransaccion(Enum):
    """Estado de una transacción"""
    EXITOSA = 'EXITOSA'
    FALLIDA = 'FALLIDA'
    PENDIENTE = 'PENDIENTE'


class Periodo(Enum):
    """Periodo para estadísticas"""
    HOY = 'HOY'
    SEMANA_ACTUAL = 'SEMANA_ACTUAL'
    MES_ACTUAL = 'MES_ACTUAL'
    TODO = 'TODO'


# ============= TYPES =============

class UsuarioType(ObjectType):
    """
    Tipo de dato Usuario para GraphQL
    """
    numero_telefono = String(required=True, description="Número de teléfono del usuario")
    nombre = String(required=True, description="Nombre completo del usuario")
    email = String(required=True, description="Email del usuario")
    saldo = Float(required=True, description="Saldo disponible en la cuenta")
    fecha_registro = String(required=True, description="Fecha de registro del usuario")
    biografia = String(description="Biografía del usuario")
    
    def resolve_biografia(root, info):
        """Resolver biografía del perfil"""
        perfil = root.get('perfil', {})
        return perfil.get('biografia', '')


class MovimientoType(ObjectType):
    """
    Tipo de dato Movimiento/Transacción para GraphQL
    """
    id = String(required=True, description="ID único de la transacción")
    tipo = Field(TipoMovimiento, required=True, description="Tipo de movimiento (ENVIADO/RECIBIDO)")
    numero_origen = String(required=True, description="Número del remitente")
    nombre_origen = String(required=True, description="Nombre del remitente")
    numero_destino = String(required=True, description="Número del destinatario")
    nombre_destino = String(required=True, description="Nombre del destinatario")
    monto = Float(required=True, description="Monto de la transacción")
    mensaje = String(description="Mensaje opcional de la transacción")
    fecha = String(required=True, description="Fecha y hora de la transacción")
    estado = Field(EstadoTransaccion, required=True, description="Estado de la transacción")
    
    def resolve_fecha(root, info):
        """Formatear fecha a string ISO"""
        fecha = root.get('fecha')
        if hasattr(fecha, 'isoformat'):
            return fecha.isoformat()
        return str(fecha)


class EstadisticasType(ObjectType):
    """
    Tipo de dato Estadísticas para GraphQL
    """
    total_enviado = Float(required=True, description="Total de dinero enviado")
    total_recibido = Float(required=True, description="Total de dinero recibido")
    cantidad_transacciones = Int(required=True, description="Cantidad total de transacciones")
    promedio_transaccion = Float(required=True, description="Promedio por transacción")
    periodo = String(required=True, description="Periodo de las estadísticas")
    balance = Float(required=True, description="Balance (recibido - enviado)")


class ResumenFinancieroType(ObjectType):
    """
    Tipo de dato para resumen financiero
    """
    saldo_actual = Float(required=True, description="Saldo actual del usuario")
    total_transacciones = Int(required=True, description="Total de transacciones realizadas")
    ultima_transaccion = Field(MovimientoType, description="Última transacción realizada")
    estadisticas_mes = Field(EstadisticasType, description="Estadísticas del mes actual")


class BuscarUsuarioResult(ObjectType):
    """
    Resultado de búsqueda de usuarios
    """
    numero_telefono = String(required=True)
    nombre = String(required=True)
    existe = graphene.Boolean(required=True, description="Si el usuario existe")


# Exportar tipos
__all__ = [
    'UsuarioType',
    'MovimientoType',
    'EstadisticasType',
    'ResumenFinancieroType',
    'BuscarUsuarioResult',
    'TipoMovimiento',
    'EstadoTransaccion',
    'Periodo'
]