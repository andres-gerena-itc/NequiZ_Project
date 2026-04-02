# domain/entities/usuario.py
# Entidad pura de dominio: sin dependencias externas

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from domain.exceptions import SaldoInsuficienteError, MontoInvalidoError


@dataclass
class PerfilUsuario:
    """Objeto de valor: datos opcionales del perfil"""
    foto: Optional[str] = None
    biografia: str = ''


@dataclass
class Usuario:
    """
    Entidad de dominio: Usuario
    Encapsula las reglas de negocio relacionadas con el usuario.
    No conoce MongoDB, Flask, JWT ni ningún detalle de infraestructura.
    """
    numero_telefono: str
    nombre: str
    email: str
    password_hash: str
    saldo: float
    fecha_registro: datetime
    activo: bool = True
    perfil: PerfilUsuario = field(default_factory=PerfilUsuario)

    # ── Reglas de negocio ──────────────────────────────────────────────

    def tiene_saldo_suficiente(self, monto: float) -> bool:
        return self.saldo >= monto

    def debitar(self, monto: float) -> None:
        """Descuenta saldo; lanza error de dominio si no alcanza."""
        if monto <= 0:
            raise MontoInvalidoError("El monto debe ser mayor a cero")
        if not self.tiene_saldo_suficiente(monto):
            raise SaldoInsuficienteError(
                f"Saldo insuficiente. Disponible: {self.saldo}, requerido: {monto}"
            )
        self.saldo -= monto

    def acreditar(self, monto: float) -> None:
        """Suma saldo."""
        if monto <= 0:
            raise MontoInvalidoError("El monto debe ser mayor a cero")
        self.saldo += monto

    def desactivar(self) -> None:
        self.activo = False

    def actualizar_nombre(self, nuevo_nombre: str) -> None:
        if not nuevo_nombre or len(nuevo_nombre.strip()) < 2:
            raise ValueError("Nombre inválido")
        self.nombre = nuevo_nombre.strip()

    def actualizar_biografia(self, bio: str) -> None:
        if len(bio) > 500:
            raise ValueError("Biografía demasiado larga (máximo 500 caracteres)")
        self.perfil.biografia = bio
