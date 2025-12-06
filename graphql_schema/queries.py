# graphql_schema/queries.py - Resolvers de Queries GraphQL

import graphene
from graphene import ObjectType, String, Int, Field, List
from graphql_schema.types import MovimientoType, UsuarioType, EstadisticasType, ResumenFinancieroType, BuscarUsuarioResult, TipoMovimiento, Periodo
from utils.db import usuarios_collection, transacciones_collection
from utils.jwt_handler import verificar_token
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def obtener_usuario_desde_contexto(info):
    """
    Obtener usuario autenticado desde el contexto GraphQL
    
    Args:
        info: Contexto de GraphQL
        
    Returns:
        str: Número de teléfono del usuario o None
    """
    try:
        # Obtener contexto (es un dict)
        context = info.context
        
        logger.info(f"🔍 Contexto type: {type(context)}")
        
        # El contexto es un diccionario, acceder con ['headers']
        if isinstance(context, dict):
            # Opción 1: Si el contexto tiene 'headers' directamente
            if 'headers' in context:
                headers = context['headers']
                logger.info(f"✅ Headers encontrados en context['headers']")
            # Opción 2: Si el contexto tiene 'request' con headers
            elif 'request' in context:
                headers = context['request'].headers
                logger.info(f"✅ Headers encontrados en context['request'].headers")
            else:
                logger.error(f"❌ No se encontró 'headers' ni 'request' en contexto")
                logger.error(f"❌ Keys disponibles: {list(context.keys())}")
                return None
            
            # Obtener header Authorization
            auth_header = headers.get('Authorization', '')
            
            if not auth_header:
                logger.warning("❌ Header Authorization no encontrado")
                return None
            
            logger.info(f"🔑 Authorization header: {auth_header[:50]}...")
            
            # Extraer token
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                logger.warning(f"❌ Formato de header incorrecto: {auth_header[:30]}")
                return None
            
            token = parts[1]
            logger.info(f"✅ Token extraído: {token[:20]}...")
            
            # Verificar token
            payload = verificar_token(token)
            
            if not payload:
                logger.warning("❌ Token inválido o expirado")
                return None
                
            if payload.get('tipo') != 'access':
                logger.warning(f"❌ Tipo de token incorrecto: {payload.get('tipo')}")
                return None
            
            numero = payload.get('numeroTelefono')
            logger.info(f"✅ Usuario autenticado: {numero}")
            return numero
        
        else:
            logger.error(f"❌ Contexto no es dict: {type(context)}")
            return None
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo usuario desde contexto: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


class Query(ObjectType):
    """
    Queries principales de GraphQL para NequiZ
    """
    
    # ============= PERFIL DE USUARIO =============
    
    mi_perfil = Field(
        UsuarioType,
        description="Obtener perfil completo del usuario autenticado"
    )
    
    def resolve_mi_perfil(root, info):
        """
        Resolver query: miPerfil
        Retorna el perfil del usuario autenticado
        """
        numero_telefono = obtener_usuario_desde_contexto(info)
        
        if not numero_telefono:
            raise Exception("No autenticado. Token JWT requerido")
        
        usuario = usuarios_collection.find_one(
            {'numeroTelefono': numero_telefono},
            {'passwordHash': 0, '_id': 0}
        )
        
        if not usuario:
            raise Exception("Usuario no encontrado")
        
        # Formatear fecha
        if 'fechaRegistro' in usuario and hasattr(usuario['fechaRegistro'], 'isoformat'):
            usuario['fechaRegistro'] = usuario['fechaRegistro'].isoformat()
        
        # Mapear campos para GraphQL
        return {
            'numero_telefono': usuario['numeroTelefono'],
            'nombre': usuario['nombre'],
            'email': usuario['email'],
            'saldo': usuario['saldo'],
            'fecha_registro': usuario.get('fechaRegistro', ''),
            'perfil': usuario.get('perfil', {})
        }
    
    # ============= BUSCAR USUARIO =============
    
    buscar_usuario = Field(
        BuscarUsuarioResult,
        numero_telefono=String(required=True, description="Número de teléfono a buscar"),
        description="Buscar usuario por número de teléfono (para validar destinatario)"
    )
    
    def resolve_buscar_usuario(root, info, numero_telefono):
        """
        Resolver query: buscarUsuario
        Busca si existe un usuario con el número dado
        """
        # Verificar autenticación
        usuario_autenticado = obtener_usuario_desde_contexto(info)
        if not usuario_autenticado:
            raise Exception("No autenticado. Token JWT requerido")
        
        usuario = usuarios_collection.find_one(
            {'numeroTelefono': numero_telefono, 'activo': True},
            {'nombre': 1, 'numeroTelefono': 1, '_id': 0}
        )
        
        if not usuario:
            return {
                'existe': False,
                'numero_telefono': numero_telefono,
                'nombre': ''
            }
        
        return {
            'existe': True,
            'numero_telefono': usuario['numeroTelefono'],
            'nombre': usuario['nombre']
        }
    
    # ============= MOVIMIENTOS/HISTORIAL =============
    
    mis_movimientos = List(
        MovimientoType,
        limite=Int(default_value=10, description="Cantidad máxima de movimientos a retornar"),
        offset=Int(default_value=0, description="Offset para paginación"),
        tipo=TipoMovimiento(default_value='TODOS', description="Filtrar por tipo de movimiento"),
        fecha_desde=String(description="Filtrar desde fecha (ISO format)"),
        fecha_hasta=String(description="Filtrar hasta fecha (ISO format)"),
        description="Obtener historial de movimientos del usuario autenticado"
    )
    
    def resolve_mis_movimientos(root, info, limite=10, offset=0, tipo='TODOS', fecha_desde=None, fecha_hasta=None):
        """
        Resolver query: misMovimientos
        Retorna el historial de transacciones del usuario
        """
        numero_telefono = obtener_usuario_desde_contexto(info)
        
        if not numero_telefono:
            raise Exception("No autenticado. Token JWT requerido")
        
        # Limitar máximo
        limite = min(limite, 100)
        
        # Construir filtro base
        filtro = {}
        
        # Filtrar por tipo
        if tipo == 'ENVIADO':
            filtro['numeroOrigen'] = numero_telefono
        elif tipo == 'RECIBIDO':
            filtro['numeroDestino'] = numero_telefono
        else:  # TODOS
            filtro['$or'] = [
                {'numeroOrigen': numero_telefono},
                {'numeroDestino': numero_telefono}
            ]
        
        # Filtrar por fechas
        if fecha_desde or fecha_hasta:
            filtro['fecha'] = {}
            
            if fecha_desde:
                try:
                    fecha_desde_dt = datetime.fromisoformat(fecha_desde)
                    filtro['fecha']['$gte'] = fecha_desde_dt
                except:
                    pass
            
            if fecha_hasta:
                try:
                    fecha_hasta_dt = datetime.fromisoformat(fecha_hasta)
                    filtro['fecha']['$lte'] = fecha_hasta_dt
                except:
                    pass
        
        # Buscar transacciones
        transacciones = list(
            transacciones_collection
            .find(filtro)
            .sort('fecha', -1)
            .skip(offset)
            .limit(limite)
        )
        
        # Formatear resultado
        resultado = []
        for trans in transacciones:
            tipo_mov = 'ENVIADO' if trans['numeroOrigen'] == numero_telefono else 'RECIBIDO'
            
            resultado.append({
                'id': str(trans['_id']),
                'tipo': tipo_mov,
                'numero_origen': trans['numeroOrigen'],
                'nombre_origen': trans.get('nombreOrigen', ''),
                'numero_destino': trans['numeroDestino'],
                'nombre_destino': trans.get('nombreDestino', ''),
                'monto': trans['monto'],
                'mensaje': trans.get('mensaje', ''),
                'fecha': trans['fecha'],
                'estado': trans.get('estado', 'EXITOSA')
            })
        
        return resultado
    
    # ============= ESTADÍSTICAS =============
    
    mis_estadisticas = Field(
        EstadisticasType,
        periodo=Periodo(default_value='MES_ACTUAL', description="Periodo para las estadísticas"),
        description="Obtener estadísticas financieras del usuario"
    )
    
    def resolve_mis_estadisticas(root, info, periodo='MES_ACTUAL'):
        """
        Resolver query: misEstadisticas
        Calcula estadísticas financieras del usuario
        """
        numero_telefono = obtener_usuario_desde_contexto(info)
        
        if not numero_telefono:
            raise Exception("No autenticado. Token JWT requerido")
        
        # Calcular rango de fechas según periodo
        ahora = datetime.utcnow()
        fecha_desde = None
        
        if periodo == 'HOY':
            fecha_desde = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
        elif periodo == 'SEMANA_ACTUAL':
            fecha_desde = ahora - timedelta(days=ahora.weekday())
            fecha_desde = fecha_desde.replace(hour=0, minute=0, second=0, microsecond=0)
        elif periodo == 'MES_ACTUAL':
            fecha_desde = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Si es 'TODO', fecha_desde = None (todas las transacciones)
        
        # Filtro base
        filtro_enviado = {'numeroOrigen': numero_telefono}
        filtro_recibido = {'numeroDestino': numero_telefono}
        
        if fecha_desde:
            filtro_enviado['fecha'] = {'$gte': fecha_desde}
            filtro_recibido['fecha'] = {'$gte': fecha_desde}
        
        # Calcular total enviado
        pipeline_enviado = [
            {'$match': filtro_enviado},
            {'$group': {
                '_id': None,
                'total': {'$sum': '$monto'},
                'count': {'$sum': 1}
            }}
        ]
        
        resultado_enviado = list(transacciones_collection.aggregate(pipeline_enviado))
        total_enviado = resultado_enviado[0]['total'] if resultado_enviado else 0
        count_enviado = resultado_enviado[0]['count'] if resultado_enviado else 0
        
        # Calcular total recibido
        pipeline_recibido = [
            {'$match': filtro_recibido},
            {'$group': {
                '_id': None,
                'total': {'$sum': '$monto'},
                'count': {'$sum': 1}
            }}
        ]
        
        resultado_recibido = list(transacciones_collection.aggregate(pipeline_recibido))
        total_recibido = resultado_recibido[0]['total'] if resultado_recibido else 0
        count_recibido = resultado_recibido[0]['count'] if resultado_recibido else 0
        
        # Calcular promedios y balance
        cantidad_total = count_enviado + count_recibido
        promedio = (total_enviado + total_recibido) / cantidad_total if cantidad_total > 0 else 0
        balance = total_recibido - total_enviado
        
        return {
            'total_enviado': total_enviado,
            'total_recibido': total_recibido,
            'cantidad_transacciones': cantidad_total,
            'promedio_transaccion': promedio,
            'periodo': periodo,
            'balance': balance
        }
    
    # ============= ÚLTIMAS TRANSACCIONES =============
    
    ultimas_transacciones = List(
        MovimientoType,
        limite=Int(default_value=5, description="Cantidad de transacciones a retornar"),
        description="Obtener las últimas transacciones del usuario (para dashboard)"
    )
    
    def resolve_ultimas_transacciones(root, info, limite=5):
        """
        Resolver query: ultimasTransacciones
        Retorna las últimas N transacciones del usuario
        """
        numero_telefono = obtener_usuario_desde_contexto(info)
        
        if not numero_telefono:
            raise Exception("No autenticado. Token JWT requerido")
        
        # Limitar máximo a 20
        limite = min(limite, 20)
        
        transacciones = list(
            transacciones_collection.find({
                '$or': [
                    {'numeroOrigen': numero_telefono},
                    {'numeroDestino': numero_telefono}
                ]
            })
            .sort('fecha', -1)
            .limit(limite)
        )
        
        resultado = []
        for trans in transacciones:
            tipo_mov = 'ENVIADO' if trans['numeroOrigen'] == numero_telefono else 'RECIBIDO'
            
            resultado.append({
                'id': str(trans['_id']),
                'tipo': tipo_mov,
                'numero_origen': trans['numeroOrigen'],
                'nombre_origen': trans.get('nombreOrigen', ''),
                'numero_destino': trans['numeroDestino'],
                'nombre_destino': trans.get('nombreDestino', ''),
                'monto': trans['monto'],
                'mensaje': trans.get('mensaje', ''),
                'fecha': trans['fecha'],
                'estado': trans.get('estado', 'EXITOSA')
            })
        
        return resultado


# Exportar Query
__all__ = ['Query']