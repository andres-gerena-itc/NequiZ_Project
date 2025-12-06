# utils/db.py - Conexión y utilidades de MongoDB

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from config import Config
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cliente MongoDB
try:
    client = MongoClient(Config.MONGODB_URI, serverSelectionTimeoutMS=5000)
    # Verificar conexión
    client.admin.command('ping')
    logger.info("✅ Conexión exitosa a MongoDB Atlas")
except ConnectionFailure as e:
    logger.error(f"❌ Error conectando a MongoDB: {e}")
    raise

# Base de datos
db = client[Config.DATABASE_NAME]

# Colecciones
usuarios_collection = db.usuarios
transacciones_collection = db.transacciones
sesiones_collection = db.sesiones


def init_db():
    """
    Inicializar base de datos con índices y datos iniciales
    """
    logger.info("🔧 Inicializando base de datos...")
    
    try:
        # ============= ÍNDICES USUARIOS =============
        # Índice único para número de teléfono
        usuarios_collection.create_index(
            [("numeroTelefono", ASCENDING)], 
            unique=True,
            name="idx_numero_telefono_unique"
        )
        
        # Índice para email (único)
        usuarios_collection.create_index(
            [("email", ASCENDING)], 
            unique=True,
            name="idx_email_unique"
        )
        
        # Índice para búsquedas por nombre
        usuarios_collection.create_index(
            [("nombre", ASCENDING)],
            name="idx_nombre"
        )
        
        logger.info("✅ Índices de usuarios creados")
        
        # ============= ÍNDICES TRANSACCIONES =============
        # Índice compuesto para consultas de historial
        transacciones_collection.create_index(
            [("numeroOrigen", ASCENDING), ("fecha", DESCENDING)],
            name="idx_origen_fecha"
        )
        
        transacciones_collection.create_index(
            [("numeroDestino", ASCENDING), ("fecha", DESCENDING)],
            name="idx_destino_fecha"
        )
        
        # Índice para búsquedas por estado
        transacciones_collection.create_index(
            [("estado", ASCENDING)],
            name="idx_estado"
        )
        
        logger.info("✅ Índices de transacciones creados")
        
        # ============= ÍNDICES SESIONES =============
        # Índice para refresh tokens
        sesiones_collection.create_index(
            [("refreshToken", ASCENDING)],
            name="idx_refresh_token"
        )
        
        # Índice con TTL para expiración automática de sesiones
        sesiones_collection.create_index(
            [("fechaExpiracion", ASCENDING)],
            expireAfterSeconds=0,  # Se borra automáticamente después de fechaExpiracion
            name="idx_expiracion_ttl"
        )
        
        logger.info("✅ Índices de sesiones creados")
        
        # ============= CREAR USUARIOS INICIALES =============
        crear_usuarios_iniciales()
        
        logger.info("✅ Base de datos inicializada correctamente")
        
    except Exception as e:
        logger.error(f"❌ Error inicializando base de datos: {e}")
        raise


def crear_usuarios_iniciales():
    """
    Crear usuarios iniciales del equipo si no existen
    """
    import bcrypt
    from datetime import datetime
    
    usuarios_iniciales = [
        {
            "nombre": "Andrés Gerena",
            "numeroTelefono": "3001234567",
            "email": "andres.gerena@nequiz.com",
            "saldo": 1000000.0
        },
        {
            "nombre": "Fabián Suarez",
            "numeroTelefono": "3009876543",
            "email": "fabian.suarez@nequiz.com",
            "saldo": 900000.0
        },
        {
            "nombre": "Camila Mosquera",
            "numeroTelefono": "3108556655",
            "email": "camila.mosquera@nequiz.com",
            "saldo": 750000.0
        }
    ]
    
    # Password por defecto para todos: "nequiz2025"
    password_default = "nequiz2025"
    password_hash = bcrypt.hashpw(password_default.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    for user_data in usuarios_iniciales:
        try:
            # Verificar si el usuario ya existe
            existing = usuarios_collection.find_one({"numeroTelefono": user_data["numeroTelefono"]})
            
            if not existing:
                usuario = {
                    "nombre": user_data["nombre"],
                    "numeroTelefono": user_data["numeroTelefono"],
                    "email": user_data["email"],
                    "passwordHash": password_hash,
                    "saldo": user_data["saldo"],
                    "fechaRegistro": datetime.utcnow(),
                    "activo": True,
                    "perfil": {
                        "foto": None,
                        "biografia": f"Usuario del equipo NequiZ"
                    }
                }
                
                usuarios_collection.insert_one(usuario)
                logger.info(f"✅ Usuario creado: {user_data['nombre']} ({user_data['numeroTelefono']})")
            else:
                logger.info(f"ℹ️  Usuario ya existe: {user_data['nombre']}")
                
        except DuplicateKeyError:
            logger.info(f"ℹ️  Usuario duplicado (ya existe): {user_data['nombre']}")
        except Exception as e:
            logger.error(f"❌ Error creando usuario {user_data['nombre']}: {e}")


def verificar_conexion():
    """
    Verificar que la conexión a MongoDB está activa
    """
    try:
        client.admin.command('ping')
        return True
    except Exception as e:
        logger.error(f"❌ Error de conexión a MongoDB: {e}")
        return False


def obtener_stats_db():
    """
    Obtener estadísticas de la base de datos
    """
    try:
        stats = {
            "usuarios": usuarios_collection.count_documents({}),
            "transacciones": transacciones_collection.count_documents({}),
            "sesiones_activas": sesiones_collection.count_documents({}),
            "base_datos": Config.DATABASE_NAME,
            "conectado": verificar_conexion()
        }
        return stats
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")
        return None


# Exportar colecciones para uso en otros módulos
__all__ = [
    'db',
    'usuarios_collection',
    'transacciones_collection',
    'sesiones_collection',
    'init_db',
    'verificar_conexion',
    'obtener_stats_db'
]