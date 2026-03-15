# domain/exceptions.py
# Excepciones propias del dominio; no dependen de ningún framework


class DomainError(Exception):
    """Base para todos los errores de dominio."""


class UsuarioNoEncontradoError(DomainError):
    """El usuario no existe en el sistema."""


class UsuarioYaExisteError(DomainError):
    """Intento de registrar un usuario con datos duplicados."""


class UsuarioInactivoError(DomainError):
    """El usuario está desactivado y no puede operar."""


class CredencialesInvalidasError(DomainError):
    """Número de teléfono o contraseña incorrectos."""


class SaldoInsuficienteError(DomainError):
    """El usuario no tiene saldo suficiente para la operación."""


class MontoInvalidoError(DomainError):
    """El monto de la transacción no es válido."""


class TransaccionInvalidaError(DomainError):
    """La transacción no cumple las reglas de negocio."""


class TokenInvalidoError(DomainError):
    """El token JWT no es válido o ha expirado."""
