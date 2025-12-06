# app.py - Aplicación Principal NequiZ

from flask import Flask, jsonify, render_template
from flask_cors import CORS
from graphql_server.flask import GraphQLView
from config import get_config
from utils.db import init_db, verificar_conexion, obtener_stats_db
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)
config = get_config()
app.config.from_object(config)

# Configurar CORS
CORS(app, resources={
    r"/api/*": {"origins": config.CORS_ORIGINS},
    r"/graphql": {"origins": config.CORS_ORIGINS}
})

# Importar Blueprints (rutas REST)
from routes.auth import auth_bp
from routes.perfil import perfil_bp
from routes.transferencias import transferencias_bp

# Registrar Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(perfil_bp)
app.register_blueprint(transferencias_bp)

# Importar Schema GraphQL
from graphql_schema.schema import schema
from flask import request

# Función para obtener contexto con autenticación
def get_graphql_context():
    """
    Extrae el contexto de la petición para GraphQL
    Incluye los headers para que los resolvers puedan acceder al token JWT
    """
    logger.info("\n🌐 get_graphql_context() llamado")
    logger.info(f"📨 Authorization header: {request.headers.get('Authorization', 'NO ENCONTRADO')[:50]}")
    
    return {
        'headers': request.headers,
        'request': request
    }

# Configurar endpoint GraphQL
from graphql_server.flask import GraphQLView

app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True,
        get_context=get_graphql_context  # 👈 IMPORTANTE: Esta línea debe estar
    )
)


# ============= RUTAS PRINCIPALES =============

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')


@app.route('/login')
def login_page():
    """Página de login"""
    return render_template('login.html')


@app.route('/registro')
def registro_page():
    """Página de registro"""
    return render_template('registro.html')


@app.route('/perfil')
def perfil_page():
    """Página de perfil"""
    return render_template('perfil.html')


@app.route('/transferir')
def transferir_page():
    """Página de transferencias"""
    return render_template('transferir.html')


@app.route('/movimientos')
def movimientos_page():
    """Página de historial de movimientos"""
    return render_template('movimientos.html')


# ============= API DE SALUD Y ESTADÍSTICAS =============

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check de la aplicación
    
    GET /api/health
    
    Response:
    {
        "status": "ok",
        "service": "NequiZ API",
        "version": "1.0.0",
        "database": "connected"
    }
    """
    db_status = "connected" if verificar_conexion() else "disconnected"
    
    return jsonify({
        "status": "ok",
        "service": "NequiZ API",
        "version": config.APP_VERSION,
        "database": db_status
    }), 200


@app.route('/api/stats', methods=['GET'])
def stats():
    """
    Estadísticas generales de la base de datos
    
    GET /api/stats
    
    Response:
    {
        "usuarios": 10,
        "transacciones": 25,
        "sesiones_activas": 3
    }
    """
    stats_data = obtener_stats_db()
    
    if not stats_data:
        return jsonify({"error": "No se pudieron obtener estadísticas"}), 500
    
    return jsonify(stats_data), 200


@app.route('/api/info', methods=['GET'])
def info():
    """
    Información de la API
    
    GET /api/info
    
    Response:
    {
        "nombre": "NequiZ",
        "version": "1.0.0",
        "descripcion": "Sistema de billetera digital",
        "endpoints": {...}
    }
    """
    return jsonify({
        "nombre": config.APP_NAME,
        "version": config.APP_VERSION,
        "descripcion": "Sistema de billetera digital con GraphQL y REST API",
        "autores": [
            "Andrés Gerena",
            "Fabián Suarez",
            "Camila Mosquera"
        ],
        "endpoints": {
            "rest": {
                "auth": "/api/auth/*",
                "perfil": "/api/perfil/*",
                "transferencias": "/api/transferencias/*"
            },
            "graphql": "/graphql"
        },
        "documentacion": {
            "graphiql": "/graphql (navegador)",
            "postman": "Importar colección desde /api/postman"
        }
    }), 200


# ============= MANEJO DE ERRORES =============

@app.errorhandler(404)
def not_found(error):
    """Manejo de error 404"""
    return jsonify({
        "error": "Recurso no encontrado",
        "codigo": 404
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Manejo de error 500"""
    logger.error(f"Error interno: {error}")
    return jsonify({
        "error": "Error interno del servidor",
        "codigo": 500
    }), 500


@app.errorhandler(403)
def forbidden(error):
    """Manejo de error 403"""
    return jsonify({
        "error": "Acceso prohibido",
        "codigo": 403
    }), 403


@app.errorhandler(401)
def unauthorized(error):
    """Manejo de error 401"""
    return jsonify({
        "error": "No autorizado. Token requerido",
        "codigo": 401
    }), 401


# ============= INICIALIZACIÓN =============

def inicializar_app():
    """Inicializar la aplicación"""
    logger.info("=" * 60)
    logger.info(f"🚀 Iniciando {config.APP_NAME} v{config.APP_VERSION}")
    logger.info("=" * 60)
    
    # Inicializar base de datos
    try:
        init_db()
        logger.info("✅ Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"❌ Error inicializando base de datos: {e}")
        raise
    
    # Mostrar información de usuarios iniciales
    logger.info("\n👥 Usuarios del equipo (password: nequiz2025):")
    logger.info("   • Andrés Gerena - 3001234567")
    logger.info("   • Fabián Suarez - 3009876543")
    logger.info("   • Camila Mosquera - 3108556655")
    
    logger.info("\n🔗 Endpoints disponibles:")
    logger.info("   • REST API: /api/*")
    logger.info("   • GraphQL: /graphql")
    logger.info("   • GraphiQL: /graphql (navegador)")
    logger.info("   • Health: /api/health")
    logger.info("   • Info: /api/info")
    
    logger.info("\n📱 Aplicación Web:")
    logger.info("   • Login: /login")
    logger.info("   • Registro: /registro")
    logger.info("   • Perfil: /perfil")
    logger.info("   • Transferir: /transferir")
    logger.info("   • Movimientos: /movimientos")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"✅ Servidor corriendo en: http://0.0.0.0:{config.PORT if hasattr(config, 'PORT') else 5000}")
    logger.info("=" * 60 + "\n")


# ============= PUNTO DE ENTRADA =============

if __name__ == '__main__':
    # Inicializar aplicación
    inicializar_app()
    
    # Ejecutar servidor
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=config.DEBUG
    )