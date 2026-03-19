from typing import Optional, List, Any
from datetime import datetime

from domain.entities.usuario import Usuario, PerfilUsuario
from domain.entities.transaccion import Transaccion, EstadoTransaccion, TipoTransaccion, TipoMovimiento
from domain.ports.repositories.usuario_repository import UsuarioRepository
from domain.ports.repositories.transaccion_repository import TransaccionRepository

# Reutilizando la conexión ya existente en la infraestructura
from infrastructure.adapters.secondary.mongodb.connection import usuarios_col, transacciones_col


def _map_usuario_to_doc(usuario: Usuario) -> dict:
    return {
        "numeroTelefono": usuario.numero_telefono,
        "nombre": usuario.nombre,
        "email": usuario.email,
        "passwordHash": usuario.password_hash,
        "saldo": usuario.saldo,
        "fechaRegistro": usuario.fecha_registro,
        "activo": usuario.activo,
        "perfil": {
            "foto": usuario.perfil.foto,
            "biografia": usuario.perfil.biografia
        }
    }


def _map_doc_to_usuario(doc: dict) -> Usuario:
    perfil_doc = doc.get("perfil", {})
    perfil = PerfilUsuario(
        foto=perfil_doc.get("foto"),
        biografia=perfil_doc.get("biografia", "")
    )
    return Usuario(
        numero_telefono=doc.get("numeroTelefono", doc.get("numero_telefono", "")),
        nombre=doc.get("nombre", ""),
        email=doc.get("email", ""),
        password_hash=doc.get("passwordHash", ""),
        saldo=doc.get("saldo", 0.0),
        fecha_registro=doc.get("fechaRegistro") or datetime.now(),
        activo=doc.get("activo", True),
        perfil=perfil
    )


def _map_transaccion_to_doc(transaccion: Transaccion) -> dict:
    return {
        "_id": transaccion.id,
        "numeroOrigen": transaccion.numero_origen,
        "nombreOrigen": transaccion.nombre_origen,
        "numeroDestino": transaccion.numero_destino,
        "nombreDestino": transaccion.nombre_destino,
        "monto": transaccion.monto,
        "fecha": transaccion.fecha,
        "mensaje": transaccion.mensaje,
        "estado": transaccion.estado.value,
        "tipo": transaccion.tipo.value
    }


def _map_doc_to_transaccion(doc: dict) -> Transaccion:
    t = Transaccion(
        numero_origen=doc.get("numeroOrigen", ""),
        nombre_origen=doc.get("nombreOrigen", ""),
        numero_destino=doc.get("numeroDestino", ""),
        nombre_destino=doc.get("nombreDestino", ""),
        monto=doc.get("monto", 0.0),
        fecha=doc.get("fecha") or datetime.now(),
        id=doc.get("_id", ""),
        mensaje=doc.get("mensaje", "")
    )
    t.estado = EstadoTransaccion(doc.get("estado", EstadoTransaccion.EXITOSA.value))
    t.tipo = TipoTransaccion(doc.get("tipo", TipoTransaccion.TRANSFERENCIA_P2P.value))
    return t


class MongoUsuarioRepository(UsuarioRepository):
    def __init__(self, collection: Any = usuarios_col):
        self.collection = collection

    def guardar(self, usuario: Usuario) -> None:
        doc = _map_usuario_to_doc(usuario)
        self.collection.insert_one(doc)

    def actualizar(self, usuario: Usuario) -> None:
        doc = _map_usuario_to_doc(usuario)
        self.collection.update_one(
            {"numeroTelefono": usuario.numero_telefono},
            {"$set": doc}
        )

    def buscar_por_telefono(self, numero_telefono: str) -> Optional[Usuario]:
        doc = self.collection.find_one({"numeroTelefono": numero_telefono})
        if doc:
            return _map_doc_to_usuario(doc)
        return None

    def buscar_por_email(self, email: str) -> Optional[Usuario]:
        doc = self.collection.find_one({"email": email})
        if doc:
            return _map_doc_to_usuario(doc)
        return None

    def existe_telefono(self, numero_telefono: str) -> bool:
        return self.collection.count_documents({"numeroTelefono": numero_telefono}, limit=1) > 0

    def existe_email(self, email: str) -> bool:
        return self.collection.count_documents({"email": email}, limit=1) > 0


class MongoTransaccionRepository(TransaccionRepository):
    def __init__(self, collection: Any = transacciones_col):
        self.collection = collection

    def guardar(self, transaccion: Transaccion) -> str:
        doc = _map_transaccion_to_doc(transaccion)
        self.collection.insert_one(doc)
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
        query: dict[str, Any] = {}
        if tipo == TipoMovimiento.ENVIADO:
            query["numeroOrigen"] = numero_telefono
        elif tipo == TipoMovimiento.RECIBIDO:
            query["numeroDestino"] = numero_telefono
        else:
            query["$or"] = [{"numeroOrigen": numero_telefono}, {"numeroDestino": numero_telefono}]

        if fecha_desde or fecha_hasta:
            query["fecha"] = {}
            if fecha_desde:
                query["fecha"]["$gte"] = fecha_desde
            if fecha_hasta:
                query["fecha"]["$lte"] = fecha_hasta

        docs = self.collection.find(query).sort("fecha", -1).skip(offset).limit(limite)
        return [_map_doc_to_transaccion(doc) for doc in docs]

    def contar_por_usuario(self, numero_telefono: str) -> int:
        return self.collection.count_documents({
            "$or": [{"numeroOrigen": numero_telefono}, {"numeroDestino": numero_telefono}]
        })

    def sumar_enviado(
        self,
        numero_telefono: str,
        fecha_desde: Optional[datetime] = None,
    ) -> float:
        match = {"numeroOrigen": numero_telefono, "estado": EstadoTransaccion.EXITOSA.value}
        if fecha_desde:
            match["fecha"] = {"$gte": fecha_desde}
        
        pipeline = [
            {"$match": match},
            {"$group": {"_id": None, "total": {"$sum": "$monto"}}}
        ]
        result = list(self.collection.aggregate(pipeline))
        return result[0]["total"] if result else 0.0

    def sumar_recibido(
        self,
        numero_telefono: str,
        fecha_desde: Optional[datetime] = None,
    ) -> float:
        match = {"numeroDestino": numero_telefono, "estado": EstadoTransaccion.EXITOSA.value}
        if fecha_desde:
            match["fecha"] = {"$gte": fecha_desde}
            
        pipeline = [
            {"$match": match},
            {"$group": {"_id": None, "total": {"$sum": "$monto"}}}
        ]
        result = list(self.collection.aggregate(pipeline))
        return result[0]["total"] if result else 0.0

    def contar_en_periodo(
        self,
        numero_telefono: str,
        fecha_desde: Optional[datetime] = None,
    ) -> int:
        query = {"$or": [{"numeroOrigen": numero_telefono}, {"numeroDestino": numero_telefono}]}
        if fecha_desde:
            query["fecha"] = {"$gte": fecha_desde}
        return self.collection.count_documents(query)
