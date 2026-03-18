# infrastructure/adapters/secondary/mongodb/connection.py
# Detalles de conexión a MongoDB: solo infraestructura, nunca dominio

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure
from config import Config
import logging

logger = logging.getLogger(__name__)


def crear_cliente() -> MongoClient:
    try:
        client = MongoClient(Config.MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        logger.info("✅ Conexión exitosa a MongoDB")
        return client
    except ConnectionFailure as e:
        logger.error(f"❌ Error conectando a MongoDB: {e}")
        raise


# Cliente y colecciones singleton
_client = crear_cliente()
_db = _client[Config.DATABASE_NAME]

usuarios_col = _db.usuarios
transacciones_col = _db.transacciones
sesiones_col = _db.sesiones


def init_indices() -> None:
    """Crea índices necesarios en MongoDB."""
    usuarios_col.create_index([("numeroTelefono", ASCENDING)], unique=True, name="idx_telefono")
    usuarios_col.create_index([("email", ASCENDING)], unique=True, name="idx_email")
    usuarios_col.create_index([("nombre", ASCENDING)], name="idx_nombre")

    transacciones_col.create_index([("numeroOrigen", ASCENDING), ("fecha", DESCENDING)], name="idx_origen_fecha")
    transacciones_col.create_index([("numeroDestino", ASCENDING), ("fecha", DESCENDING)], name="idx_destino_fecha")
    transacciones_col.create_index([("estado", ASCENDING)], name="idx_estado")

    sesiones_col.create_index([("refreshToken", ASCENDING)], name="idx_refresh_token")
    sesiones_col.create_index([("fechaExpiracion", ASCENDING)], expireAfterSeconds=0, name="idx_ttl")

    logger.info("✅ Índices de MongoDB creados")
