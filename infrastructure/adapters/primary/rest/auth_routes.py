# infrastructure/adapters/primary/rest/auth_routes.py
# Adaptador primario REST: traduce HTTP → casos de uso

from flask import Blueprint, request, jsonify

from application.use_cases.auth.registrar_usuario import RegistrarUsuarioUseCase, RegistrarUsuarioInput
from application.use_cases.auth.login_usuario import LoginUsuarioUseCase, LoginInput
from application.use_cases.auth.logout_usuario import LogoutUsuarioUseCase, RefreshTokenUseCase
from domain.exceptions import (
    UsuarioYaExisteError,
    CredencialesInvalidasError,
    UsuarioInactivoError,
    UsuarioNoEncontradoError,
)
from infrastructure.adapters.primary.rest.middlewares import require_access_token, require_refresh_token_middleware
from infrastructure.config.validators import validar_datos_registro, validar_numero_telefono, sanitizar_texto
import logging

logger = logging.getLogger(__name__)


def crear_auth_blueprint(
    registrar_uc: RegistrarUsuarioUseCase,
    login_uc: LoginUsuarioUseCase,
    logout_uc: LogoutUsuarioUseCase,
    refresh_uc: RefreshTokenUseCase,
) -> Blueprint:
    """
    Factory que recibe los casos de uso ya instanciados (DI manual).
    El Blueprint no crea dependencias; solo las usa.
    """

    bp = Blueprint('auth', __name__, url_prefix='/api/auth')

    @bp.route('/registro', methods=['POST'])
    def registro():
        data = request.get_json() or {}

        nombre = sanitizar_texto(data.get('nombre', ''))
        numero = sanitizar_texto(data.get('numeroTelefono', ''))
        email = sanitizar_texto(data.get('email', '')).lower()
        password = data.get('password', '')

        valido, error = validar_datos_registro(nombre, numero, email, password)
        if not valido:
            return jsonify({'error': error}), 400

        try:
            resultado = registrar_uc.ejecutar(RegistrarUsuarioInput(
                nombre=nombre,
                numero_telefono=numero,
                email=email,
                password=password,
                dispositivo=request.headers.get('User-Agent', '')[:200],
                ip=request.remote_addr or '',
            ))
        except UsuarioYaExisteError as e:
            return jsonify({'error': str(e)}), 409
        except Exception:
            logger.exception("Error en registro")
            return jsonify({'error': 'Error interno del servidor'}), 500

        return jsonify({
            'mensaje': 'Usuario registrado exitosamente',
            'accessToken': resultado.access_token,
            'refreshToken': resultado.refresh_token,
            'usuario': resultado.usuario,
        }), 201

    @bp.route('/login', methods=['POST'])
    def login():
        data = request.get_json() or {}

        numero = sanitizar_texto(data.get('numeroTelefono', ''))
        password = data.get('password', '')

        if not numero or not password:
            return jsonify({'error': 'Número de teléfono y contraseña son requeridos'}), 400

        valido, error = validar_numero_telefono(numero)
        if not valido:
            return jsonify({'error': error}), 400

        try:
            resultado = login_uc.ejecutar(LoginInput(
                numero_telefono=numero,
                password=password,
                dispositivo=request.headers.get('User-Agent', '')[:200],
                ip=request.remote_addr or '',
            ))
        except (CredencialesInvalidasError, UsuarioInactivoError) as e:
            status = 401 if isinstance(e, CredencialesInvalidasError) else 403
            return jsonify({'error': str(e)}), status
        except Exception:
            logger.exception("Error en login")
            return jsonify({'error': 'Error interno del servidor'}), 500

        return jsonify({
            'mensaje': 'Login exitoso',
            'accessToken': resultado.access_token,
            'refreshToken': resultado.refresh_token,
            'usuario': resultado.usuario,
        }), 200

    @bp.route('/refresh', methods=['POST'])
    @require_refresh_token_middleware
    def refresh():
        numero = request.user_data['numeroTelefono']
        try:
            nuevo_token = refresh_uc.ejecutar(numero)
        except (UsuarioNoEncontradoError, UsuarioInactivoError) as e:
            return jsonify({'error': str(e)}), 401
        except Exception:
            logger.exception("Error renovando token")
            return jsonify({'error': 'Error interno del servidor'}), 500

        return jsonify({
            'accessToken': nuevo_token,
            'mensaje': 'Token renovado exitosamente',
        }), 200

    @bp.route('/logout', methods=['POST'])
    @require_refresh_token_middleware
    def logout():
        numero = request.user_data['numeroTelefono']
        auth_header = request.headers.get('Authorization', '')
        refresh_token = auth_header.split(' ')[1] if len(auth_header.split()) == 2 else ''

        try:
            logout_uc.ejecutar(numero, refresh_token)
        except Exception:
            logger.exception("Error en logout")
            return jsonify({'error': 'Error interno del servidor'}), 500

        return jsonify({'mensaje': 'Sesión cerrada exitosamente'}), 200

    @bp.route('/verificar', methods=['GET'])
    @require_access_token
    def verificar():
        return jsonify({
            'valido': True,
            'numeroTelefono': request.user_data['numeroTelefono'],
            'nombre': request.user_data.get('nombre'),
        }), 200

    return bp
