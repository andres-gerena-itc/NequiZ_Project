# domain/entities/transaccion.py
# Entidad pura de dominio: sin dependencias externas

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid

from domain.exceptions import MontoInvalidoError, TransaccionInvalidaError


class EstadoTransaccion(Enum):
    EXITOSA = 'EXITOSA'
    FALLIDA = 'FALLIDA'
    PENDIENTE = 'PENDIENTE'


class TipoTransaccion(Enum):
    TRANSFERENCIA_P2P = 'TRANSFERENCIA_P2P'


class TipoMovimiento(Enum):
    """Vista del movimiento desde el punto de vista de un usuario."""
    ENVIADO = 'ENVIADO'
    RECIBIDO = 'RECIBIDO'
    TODOS = 'TODOS'


@dataclass
class Transaccion:
    """
    Entidad de dominio: Transaccion
    Representa una transferencia entre dos usuarios.
    Contiene las reglas de validación propias de una transacción.
    """
    numero_origen: str
    nombre_origen: str
    numero_destino: str
    nombre_destino: str
    monto: float
    fecha: datetime
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    mensaje: str = ''
    estado: EstadoTransaccion = EstadoTransaccion.EXITOSA
    tipo: TipoTransaccion = TipoTransaccion.TRANSFERENCIA_P2P

    def __post_init__(self):
        self._validar()

    def _validar(self) -> None:
        if self.monto <= 0:
            raise MontoInvalidoError("El monto debe ser mayor a cero")
        if self.numero_origen == self.numero_destino:
            raise TransaccionInvalidaError("No puedes enviarte dinero a ti mismo")
        if self.monto > 50_000_000:
            raise MontoInvalidoError("Monto excede el límite permitido (50 millones)")

    def tipo_para_usuario(self, numero_telefono: str) -> TipoMovimiento:
        """Determina si este movimiento fue enviado o recibido por el usuario dado."""
        if self.numero_origen == numero_telefono:
            return TipoMovimiento.ENVIADO
        return TipoMovimiento.RECIBIDO

    def marcar_como_fallida(self) -> None:
        self.estado = EstadoTransaccion.FALLIDA
