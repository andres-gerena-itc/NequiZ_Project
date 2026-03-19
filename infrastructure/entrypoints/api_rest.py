# infrastructure/entrypoints/api_rest.py
# Adaptador de entrada REST para NequiZ - Fase 4 (Puertos y Adaptadores)

from flask import Blueprint, request, jsonify
import logging

from application.use_cases.transferencias.enviar_dinero import EnviarDineroUseCase, EnviarDineroInput, ValidarDestinatarioUseCase
from application.use_cases.movimientos.obtener_movimientos import ObtenerMovimientosUseCase, ObtenerMovimientosInput
from application.use_cases.perfil.obtener_perfil import ObtenerSaldoUseCase, ActualizarPerfilUseCase, ActualizarPerfilInput
from infrastructure.adapters.mongodb_repository import MongoUsuarioRepository, MongoTransaccionRepository
from infrastructure.adapters.primary.rest.middlewares import require_access_token, obtener_numero_desde_request
from infrastructure.config.validators import sanitizar_texto, validar_datos_transferencia
from domain.entities.transaccion import TipoMovimiento
from domain.exceptions import (
    UsuarioNoEncontradoError, UsuarioInactivoError,
    SaldoInsuficienteError, TransaccionInvalidaError, MontoInvalidoError,
)

logger = logging.getLogger(__name__)

bp = Blueprint('api_rest', __name__, url_prefix='/api')

@bp.route('/transferencias/enviar', methods=['POST'])
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

    # Fase 4: Instanciamos los repositorios y el Caso de Uso (Inversión de Control delegada en el entrypoint)
    usuario_repo = MongoUsuarioRepository()
    transaccion_repo = MongoTransaccionRepository()
    use_case = EnviarDineroUseCase(usuario_repo, transaccion_repo)

    try:
        resultado = use_case.ejecutar(EnviarDineroInput(
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

@bp.route('/transferencias/ultimas', methods=['GET'])
@require_access_token
def ultimas():
    numero = obtener_numero_desde_request()
    limite = min(request.args.get('limite', 5, type=int), 50)

    # Fase 4: Instanciamos repositorios y Caso de Uso
    transaccion_repo = MongoTransaccionRepository()
    use_case = ObtenerMovimientosUseCase(transaccion_repo)

    movimientos = use_case.ejecutar(ObtenerMovimientosInput(
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

    return jsonify({
        'transferencias': transferencias,
        'total': len(transferencias),
        'limite': limite,
    }), 200

@bp.route('/transferencias/validar-destinatario', methods=['POST'])
@require_access_token
def validar_destinatario():
    data = request.get_json() or {}
    numero_destino = sanitizar_texto(data.get('numeroDestino', ''))

    if not numero_destino:
        return jsonify({'error': 'Número de destino es requerido'}), 400

    usuario_repo = MongoUsuarioRepository()
    use_case = ValidarDestinatarioUseCase(usuario_repo)
    resultado = use_case.ejecutar(numero_destino)

    if not resultado.existe:
        return jsonify({'existe': False, 'mensaje': 'Usuario no encontrado'}), 404

    return jsonify({
        'existe': True,
        'nombre': resultado.nombre,
        'numeroTelefono': resultado.numero_telefono,
    }), 200

@bp.route('/perfil/saldo', methods=['GET'])
@require_access_token
def obtener_saldo():
    """Nuevo endpoint 1: Obtener el saldo del usuario actual"""
    numero = obtener_numero_desde_request()
    
    usuario_repo = MongoUsuarioRepository()
    use_case = ObtenerSaldoUseCase(usuario_repo)
    
    try:
        resultado = use_case.ejecutar(numero)
        return jsonify(resultado), 200
    except UsuarioNoEncontradoError as e:
        return jsonify({'error': str(e)}), 404

@bp.route('/perfil/actualizar', methods=['PUT'])
@require_access_token
def actualizar_perfil():
    """Nuevo endpoint 2: Actualizar la biografía o nombre del perfil"""
    numero = obtener_numero_desde_request()
    data = request.get_json() or {}
    
    nombre = data.get('nombre')
    biografia = data.get('biografia')
    
    usuario_repo = MongoUsuarioRepository()
    use_case = ActualizarPerfilUseCase(usuario_repo)
    
    try:
        resultado = use_case.ejecutar(ActualizarPerfilInput(
            numero_telefono=numero,
            nombre=sanitizar_texto(nombre) if nombre else None,
            biografia=sanitizar_texto(biografia) if biografia else None
        ))
        return jsonify(resultado), 200
    except UsuarioNoEncontradoError as e:
        return jsonify({'error': str(e)}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
