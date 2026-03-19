# application/use_cases/movimientos/obtener_movimientos.py

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional

from domain.entities.transaccion import TipoMovimiento
from domain.ports.repositories.transaccion_repository import TransaccionRepository


@dataclass
class ObtenerMovimientosInput:
    numero_telefono: str
    limite: int = 10
    offset: int = 0
    tipo: TipoMovimiento = TipoMovimiento.TODOS
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None


class ObtenerMovimientosUseCase:
    def __init__(self, transaccion_repo: TransaccionRepository):
        self._transaccion_repo = transaccion_repo

    def ejecutar(self, datos: ObtenerMovimientosInput) -> List[Dict]:
        limite = min(datos.limite, 100)

        transacciones = self._transaccion_repo.buscar_por_usuario(
            numero_telefono=datos.numero_telefono,
            limite=limite,
            offset=datos.offset,
            tipo=datos.tipo,
            fecha_desde=datos.fecha_desde,
            fecha_hasta=datos.fecha_hasta,
        )

        resultado = []
        for trans in transacciones:
            tipo_mov = trans.tipo_para_usuario(datos.numero_telefono)
            fecha_str = (
                trans.fecha.isoformat()
                if hasattr(trans.fecha, 'isoformat')
                else str(trans.fecha)
            )
            resultado.append({
                'id': trans.id,
                'tipo': tipo_mov.value,
                'numero_origen': trans.numero_origen,
                'nombre_origen': trans.nombre_origen,
                'numero_destino': trans.numero_destino,
                'nombre_destino': trans.nombre_destino,
                'monto': trans.monto,
                'mensaje': trans.mensaje,
                'fecha': fecha_str,
                'estado': trans.estado.value,
            })

        return resultado


# ─────────────────────────────────────────────────────────────────────────────


# application/use_cases/movimientos/obtener_estadisticas.py

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict

from domain.ports.repositories.transaccion_repository import TransaccionRepository


class Periodo:
    HOY = 'HOY'
    SEMANA_ACTUAL = 'SEMANA_ACTUAL'
    MES_ACTUAL = 'MES_ACTUAL'
    TODO = 'TODO'

    @staticmethod
    def calcular_fecha_desde(periodo: str) -> datetime | None:
        ahora = datetime.utcnow()
        if periodo == Periodo.HOY:
            return ahora.replace(hour=0, minute=0, second=0, microsecond=0)
        if periodo == Periodo.SEMANA_ACTUAL:
            inicio = ahora - timedelta(days=ahora.weekday())
            return inicio.replace(hour=0, minute=0, second=0, microsecond=0)
        if periodo == Periodo.MES_ACTUAL:
            return ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return None  # TODO: todas las transacciones


@dataclass
class ObtenerEstadisticasInput:
    numero_telefono: str
    periodo: str = Periodo.MES_ACTUAL


class ObtenerEstadisticasUseCase:
    def __init__(self, transaccion_repo: TransaccionRepository):
        self._transaccion_repo = transaccion_repo

    def ejecutar(self, datos: ObtenerEstadisticasInput) -> Dict:
        fecha_desde = Periodo.calcular_fecha_desde(datos.periodo)

        total_enviado = self._transaccion_repo.sumar_enviado(
            datos.numero_telefono, fecha_desde
        )
        total_recibido = self._transaccion_repo.sumar_recibido(
            datos.numero_telefono, fecha_desde
        )
        cantidad = self._transaccion_repo.contar_en_periodo(
            datos.numero_telefono, fecha_desde
        )

        promedio = (total_enviado + total_recibido) / cantidad if cantidad > 0 else 0

        return {
            'total_enviado': total_enviado,
            'total_recibido': total_recibido,
            'cantidad_transacciones': cantidad,
            'promedio_transaccion': promedio,
            'periodo': datos.periodo,
            'balance': total_recibido - total_enviado,
        }
