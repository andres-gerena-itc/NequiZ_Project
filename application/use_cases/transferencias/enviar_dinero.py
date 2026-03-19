# application/use_cases/transferencias/enviar_dinero.py

from dataclasses import dataclass
from datetime import datetime
from typing import Dict

from domain.entities.transaccion import Transaccion
from domain.exceptions import (
    UsuarioNoEncontradoError,
    UsuarioInactivoError,
    TransaccionInvalidaError,
)
from domain.ports.repositories.usuario_repository import UsuarioRepository
from domain.ports.repositories.transaccion_repository import TransaccionRepository


@dataclass
class EnviarDineroInput:
    numero_origen: str
    numero_destino: str
    monto: float
    mensaje: str = ''


@dataclass
class EnviarDineroOutput:
    id_transaccion: str
    numero_origen: str
    numero_destino: str
    nombre_destino: str
    monto: float
    mensaje: str
    fecha: str
    nuevo_saldo_origen: float
    estado: str


class EnviarDineroUseCase:
    """
    Caso de uso: transferencia P2P entre dos usuarios.
    La lógica de negocio (débito/crédito, validaciones) vive en las entidades.
    """

    def __init__(
        self,
        usuario_repo: UsuarioRepository,
        transaccion_repo: TransaccionRepository,
    ):
        self._usuario_repo = usuario_repo
        self._transaccion_repo = transaccion_repo

    def ejecutar(self, datos: EnviarDineroInput) -> EnviarDineroOutput:
        if datos.numero_origen == datos.numero_destino:
            raise TransaccionInvalidaError("No puedes enviarte dinero a ti mismo")

        # Cargar entidades
        origen = self._usuario_repo.buscar_por_telefono(datos.numero_origen)
        if not origen:
            raise UsuarioNoEncontradoError("Usuario origen no encontrado")

        destino = self._usuario_repo.buscar_por_telefono(datos.numero_destino)
        if not destino:
            raise UsuarioNoEncontradoError("Usuario destino no encontrado")

        if not destino.activo:
            raise UsuarioInactivoError("Usuario destino inactivo")

        # Reglas de negocio en las entidades (lanza SaldoInsuficienteError si aplica)
        origen.debitar(datos.monto)
        destino.acreditar(datos.monto)

        # Persistir cambios de saldo
        self._usuario_repo.actualizar(origen)
        self._usuario_repo.actualizar(destino)

        # Crear y persistir transacción
        transaccion = Transaccion(
            numero_origen=origen.numero_telefono,
            nombre_origen=origen.nombre,
            numero_destino=destino.numero_telefono,
            nombre_destino=destino.nombre,
            monto=datos.monto,
            fecha=datetime.utcnow(),
            mensaje=datos.mensaje,
        )
        id_generado = self._transaccion_repo.guardar(transaccion)

        return EnviarDineroOutput(
            id_transaccion=id_generado,
            numero_origen=origen.numero_telefono,
            numero_destino=destino.numero_telefono,
            nombre_destino=destino.nombre,
            monto=datos.monto,
            mensaje=datos.mensaje,
            fecha=transaccion.fecha.isoformat(),
            nuevo_saldo_origen=origen.saldo,
            estado=transaccion.estado.value,
        )


# ─────────────────────────────────────────────────────────────────────────────


# application/use_cases/transferencias/validar_destinatario.py

from dataclasses import dataclass
from domain.ports.repositories.usuario_repository import UsuarioRepository


@dataclass
class ValidarDestinatarioOutput:
    existe: bool
    nombre: str
    numero_telefono: str


class ValidarDestinatarioUseCase:
    def __init__(self, usuario_repo: UsuarioRepository):
        self._usuario_repo = usuario_repo

    def ejecutar(self, numero_destino: str) -> ValidarDestinatarioOutput:
        usuario = self._usuario_repo.buscar_por_telefono(numero_destino)

        if not usuario or not usuario.activo:
            return ValidarDestinatarioOutput(
                existe=False, nombre='', numero_telefono=numero_destino
            )

        return ValidarDestinatarioOutput(
            existe=True,
            nombre=usuario.nombre,
            numero_telefono=usuario.numero_telefono,
        )
