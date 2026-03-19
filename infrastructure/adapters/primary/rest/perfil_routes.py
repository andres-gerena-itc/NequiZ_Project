# infrastructure/adapters/primary/rest/perfil_routes.py

from flask import Blueprint, request, jsonify

from application.use_cases.perfil.obtener_perfil import (
    ObtenerPerfilUseCase, ActualizarPerfilUseCase, ObtenerSaldoUseCase,
    ActualizarPerfilInput,
)
from domain.exceptions import UsuarioNoEncontradoError
from infrastructure.adapters.primary.rest.middlewares import require_access_token, obtener_numero_desde_request
from infrastructure.config.validators import sanitizar_texto
import logging

logger = logging.getLogger(__name__)


def crear_perfil_blueprint(
    obtener_perfil_uc: ObtenerPerfilUseCase,
    actualizar_perfil_uc: ActualizarPerfilUseCase,
    obtener_saldo_uc: ObtenerSaldoUseCase,
) -> Blueprint:

    bp = Blueprint('perfil', __name__, url_prefix='/api/perfil')

    @bp.route('/', methods=['GET'])
    @require_access_token
    def obtener_perfil():
        numero = obtener_numero_desde_request()
        try:
            perfil = obtener_perfil_uc.ejecutar(numero)
        except UsuarioNoEncontradoError as e:
            return jsonify({'error': str(e)}), 404
        except Exception:
            logger.exception("Error obteniendo perfil")
            return jsonify({'error': 'Error interno del servidor'}), 500
        return jsonify(perfil), 200

    @bp.route('/actualizar', methods=['PUT'])
    @require_access_token
    def actualizar_perfil():
        numero = obtener_numero_desde_request()
        data = request.get_json() or {}

        campos = ActualizarPerfilInput(numero_telefono=numero)

        if 'nombre' in data:
            campos.nombre = sanitizar_texto(data['nombre'])
        if 'biografia' in data:
            campos.biografia = sanitizar_texto(data['biografia'])

        try:
            perfil_actualizado = actualizar_perfil_uc.ejecutar(campos)
        except UsuarioNoEncontradoError as e:
            return jsonify({'error': str(e)}), 404
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception:
            logger.exception("Error actualizando perfil")
            return jsonify({'error': 'Error interno del servidor'}), 500

        return jsonify({
            'mensaje': 'Perfil actualizado exitosamente',
            'perfil': perfil_actualizado,
        }), 200

    @bp.route('/saldo', methods=['GET'])
    @require_access_token
    def obtener_saldo():
        numero = obtener_numero_desde_request()
        try:
            saldo = obtener_saldo_uc.ejecutar(numero)
        except UsuarioNoEncontradoError as e:
            return jsonify({'error': str(e)}), 404
        except Exception:
            logger.exception("Error obteniendo saldo")
            return jsonify({'error': 'Error interno del servidor'}), 500
        return jsonify(saldo), 200

    return bp
