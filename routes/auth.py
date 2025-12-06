# routes/auth.py - Módulo de Autenticación REST

from flask import Blueprint, request, jsonify
from utils.db import usuarios_collection, sesiones_collection
from utils.jwt_handler import (
    generar_access_token, 
    generar_refresh_token,
    require_refresh_token,
    obtener_usuario_desde_token
)
from utils.validators import (
    validar_datos_registro,
    validar_numero_telefono,
    validar_password,
    sanitizar_texto
)
from config import Config
from datetime import datetime
import bcrypt
import logging

logger = logging.getLogger(__name__)

# Crear Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/registro', methods=['POST'])
def registro():
    """
    Registrar nuevo usuario
    
    POST /api/auth/registro
    {
        "nombre": "Juan Pérez",
        "numeroTelefono": "3001234567",
        "email": "juan@email.com",
        "password": "password123"
    }
    
    Response:
    {
        "mensaje": "Usuario registrado exitosamente",
        "accessToken": "eyJhbGc...",
        "refreshToken": "eyJhbGc...",
        "usuario": {
            "nombre": "Juan Pérez",
            "numeroTelefono": "3001234567",
            "email": "juan@email.com",
            "saldo": 100000.0
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Datos no proporcionados'}), 400
        
        # Extraer y sanitizar datos
        nombre = sanitizar_texto(data.get('nombre', ''))
        numero_telefono = sanitizar_texto(data.get('numeroTelefono', ''))
        email = sanitizar_texto(data.get('email', '')).lower()
        password = data.get('password', '')
        
        # Validar datos
        valido, error = validar_datos_registro(nombre, numero_telefono, email, password)
        if not valido:
            return jsonify({'error': error}), 400
        
        # Verificar que el número no exista
        if usuarios_collection.find_one({'numeroTelefono': numero_telefono}):
            return jsonify({'error': 'Este número de teléfono ya está registrado'}), 409
        
        # Verificar que el email no exista
        if usuarios_collection.find_one({'email': email}):
            return jsonify({'error': 'Este email ya está registrado'}), 409
        
        # Hash de la contraseña
        password_hash = bcrypt.hashpw(
            password.encode('utf-8'), 
            bcrypt.gensalt(Config.BCRYPT_LOG_ROUNDS)
        ).decode('utf-8')
        
        # Crear usuario
        nuevo_usuario = {
            'nombre': nombre,
            'numeroTelefono': numero_telefono,
            'email': email,
            'passwordHash': password_hash,
            'saldo': Config.SALDO_INICIAL,
            'fechaRegistro': datetime.utcnow(),
            'activo': True,
            'perfil': {
                'foto': None,
                'biografia': ''
            }
        }
        
        result = usuarios_collection.insert_one(nuevo_usuario)
        logger.info(f"✅ Usuario registrado: {nombre} ({numero_telefono})")
        
        # Generar tokens
        access_token = generar_access_token(numero_telefono, nombre)
        refresh_token = generar_refresh_token(numero_telefono)
        
        # Guardar refresh token en sesiones
        sesion = {
            'numeroTelefono': numero_telefono,
            'refreshToken': refresh_token,
            'fechaCreacion': datetime.utcnow(),
            'fechaExpiracion': datetime.utcnow() + Config.JWT_REFRESH_TOKEN_EXPIRES,
            'dispositivo': request.headers.get('User-Agent', 'Desconocido')[:200],
            'ip': request.remote_addr
        }
        sesiones_collection.insert_one(sesion)
        
        return jsonify({
            'mensaje': 'Usuario registrado exitosamente',
            'accessToken': access_token,
            'refreshToken': refresh_token,
            'usuario': {
                'nombre': nombre,
                'numeroTelefono': numero_telefono,
                'email': email,
                'saldo': Config.SALDO_INICIAL
            }
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Error en registro: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Iniciar sesión
    
    POST /api/auth/login
    {
        "numeroTelefono": "3001234567",
        "password": "password123"
    }
    
    Response:
    {
        "mensaje": "Login exitoso",
        "accessToken": "eyJhbGc...",
        "refreshToken": "eyJhbGc...",
        "usuario": {
            "nombre": "Juan Pérez",
            "numeroTelefono": "3001234567",
            "email": "juan@email.com",
            "saldo": 500000.0
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Datos no proporcionados'}), 400
        
        numero_telefono = sanitizar_texto(data.get('numeroTelefono', ''))
        password = data.get('password', '')
        
        # Validar datos básicos
        if not numero_telefono or not password:
            return jsonify({'error': 'Número de teléfono y contraseña son requeridos'}), 400
        
        # Validar formato de número
        valido, error = validar_numero_telefono(numero_telefono)
        if not valido:
            return jsonify({'error': error}), 400
        
        # Buscar usuario
        usuario = usuarios_collection.find_one({'numeroTelefono': numero_telefono})
        
        if not usuario:
            return jsonify({'error': 'Credenciales incorrectas'}), 401
        
        # Verificar que esté activo
        if not usuario.get('activo', True):
            return jsonify({'error': 'Usuario inactivo. Contacta a soporte'}), 403
        
        # Verificar contraseña
        if not bcrypt.checkpw(password.encode('utf-8'), usuario['passwordHash'].encode('utf-8')):
            return jsonify({'error': 'Credenciales incorrectas'}), 401
        
        logger.info(f"✅ Login exitoso: {usuario['nombre']} ({numero_telefono})")
        
        # Generar tokens
        access_token = generar_access_token(numero_telefono, usuario['nombre'])
        refresh_token = generar_refresh_token(numero_telefono)
        
        # Guardar refresh token en sesiones
        sesion = {
            'numeroTelefono': numero_telefono,
            'refreshToken': refresh_token,
            'fechaCreacion': datetime.utcnow(),
            'fechaExpiracion': datetime.utcnow() + Config.JWT_REFRESH_TOKEN_EXPIRES,
            'dispositivo': request.headers.get('User-Agent', 'Desconocido')[:200],
            'ip': request.remote_addr
        }
        sesiones_collection.insert_one(sesion)
        
        return jsonify({
            'mensaje': 'Login exitoso',
            'accessToken': access_token,
            'refreshToken': refresh_token,
            'usuario': {
                'nombre': usuario['nombre'],
                'numeroTelefono': usuario['numeroTelefono'],
                'email': usuario['email'],
                'saldo': usuario['saldo']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error en login: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500


@auth_bp.route('/refresh', methods=['POST'])
@require_refresh_token
def refresh():
    """
    Renovar access token usando refresh token
    
    POST /api/auth/refresh
    Headers:
        Authorization: Bearer <refresh_token>
    
    Response:
    {
        "accessToken": "eyJhbGc...",
        "mensaje": "Token renovado exitosamente"
    }
    """
    try:
        numero_telefono = obtener_usuario_desde_token()
        
        if not numero_telefono:
            return jsonify({'error': 'Token inválido'}), 401
        
        # Buscar usuario
        usuario = usuarios_collection.find_one({'numeroTelefono': numero_telefono})
        
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        if not usuario.get('activo', True):
            return jsonify({'error': 'Usuario inactivo'}), 403
        
        # Generar nuevo access token
        access_token = generar_access_token(numero_telefono, usuario['nombre'])
        
        logger.info(f"🔄 Token renovado: {numero_telefono}")
        
        return jsonify({
            'accessToken': access_token,
            'mensaje': 'Token renovado exitosamente'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error renovando token: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500


@auth_bp.route('/logout', methods=['POST'])
@require_refresh_token
def logout():
    """
    Cerrar sesión (invalidar refresh token)
    
    POST /api/auth/logout
    Headers:
        Authorization: Bearer <refresh_token>
    
    Response:
    {
        "mensaje": "Sesión cerrada exitosamente"
    }
    """
    try:
        numero_telefono = obtener_usuario_desde_token()
        
        if not numero_telefono:
            return jsonify({'error': 'Token inválido'}), 401
        
        # Eliminar refresh token de sesiones
        # En producción, se debería mantener una lista negra de tokens
        refresh_token = request.headers.get('Authorization', '').split(' ')[1]
        
        result = sesiones_collection.delete_one({
            'numeroTelefono': numero_telefono,
            'refreshToken': refresh_token
        })
        
        logger.info(f"👋 Logout: {numero_telefono}")
        
        return jsonify({
            'mensaje': 'Sesión cerrada exitosamente'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error en logout: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500


@auth_bp.route('/verificar', methods=['GET'])
def verificar_token_endpoint():
    """
    Verificar si un token es válido
    
    GET /api/auth/verificar
    Headers:
        Authorization: Bearer <access_token>
    
    Response:
    {
        "valido": true,
        "numeroTelefono": "3001234567",
        "nombre": "Juan Pérez"
    }
    """
    from utils.jwt_handler import extraer_token_de_header, verificar_token
    
    try:
        token = extraer_token_de_header()
        
        if not token:
            return jsonify({'valido': False, 'error': 'Token no proporcionado'}), 401
        
        payload = verificar_token(token)
        
        if not payload:
            return jsonify({'valido': False, 'error': 'Token inválido o expirado'}), 401
        
        return jsonify({
            'valido': True,
            'numeroTelefono': payload.get('numeroTelefono'),
            'nombre': payload.get('nombre'),
            'tipo': payload.get('tipo')
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error verificando token: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500


# Exportar Blueprint
__all__ = ['auth_bp']