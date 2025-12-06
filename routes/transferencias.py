# routes/transferencias.py - Módulo de Transferencias P2P

from flask import Blueprint, request, jsonify
from utils.db import usuarios_collection, transacciones_collection
from utils.jwt_handler import require_jwt, obtener_usuario_desde_token
from utils.validators import validar_datos_transferencia, sanitizar_texto
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Crear Blueprint
transferencias_bp = Blueprint('transferencias', __name__, url_prefix='/api/transferencias')


@transferencias_bp.route('/enviar', methods=['POST'])
@require_jwt
def enviar_dinero():
    """
    Enviar dinero a otro usuario (Transferencia P2P)
    
    POST /api/transferencias/enviar
    Headers:
        Authorization: Bearer <access_token>
    Body:
    {
        "numeroDestino": "3009876543",
        "monto": 50000,
        "mensaje": "Pago de almuerzo"
    }
    
    Response:
    {
        "mensaje": "Transferencia exitosa",
        "transaccion": {
            "id": "...",
            "numeroOrigen": "3001234567",
            "numeroDestino": "3009876543",
            "nombreDestino": "María García",
            "monto": 50000,
            "mensaje": "Pago de almuerzo",
            "fecha": "2025-01-15T10:30:00",
            "nuevoSaldoOrigen": 450000
        }
    }
    """
    try:
        numero_origen = obtener_usuario_desde_token()
        
        if not numero_origen:
            return jsonify({'error': 'No autenticado'}), 401
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Datos no proporcionados'}), 400
        
        numero_destino = sanitizar_texto(data.get('numeroDestino', ''))
        monto = data.get('monto')
        mensaje = sanitizar_texto(data.get('mensaje', ''))
        
        # Validar datos
        valido, error = validar_datos_transferencia(numero_destino, monto, mensaje)
        if not valido:
            return jsonify({'error': error}), 400
        
        monto = float(monto)
        
        # Validar que no se envíe dinero a sí mismo
        if numero_origen == numero_destino:
            return jsonify({'error': 'No puedes enviarte dinero a ti mismo'}), 400
        
        # Buscar usuario origen
        usuario_origen = usuarios_collection.find_one({'numeroTelefono': numero_origen})
        
        if not usuario_origen:
            return jsonify({'error': 'Usuario origen no encontrado'}), 404
        
        # Verificar saldo suficiente
        if usuario_origen['saldo'] < monto:
            return jsonify({
                'error': 'Saldo insuficiente',
                'saldoActual': usuario_origen['saldo'],
                'montoRequerido': monto
            }), 400
        
        # Buscar usuario destino
        usuario_destino = usuarios_collection.find_one({'numeroTelefono': numero_destino})
        
        if not usuario_destino:
            return jsonify({'error': 'Usuario destino no encontrado'}), 404
        
        if not usuario_destino.get('activo', True):
            return jsonify({'error': 'Usuario destino inactivo'}), 400
        
        # Realizar transacción
        fecha_actual = datetime.utcnow()
        nuevo_saldo_origen = usuario_origen['saldo'] - monto
        nuevo_saldo_destino = usuario_destino['saldo'] + monto
        
        # Actualizar saldos
        usuarios_collection.update_one(
            {'numeroTelefono': numero_origen},
            {'$set': {'saldo': nuevo_saldo_origen}}
        )
        
        usuarios_collection.update_one(
            {'numeroTelefono': numero_destino},
            {'$set': {'saldo': nuevo_saldo_destino}}
        )
        
        # Registrar transacción
        transaccion = {
            'numeroOrigen': numero_origen,
            'nombreOrigen': usuario_origen['nombre'],
            'numeroDestino': numero_destino,
            'nombreDestino': usuario_destino['nombre'],
            'monto': monto,
            'mensaje': mensaje,
            'fecha': fecha_actual,
            'estado': 'EXITOSA',
            'tipo': 'TRANSFERENCIA_P2P'
        }
        
        result = transacciones_collection.insert_one(transaccion)
        transaccion['id'] = str(result.inserted_id)
        transaccion['_id'] = str(result.inserted_id)  # Por compatibilidad
        
        logger.info(f"✅ Transferencia exitosa: {numero_origen} → {numero_destino} ${monto:,.0f}")
        
        # Formatear respuesta
        return jsonify({
            'mensaje': 'Transferencia exitosa',
            'transaccion': {
                'id': str(result.inserted_id),
                'numeroOrigen': numero_origen,
                'numeroDestino': numero_destino,
                'nombreDestino': usuario_destino['nombre'],
                'monto': monto,
                'mensaje': mensaje,
                'fecha': fecha_actual.isoformat(),
                'nuevoSaldoOrigen': nuevo_saldo_origen,
                'estado': 'EXITOSA'
            }
        }), 200
        
    except ValueError as e:
        return jsonify({'error': f'Monto inválido: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"❌ Error en transferencia: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500


@transferencias_bp.route('/validar-destinatario', methods=['POST'])
@require_jwt
def validar_destinatario():
    """
    Validar que un número de destino existe (para el frontend)
    
    POST /api/transferencias/validar-destinatario
    Headers:
        Authorization: Bearer <access_token>
    Body:
    {
        "numeroDestino": "3009876543"
    }
    
    Response:
    {
        "existe": true,
        "nombre": "María García",
        "numeroTelefono": "3009876543"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Datos no proporcionados'}), 400
        
        numero_destino = sanitizar_texto(data.get('numeroDestino', ''))
        
        if not numero_destino:
            return jsonify({'error': 'Número de destino es requerido'}), 400
        
        # Buscar usuario
        usuario = usuarios_collection.find_one(
            {'numeroTelefono': numero_destino},
            {'nombre': 1, 'numeroTelefono': 1, 'activo': 1, '_id': 0}
        )
        
        if not usuario:
            return jsonify({
                'existe': False,
                'mensaje': 'Usuario no encontrado'
            }), 404
        
        if not usuario.get('activo', True):
            return jsonify({
                'existe': False,
                'mensaje': 'Usuario inactivo'
            }), 400
        
        return jsonify({
            'existe': True,
            'nombre': usuario['nombre'],
            'numeroTelefono': usuario['numeroTelefono']
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error validando destinatario: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500


@transferencias_bp.route('/ultimas', methods=['GET'])
@require_jwt
def obtener_ultimas_transferencias():
    """
    Obtener las últimas transferencias del usuario
    
    GET /api/transferencias/ultimas?limite=5
    Headers:
        Authorization: Bearer <access_token>
    
    Response:
    {
        "transferencias": [
            {
                "id": "...",
                "tipo": "ENVIADO",
                "numeroOrigen": "3001234567",
                "numeroDestino": "3009876543",
                "nombreDestino": "María García",
                "monto": 50000,
                "fecha": "2025-01-15T10:30:00"
            }
        ],
        "total": 10
    }
    """
    try:
        numero_telefono = obtener_usuario_desde_token()
        
        if not numero_telefono:
            return jsonify({'error': 'No autenticado'}), 401
        
        # Obtener límite de query params
        limite = request.args.get('limite', 5, type=int)
        limite = min(limite, 50)  # Máximo 50
        
        # Buscar transacciones donde el usuario es origen o destino
        transacciones = list(transacciones_collection.find(
            {
                '$or': [
                    {'numeroOrigen': numero_telefono},
                    {'numeroDestino': numero_telefono}
                ]
            }
        ).sort('fecha', -1).limit(limite))
        
        # Formatear transacciones
        resultado = []
        for trans in transacciones:
            tipo = 'ENVIADO' if trans['numeroOrigen'] == numero_telefono else 'RECIBIDO'
            
            resultado.append({
                'id': str(trans['_id']),
                'tipo': tipo,
                'numeroOrigen': trans['numeroOrigen'],
                'nombreOrigen': trans.get('nombreOrigen', ''),
                'numeroDestino': trans['numeroDestino'],
                'nombreDestino': trans.get('nombreDestino', ''),
                'monto': trans['monto'],
                'mensaje': trans.get('mensaje', ''),
                'fecha': trans['fecha'].isoformat(),
                'estado': trans.get('estado', 'EXITOSA')
            })
        
        # Contar total de transacciones
        total = transacciones_collection.count_documents({
            '$or': [
                {'numeroOrigen': numero_telefono},
                {'numeroDestino': numero_telefono}
            ]
        })
        
        return jsonify({
            'transferencias': resultado,
            'total': total,
            'limite': limite
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo transferencias: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500


# Exportar Blueprint
__all__ = ['transferencias_bp']