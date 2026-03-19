# infrastructure/config/validators.py
# Validaciones de entrada de datos: viven en infraestructura, no en el dominio.
# El dominio valida invariantes; este módulo valida el formato de los datos externos.

import re
from typing import Tuple, Optional


def validar_numero_telefono(numero: str) -> Tuple[bool, Optional[str]]:
    if not numero:
        return False, "Número de teléfono es requerido"
    limpio = re.sub(r'[^\d]', '', numero)
    if len(limpio) != 10:
        return False, "Número de teléfono debe tener 10 dígitos"
    if not limpio.startswith('3'):
        return False, "Número de teléfono debe comenzar con 3"
    return True, None


def validar_email(email: str) -> Tuple[bool, Optional[str]]:
    if not email:
        return False, "Email es requerido"
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(patron, email):
        return False, "Formato de email inválido"
    if len(email) > 254:
        return False, "Email demasiado largo"
    return True, None


def validar_password(password: str) -> Tuple[bool, Optional[str]]:
    if not password:
        return False, "Contraseña es requerida"
    if len(password) < 6:
        return False, "Contraseña debe tener al menos 6 caracteres"
    if len(password) > 128:
        return False, "Contraseña demasiado larga"
    return True, None


def validar_nombre(nombre: str) -> Tuple[bool, Optional[str]]:
    if not nombre:
        return False, "Nombre es requerido"
    limpio = nombre.strip()
    if len(limpio) < 2:
        return False, "Nombre debe tener al menos 2 caracteres"
    if len(limpio) > 100:
        return False, "Nombre demasiado largo"
    if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\'-]+$', limpio):
        return False, "Nombre contiene caracteres no válidos"
    return True, None


def validar_monto(monto) -> Tuple[bool, Optional[str]]:
    try:
        valor = float(monto)
    except (ValueError, TypeError):
        return False, "Monto inválido"
    if valor <= 0:
        return False, "Monto debe ser mayor a cero"
    if valor > 50_000_000:
        return False, "Monto excede el límite permitido (50 millones)"
    return True, None


def sanitizar_texto(texto: str) -> str:
    if not texto:
        return ""
    return re.sub(r'[\x00-\x1f\x7f-\x9f]', '', texto.strip())


def validar_datos_registro(
    nombre: str, numero: str, email: str, password: str
) -> Tuple[bool, Optional[str]]:
    for fn, args in [
        (validar_nombre, (nombre,)),
        (validar_numero_telefono, (numero,)),
        (validar_email, (email,)),
        (validar_password, (password,)),
    ]:
        ok, err = fn(*args)
        if not ok:
            return False, err
    return True, None


def validar_datos_transferencia(
    numero_destino: str, monto, mensaje: str = None
) -> Tuple[bool, Optional[str]]:
    ok, err = validar_numero_telefono(numero_destino)
    if not ok:
        return False, err
    ok, err = validar_monto(monto)
    if not ok:
        return False, err
    if mensaje and len(mensaje) > 200:
        return False, "Mensaje demasiado largo (máximo 200 caracteres)"
    return True, None
