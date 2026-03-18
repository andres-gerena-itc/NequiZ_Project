# tests/fakes/fake_transaccion_repository.py

from datetime import datetime
from typing import Dict, List, Optional

from domain.entities.transaccion import Transaccion, TipoMovimiento
from domain.ports.repositories.transaccion_repository import TransaccionRepository


class FakeTransaccionRepository(TransaccionRepository):
    """
    Implementación falsa del puerto TransaccionRepository.
    Almacena transacciones en una lista en RAM.
    """

    def __init__(self):
        self._store: List[Transaccion] = []

    def guardar(self, transaccion: Transaccion) -> str:
        self._store.append(transaccion)
        return transaccion.id

    def buscar_por_usuario(
        self,
        numero_telefono: str,
        limite: int = 10,
        offset: int = 0,
        tipo: TipoMovimiento = TipoMovimiento.TODOS,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
    ) -> List[Transaccion]:
        resultado = []
        for t in self._store:
            if tipo == TipoMovimiento.ENVIADO and t.numero_origen != numero_telefono:
                continue
            if tipo == TipoMovimiento.RECIBIDO and t.numero_destino != numero_telefono:
                continue
            if tipo == TipoMovimiento.TODOS:
                if t.numero_origen != numero_telefono and t.numero_destino != numero_telefono:
                    continue
            resultado.append(t)
        return resultado[offset: offset + limite]

    def contar_por_usuario(self, numero_telefono: str) -> int:
        return sum(
            1 for t in self._store
            if t.numero_origen == numero_telefono or t.numero_destino == numero_telefono
        )

    def sumar_enviado(
        self, numero_telefono: str, fecha_desde: Optional[datetime] = None
    ) -> float:
        return sum(
            t.monto for t in self._store
            if t.numero_origen == numero_telefono
        )

    def sumar_recibido(
        self, numero_telefono: str, fecha_desde: Optional[datetime] = None
    ) -> float:
        return sum(
            t.monto for t in self._store
            if t.numero_destino == numero_telefono
        )

    def contar_en_periodo(
        self, numero_telefono: str, fecha_desde: Optional[datetime] = None
    ) -> int:
        return self.contar_por_usuario(numero_telefono)
