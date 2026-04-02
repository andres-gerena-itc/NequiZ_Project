# tests/fakes/fake_token_service.py
# Fake que simula JWT sin usar PyJWT real (instantáneo en pruebas).

from typing import Dict, Optional

from domain.ports.services.token_service import TokenService


class FakeTokenService(TokenService):
    """
    Implementación falsa del puerto TokenService.
    Genera tokens predecibles para facilitar las aserciones en pruebas.
    Solo para pruebas; jamás usar en producción.
    """

    def generar_access_token(self, numero_telefono: str, nombre: str) -> str:
        return f"fake_access_{numero_telefono}"

    def generar_refresh_token(self, numero_telefono: str) -> str:
        return f"fake_refresh_{numero_telefono}"

    def verificar_token(self, token: str) -> Optional[Dict]:
        # Simula verificación: si el token tiene el formato esperado, retorna payload
        if token.startswith("fake_access_"):
            numero = token.replace("fake_access_", "")
            return {"numeroTelefono": numero, "tipo": "access"}
        if token.startswith("fake_refresh_"):
            numero = token.replace("fake_refresh_", "")
            return {"numeroTelefono": numero, "tipo": "refresh"}
        return None
