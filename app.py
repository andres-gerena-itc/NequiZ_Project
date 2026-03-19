# app.py - Punto de entrada de la aplicación NequiZ (Arquitectura Hexagonal)
#
# Responsabilidades de este archivo:
#   1. Crear el contenedor de dependencias (Container)
#   2. Instanciar Flask y registrar los blueprints (adaptadores primarios REST)
#   3. Registrar el endpoint GraphQL (adaptador primario GraphQL)
#   4. Inicializar BD e índices
#
# Lo que NO hace este archivo:
#   - Lógica de negocio
#   - Acceso directo a MongoDB, JWT o bcrypt

import logging
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from graphql_server.flask import GraphQLView
import graphene

from config import get_config
from infrastructure.config.container import Container
from infrastructure.config.seeder import sembrar_usuarios
from infrastructure.adapters.secondary.mongodb.connection import init_indices
from infrastructure.adapters.primary.rest.middlewares import init_middlewares
from infrastructure.adapters.primary.rest.auth_routes import crear_auth_blueprint
from infrastructure.adapters.primary.rest.perfil_routes import crear_perfil_blueprint
from infrastructure.adapters.primary.rest.transferencias_routes import crear_transferencias_blueprint
from infrastructure.adapters.primary.graphql.queries import crear_query_class

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# ── Configuración ────────────────────────────────────────────────────────────
config = get_config()

# ── Flask ────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config.from_object(config)

CORS(app, resources={
    r"/api/*": {"origins": config.CORS_ORIGINS},
    r"/graphql": {"origins": config.CORS_ORIGINS},
})

# ── Contenedor de dependencias (único punto de ensamblaje) ───────────────────
container = Container()

# ── Inicializar middlewares con el token_service inyectado ───────────────────
init_middlewares(container.token_service)

# ── Registrar blueprints REST ────────────────────────────────────────────────
app.register_blueprint(crear_auth_blueprint(
    registrar_uc=container.registrar_usuario_uc,
    login_uc=container.login_usuario_uc,
    logout_uc=container.logout_usuario_uc,
    refresh_uc=container.refresh_token_uc,
))

app.register_blueprint(crear_perfil_blueprint(
    obtener_perfil_uc=container.obtener_perfil_uc,
    actualizar_perfil_uc=container.actualizar_perfil_uc,
    obtener_saldo_uc=container.obtener_saldo_uc,
))

app.register_blueprint(crear_transferencias_blueprint(
    enviar_dinero_uc=container.enviar_dinero_uc,
    validar_destinatario_uc=container.validar_destinatario_uc,
    obtener_movimientos_uc=container.obtener_movimientos_uc,
))

# ── Schema GraphQL ───────────────────────────────────────────────────────────
QueryClass = crear_query_class(
    obtener_perfil_uc=container.obtener_perfil_uc,
    obtener_movimientos_uc=container.obtener_movimientos_uc,
    obtener_estadisticas_uc=container.obtener_estadisticas_uc,
    validar_destinatario_uc=container.validar_destinatario_uc,
)
schema = graphene.Schema(query=QueryClass)


def get_graphql_context():
    return {'headers': request.headers, 'request': request}


app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True,
        get_context=get_graphql_context,
    ),
)

# ── Rutas de páginas HTML ────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/registro')
def registro_page():
    return render_template('registro.html')

@app.route('/perfil')
def perfil_page():
    return render_template('perfil.html')

@app.route('/transferir')
def transferir_page():
    return render_template('transferir.html')

@app.route('/movimientos')
def movimientos_page():
    return render_template('movimientos.html')

# ── API de salud ─────────────────────────────────────────────────────────────
@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'service': config.APP_NAME, 'version': config.APP_VERSION}), 200

@app.route('/api/info')
def info():
    return jsonify({
        'nombre': config.APP_NAME,
        'version': config.APP_VERSION,
        'autores': ['Andrés Gerena', 'Fabián Suarez', 'Camila Mosquera'],
        'arquitectura': 'Hexagonal (Ports & Adapters)',
        'endpoints': {
            'rest': {'auth': '/api/auth/*', 'perfil': '/api/perfil/*', 'transferencias': '/api/transferencias/*'},
            'graphql': '/graphql',
        },
    }), 200

# ── Manejo de errores ─────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Recurso no encontrado', 'codigo': 404}), 404

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Error interno: {e}")
    return jsonify({'error': 'Error interno del servidor', 'codigo': 500}), 500

# ── Inicialización ────────────────────────────────────────────────────────────
def inicializar():
    logger.info("=" * 60)
    logger.info(f"🚀 Iniciando {config.APP_NAME} v{config.APP_VERSION} — Arquitectura Hexagonal")
    logger.info("=" * 60)

    init_indices()
    sembrar_usuarios(container.usuario_repo, container.password_service)

    logger.info("\n👥 Usuarios del equipo (password: nequiz2025):")
    logger.info("   • Andrés Gerena   - 3001234567")
    logger.info("   • Fabián Suarez   - 3009876543")
    logger.info("   • Camila Mosquera - 3108556655")
    logger.info("\n" + "=" * 60)


# ── Punto de entrada ──────────────────────────────────────────────────────────
if __name__ == '__main__':
    inicializar()
    app.run(host='0.0.0.0', port=5000, debug=config.DEBUG)
