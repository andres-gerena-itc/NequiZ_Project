# routes/perfil.py - Módulo de Perfil de Usuario

from flask import Blueprint, request, jsonify
from utils.db import usuarios_collection
from utils.jwt_handler import require_jwt, obtener_usuario_desde_token
from utils.validators import validar_nombre, sanitizar_texto
import logging

logger = logging.getLogger(__name__)

# Crear Blueprint
perfil_bp = Blueprint('perfil', __name__, url_prefix='/api/perfil')


@perfil_bp.route('/', methods=['GET'])
@require_jwt
def obtener_perfil():
    """
    Obtener información del perfil del usuario autenticado
    
    GET /api/perfil
    Headers:
        Authorization: Bearer <access_token>
    
    Response:
    {
        "nombre": "Juan Pérez",
        "numeroTelefono": "3001234567",
        "email": "juan@email.com",
        "saldo": 500000.0,
        "fechaRegistro": "2025-01-15T10:30:00",
        "perfil": {
            "foto": null,
            "biografia": "Usuario de NequiZ"
        }
    }
    """
    try:
        numero_telefono = obtener_usuario_desde_token()
        
        if not numero_telefono:
            return jsonify({'error': 'No autenticado'}), 401
        
        # Buscar usuario
        usuario = usuarios_collection.find_one(
            {'numeroTelefono': numero_telefono},
            {'passwordHash': 0, '_id': 0}  # Excluir password y _id
        )
        
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Formatear fechas
        if 'fechaRegistro' in usuario:
            usuario['fechaRegistro'] = usuario['fechaRegistro'].isoformat()
        
        return jsonify(usuario), 200
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo perfil: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500


@perfil_bp.route('/actualizar', methods=['PUT'])
@require_jwt
def actualizar_perfil():
    """
    Actualizar información del perfil
    
    PUT /api/perfil/actualizar
    Headers:
        Authorization: Bearer <access_token>
    Body:
    {
        "nombre": "Juan Pérez González",
        "biografia": "Mi nueva biografía"
    }
    
    Response:
    {
        "mensaje": "Perfil actualizado exitosamente",
        "perfil": {...}
    }
    """
    try:
        numero_telefono = obtener_usuario_desde_token()
        
        if not numero_telefono:
            return jsonify({'error': 'No autenticado'}), 401
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Datos no proporcionados'}), 400
        
        # Campos actualizables
        campos_actualizar = {}
        
        # Actualizar nombre
        if 'nombre' in data:
            nombre = sanitizar_texto(data['nombre'])
            valido, error = validar_nombre(nombre)
            
            if not valido:
                return jsonify({'error': error}), 400
            
            campos_actualizar['nombre'] = nombre
        
        # Actualizar biografía
        if 'biografia' in data:
            biografia = sanitizar_texto(data['biografia'])
            
            if len(biografia) > 500:
                return jsonify({'error': 'Biografía demasiado larga (máximo 500 caracteres)'}), 400
            
            campos_actualizar['perfil.biografia'] = biografia
        
        if not campos_actualizar:
            return jsonify({'error': 'No hay campos para actualizar'}), 400
        
        # Actualizar usuario
        result = usuarios_collection.update_one(
            {'numeroTelefono': numero_telefono},
            {'$set': campos_actualizar}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Obtener perfil actualizado
        usuario = usuarios_collection.find_one(
            {'numeroTelefono': numero_telefono},
            {'passwordHash': 0, '_id': 0}
        )
        
        if 'fechaRegistro' in usuario:
            usuario['fechaRegistro'] = usuario['fechaRegistro'].isoformat()
        
        logger.info(f"✅ Perfil actualizado: {numero_telefono}")
        
        return jsonify({
            'mensaje': 'Perfil actualizado exitosamente',
            'perfil': usuario
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error actualizando perfil: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500


@perfil_bp.route('/saldo', methods=['GET'])
@require_jwt
def obtener_saldo():
    """
    Obtener solo el saldo del usuario
    
    GET /api/perfil/saldo
    Headers:
        Authorization: Bearer <access_token>
    
    Response:
    {
        "saldo": 500000.0,
        "numeroTelefono": "3001234567"
    }
    """
    try:
        numero_telefono = obtener_usuario_desde_token()
        
        if not numero_telefono:
            return jsonify({'error': 'No autenticado'}), 401
        
        usuario = usuarios_collection.find_one(
            {'numeroTelefono': numero_telefono},
            {'saldo': 1, 'numeroTelefono': 1, '_id': 0}
        )
        
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        return jsonify(usuario), 200
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo saldo: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500


# Exportar Blueprint
__all__ = ['perfil_bp']