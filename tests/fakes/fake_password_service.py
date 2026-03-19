# tests/fakes/fake_password_service.py
# Fake que simula hashing sin usar bcrypt real (instantáneo en pruebas).

from domain.ports.services.password_service import PasswordService


class FakePasswordService(PasswordService):
    """
    Implementación falsa del puerto PasswordService.
    No usa bcrypt — simplemente agrega el prefijo 'hashed_' al password.
    Solo para pruebas; jamás usar en producción.
    """

    def hashear(self, password: str) -> str:
        return f"hashed_{password}"

    def verificar(self, password: str, password_hash: str) -> bool:
        return password_hash == f"hashed_{password}"
