# infrastructure/adapters/secondary/bcrypt/bcrypt_password_service.py
# Adaptador secundario: implementa el puerto PasswordService usando bcrypt

import bcrypt

from domain.ports.services.password_service import PasswordService
from config import Config


class BcryptPasswordService(PasswordService):
    """
    Implementación concreta del puerto PasswordService.
    Solo este archivo conoce bcrypt.
    """

    def hashear(self, password: str) -> str:
        return bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt(Config.BCRYPT_LOG_ROUNDS),
        ).decode('utf-8')

    def verificar(self, password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8'),
            )
        except Exception:
            return False
