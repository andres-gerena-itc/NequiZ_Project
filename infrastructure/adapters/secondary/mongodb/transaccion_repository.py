# infrastructure/adapters/secondary/mongodb/transaccion_repository.py

from datetime import datetime
from typing import List, Optional

from bson import ObjectId

from domain.entities.transaccion import (
    Transaccion, EstadoTransaccion, TipoTransaccion, TipoMovimiento
)
from domain.ports.repositories.transaccion_repository import TransaccionRepository
from infrastructure.adapters.secondary.mongodb.connection import transacciones_col


class MongoTransaccionRepository(TransaccionRepository):
    """
    Implementación concreta del puerto TransaccionRepository sobre MongoDB.
    """

    @staticmethod
    def _a_documento(t: Transaccion) -> dict:
        return {
            'numeroOrigen': t.numero_origen,
            'nombreOrigen': t.nombre_origen,
            'numeroDestino': t.numero_destino,
            'nombreDestino': t.nombre_destino,
            'monto': t.monto,
            'mensaje': t.mensaje,
            'fecha': t.fecha,
            'estado': t.estado.value,
            'tipo': t.tipo.value,
        }

    @staticmethod
    def _a_entidad(doc: dict) -> Transaccion:
        return Transaccion(
            id=str(doc['_id']),
            numero_origen=doc['numeroOrigen'],
            nombre_origen=doc.get('nombreOrigen', ''),
            numero_destino=doc['numeroDestino'],
            nombre_destino=doc.get('nombreDestino', ''),
            monto=doc['monto'],
            fecha=doc['fecha'],
            mensaje=doc.get('mensaje', ''),
            estado=EstadoTransaccion(doc.get('estado', 'EXITOSA')),
            tipo=TipoTransaccion(doc.get('tipo', 'TRANSFERENCIA_P2P')),
        )

    def guardar(self, transaccion: Transaccion) -> str:
        result = transacciones_col.insert_one(self._a_documento(transaccion))
        return str(result.inserted_id)

    def buscar_por_usuario(
        self,
        numero_telefono: str,
        limite: int = 10,
        offset: int = 0,
        tipo: TipoMovimiento = TipoMovimiento.TODOS,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
    ) -> List[Transaccion]:
        filtro = self._construir_filtro(numero_telefono, tipo, fecha_desde, fecha_hasta)

        docs = (
            transacciones_col
            .find(filtro)
            .sort('fecha', -1)
            .skip(offset)
            .limit(limite)
        )
        return [self._a_entidad(d) for d in docs]

    def contar_por_usuario(self, numero_telefono: str) -> int:
        return transacciones_col.count_documents({
            '$or': [
                {'numeroOrigen': numero_telefono},
                {'numeroDestino': numero_telefono},
            ]
        })

    def sumar_enviado(
        self, numero_telefono: str, fecha_desde: Optional[datetime] = None
    ) -> float:
        filtro = {'numeroOrigen': numero_telefono}
        if fecha_desde:
            filtro['fecha'] = {'$gte': fecha_desde}
        resultado = list(transacciones_col.aggregate([
            {'$match': filtro},
            {'$group': {'_id': None, 'total': {'$sum': '$monto'}}},
        ]))
        return resultado[0]['total'] if resultado else 0.0

    def sumar_recibido(
        self, numero_telefono: str, fecha_desde: Optional[datetime] = None
    ) -> float:
        filtro = {'numeroDestino': numero_telefono}
        if fecha_desde:
            filtro['fecha'] = {'$gte': fecha_desde}
        resultado = list(transacciones_col.aggregate([
            {'$match': filtro},
            {'$group': {'_id': None, 'total': {'$sum': '$monto'}}},
        ]))
        return resultado[0]['total'] if resultado else 0.0

    def contar_en_periodo(
        self, numero_telefono: str, fecha_desde: Optional[datetime] = None
    ) -> int:
        filtro: dict = {
            '$or': [
                {'numeroOrigen': numero_telefono},
                {'numeroDestino': numero_telefono},
            ]
        }
        if fecha_desde:
            filtro['fecha'] = {'$gte': fecha_desde}
        return transacciones_col.count_documents(filtro)

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _construir_filtro(
        numero_telefono: str,
        tipo: TipoMovimiento,
        fecha_desde: Optional[datetime],
        fecha_hasta: Optional[datetime],
    ) -> dict:
        if tipo == TipoMovimiento.ENVIADO:
            filtro: dict = {'numeroOrigen': numero_telefono}
        elif tipo == TipoMovimiento.RECIBIDO:
            filtro = {'numeroDestino': numero_telefono}
        else:
            filtro = {'$or': [
                {'numeroOrigen': numero_telefono},
                {'numeroDestino': numero_telefono},
            ]}

        if fecha_desde or fecha_hasta:
            fecha_filtro = {}
            if fecha_desde:
                fecha_filtro['$gte'] = fecha_desde
            if fecha_hasta:
                fecha_filtro['$lte'] = fecha_hasta
            filtro['fecha'] = fecha_filtro

        return filtro
