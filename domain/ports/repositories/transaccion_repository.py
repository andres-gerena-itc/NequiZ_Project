# domain/ports/repositories/transaccion_repository.py
# Puerto de salida: contrato para el repositorio de transacciones

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from domain.entities.transaccion import Transaccion, TipoMovimiento


class TransaccionRepository(ABC):
    """
    Puerto de salida para persistencia de transacciones.
    """

    @abstractmethod
    def guardar(self, transaccion: Transaccion) -> str:
        """Persiste la transacción y retorna su ID generado."""

    @abstractmethod
    def buscar_por_usuario(
        self,
        numero_telefono: str,
        limite: int = 10,
        offset: int = 0,
        tipo: TipoMovimiento = TipoMovimiento.TODOS,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
    ) -> List[Transaccion]:
        """Retorna el historial paginado y filtrado del usuario."""

    @abstractmethod
    def contar_por_usuario(self, numero_telefono: str) -> int:
        """Cuenta el total de transacciones de un usuario."""

    @abstractmethod
    def sumar_enviado(
        self,
        numero_telefono: str,
        fecha_desde: Optional[datetime] = None,
    ) -> float:
        """Suma total de dinero enviado en el periodo."""

    @abstractmethod
    def sumar_recibido(
        self,
        numero_telefono: str,
        fecha_desde: Optional[datetime] = None,
    ) -> float:
        """Suma total de dinero recibido en el periodo."""

    @abstractmethod
    def contar_en_periodo(
        self,
        numero_telefono: str,
        fecha_desde: Optional[datetime] = None,
    ) -> int:
        """Cuenta transacciones en el periodo dado."""
