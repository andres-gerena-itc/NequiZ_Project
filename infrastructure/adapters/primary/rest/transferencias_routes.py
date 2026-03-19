# infrastructure/adapters/primary/rest/transferencias_routes.py

from flask import Blueprint, request, jsonify

from application.use_cases.transferencias.enviar_dinero import EnviarDineroUseCase, EnviarDineroInput
from application.use_cases.transferencias.enviar_dinero import ValidarDestinatarioUseCase
from application.use_cases.movimientos.obtener_movimientos import (
    ObtenerMovimientosUseCase, ObtenerMovimientosInput,
)
from domain.entities.transaccion import TipoMovimiento
from domain.exceptions import (
    UsuarioNoEncontradoError, UsuarioInactivoError,
    SaldoInsuficienteError, TransaccionInvalidaError, MontoInvalidoError,
)
from infrastructure.adapters.primary.rest.middlewares import require_access_token, obtener_numero_desde_request
from infrastructure.config.validators import sanitizar_texto, validar_datos_transferencia
import logging

logger = logging.getLogger(__name__)


def crear_transferencias_blueprint(
    enviar_dinero_uc: EnviarDineroUseCase,
    validar_destinatario_uc: ValidarDestinatarioUseCase,
    obtener_movimientos_uc: ObtenerMovimientosUseCase,
) -> Blueprint:

    bp = Blueprint('transferencias', __name__, url_prefix='/api/transferencias')

    @bp.route('/enviar', methods=['POST'])
    @require_access_token
    def enviar():
        numero_origen = obtener_numero_desde_request()
        data = request.get_json() or {}

        numero_destino = sanitizar_texto(data.get('numeroDestino', ''))
        monto = data.get('monto')
        mensaje = sanitizar_texto(data.get('mensaje', ''))

        valido, error = validar_datos_transferencia(numero_destino, monto, mensaje)
        if not valido:
            return jsonify({'error': error}), 400

        try:
            resultado = enviar_dinero_uc.ejecutar(EnviarDineroInput(
                numero_origen=numero_origen,
                numero_destino=numero_destino,
                monto=float(monto),
                mensaje=mensaje,
            ))
        except (TransaccionInvalidaError, MontoInvalidoError) as e:
            return jsonify({'error': str(e)}), 400
        except SaldoInsuficienteError as e:
            return jsonify({'error': str(e)}), 400
        except UsuarioNoEncontradoError as e:
            return jsonify({'error': str(e)}), 404
        except UsuarioInactivoError as e:
            return jsonify({'error': str(e)}), 400
        except Exception:
            logger.exception("Error en transferencia")
            return jsonify({'error': 'Error interno del servidor'}), 500

        return jsonify({
            'mensaje': 'Transferencia exitosa',
            'transaccion': {
                'id': resultado.id_transaccion,
                'numeroOrigen': resultado.numero_origen,
                'numeroDestino': resultado.numero_destino,
                'nombreDestino': resultado.nombre_destino,
                'monto': resultado.monto,
                'mensaje': resultado.mensaje,
                'fecha': resultado.fecha,
                'nuevoSaldoOrigen': resultado.nuevo_saldo_origen,
                'estado': resultado.estado,
            },
        }), 200

    @bp.route('/validar-destinatario', methods=['POST'])
    @require_access_token
    def validar_destinatario():
        data = request.get_json() or {}
        numero_destino = sanitizar_texto(data.get('numeroDestino', ''))

        if not numero_destino:
            return jsonify({'error': 'Número de destino es requerido'}), 400

        resultado = validar_destinatario_uc.ejecutar(numero_destino)

        if not resultado.existe:
            return jsonify({'existe': False, 'mensaje': 'Usuario no encontrado'}), 404

        return jsonify({
            'existe': True,
            'nombre': resultado.nombre,
            'numeroTelefono': resultado.numero_telefono,
        }), 200

    @bp.route('/ultimas', methods=['GET'])
    @require_access_token
    def ultimas():
        numero = obtener_numero_desde_request()
        limite = min(request.args.get('limite', 5, type=int), 50)

        movimientos = obtener_movimientos_uc.ejecutar(ObtenerMovimientosInput(
            numero_telefono=numero,
            limite=limite,
            tipo=TipoMovimiento.TODOS,
        ))

        # Adaptar claves al formato camelCase que espera el frontend
        transferencias = []
        for m in movimientos:
            transferencias.append({
                'id': m['id'],
                'tipo': m['tipo'],
                'numeroOrigen': m['numero_origen'],
                'nombreOrigen': m['nombre_origen'],
                'numeroDestino': m['numero_destino'],
                'nombreDestino': m['nombre_destino'],
                'monto': m['monto'],
                'mensaje': m['mensaje'],
                'fecha': m['fecha'],
                'estado': m['estado'],
            })

        from domain.ports.repositories.transaccion_repository import TransaccionRepository
        return jsonify({
            'transferencias': transferencias,
            'total': len(transferencias),
            'limite': limite,
        }), 200

    return bp
