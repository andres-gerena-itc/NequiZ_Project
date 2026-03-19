# infrastructure/config/seeder.py
# Crea los usuarios iniciales del equipo si no existen.
# Solo conoce el repositorio de dominio (puerto), no MongoDB directamente.

import logging
from datetime import datetime

from domain.entities.usuario import Usuario, PerfilUsuario
from domain.ports.repositories.usuario_repository import UsuarioRepository
from domain.ports.services.password_service import PasswordService
from config import Config

logger = logging.getLogger(__name__)

USUARIOS_INICIALES = [
    {"nombre": "Andrés Gerena",   "numeroTelefono": "3001234567", "email": "andres.gerena@nequiz.com",   "saldo": 1_000_000.0},
    {"nombre": "Fabián Suarez",   "numeroTelefono": "3009876543", "email": "fabian.suarez@nequiz.com",   "saldo": 900_000.0},
    {"nombre": "Camila Mosquera", "numeroTelefono": "3108556655", "email": "camila.mosquera@nequiz.com", "saldo": 750_000.0},
]

PASSWORD_DEFAULT = "nequiz2025"


def sembrar_usuarios(
    usuario_repo: UsuarioRepository,
    password_service: PasswordService,
) -> None:
    """Inserta los usuarios iniciales usando los puertos del dominio."""
    password_hash = password_service.hashear(PASSWORD_DEFAULT)

    for datos in USUARIOS_INICIALES:
        if usuario_repo.existe_telefono(datos["numeroTelefono"]):
            logger.info(f"ℹ️  Ya existe: {datos['nombre']}")
            continue

        usuario = Usuario(
            numero_telefono=datos["numeroTelefono"],
            nombre=datos["nombre"],
            email=datos["email"],
            password_hash=password_hash,
            saldo=datos["saldo"],
            fecha_registro=datetime.utcnow(),
            perfil=PerfilUsuario(biografia="Usuario del equipo NequiZ"),
        )
        usuario_repo.guardar(usuario)
        logger.info(f"✅ Usuario creado: {datos['nombre']}")
