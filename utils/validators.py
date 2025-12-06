# utils/validators.py - Validaciones de entrada

import re
from typing import Tuple, Optional


def validar_numero_telefono(numero: str) -> Tuple[bool, Optional[str]]:
    """
    Validar formato de número de teléfono colombiano
    
    Args:
        numero (str): Número de teléfono a validar
        
    Returns:
        Tuple[bool, Optional[str]]: (es_valido, mensaje_error)
    """
    if not numero:
        return False, "Número de teléfono es requerido"
    
    # Eliminar espacios y caracteres especiales
    numero_limpio = re.sub(r'[^\d]', '', numero)
    
    # Debe tener exactamente 10 dígitos
    if len(numero_limpio) != 10:
        return False, "Número de teléfono debe tener 10 dígitos"
    
    # Debe comenzar con 3 (celulares en Colombia)
    if not numero_limpio.startswith('3'):
        return False, "Número de teléfono debe comenzar con 3"
    
    return True, None


def validar_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validar formato de email
    
    Args:
        email (str): Email a validar
        
    Returns:
        Tuple[bool, Optional[str]]: (es_valido, mensaje_error)
    """
    if not email:
        return False, "Email es requerido"
    
    # Patrón básico de email
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(patron, email):
        return False, "Formato de email inválido"
    
    if len(email) > 254:
        return False, "Email demasiado largo"
    
    return True, None


def validar_password(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validar fortaleza de contraseña
    
    Args:
        password (str): Contraseña a validar
        
    Returns:
        Tuple[bool, Optional[str]]: (es_valido, mensaje_error)
    """
    if not password:
        return False, "Contraseña es requerida"
    
    if len(password) < 6:
        return False, "Contraseña debe tener al menos 6 caracteres"
    
    if len(password) > 128:
        return False, "Contraseña demasiado larga"
    
    # Opcional: Validaciones más estrictas
    # if not re.search(r'[A-Z]', password):
    #     return False, "Contraseña debe contener al menos una mayúscula"
    
    # if not re.search(r'[a-z]', password):
    #     return False, "Contraseña debe contener al menos una minúscula"
    
    # if not re.search(r'\d', password):
    #     return False, "Contraseña debe contener al menos un número"
    
    return True, None


def validar_nombre(nombre: str) -> Tuple[bool, Optional[str]]:
    """
    Validar nombre de usuario
    
    Args:
        nombre (str): Nombre a validar
        
    Returns:
        Tuple[bool, Optional[str]]: (es_valido, mensaje_error)
    """
    if not nombre:
        return False, "Nombre es requerido"
    
    nombre_limpio = nombre.strip()
    
    if len(nombre_limpio) < 2:
        return False, "Nombre debe tener al menos 2 caracteres"
    
    if len(nombre_limpio) > 100:
        return False, "Nombre demasiado largo"
    
    # Permitir letras, espacios, tildes y algunos caracteres especiales
    if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\'-]+$', nombre_limpio):
        return False, "Nombre contiene caracteres no válidos"
    
    return True, None


def validar_monto(monto) -> Tuple[bool, Optional[str]]:
    """
    Validar monto de transacción
    
    Args:
        monto: Monto a validar (puede ser str, int, float)
        
    Returns:
        Tuple[bool, Optional[str]]: (es_valido, mensaje_error)
    """
    try:
        monto_float = float(monto)
    except (ValueError, TypeError):
        return False, "Monto inválido"
    
    if monto_float <= 0:
        return False, "Monto debe ser mayor a cero"
    
    if monto_float > 50000000:  # Límite de 50 millones
        return False, "Monto excede el límite permitido (50 millones)"
    
    # Validar que tenga máximo 2 decimales
    if round(monto_float, 2) != monto_float:
        return False, "Monto solo puede tener hasta 2 decimales"
    
    return True, None


def validar_mensaje(mensaje: str) -> Tuple[bool, Optional[str]]:
    """
    Validar mensaje de transferencia (opcional)
    
    Args:
        mensaje (str): Mensaje a validar
        
    Returns:
        Tuple[bool, Optional[str]]: (es_valido, mensaje_error)
    """
    if not mensaje:
        return True, None  # Mensaje es opcional
    
    if len(mensaje) > 200:
        return False, "Mensaje demasiado largo (máximo 200 caracteres)"
    
    return True, None


def sanitizar_texto(texto: str) -> str:
    """
    Sanitizar texto para prevenir inyecciones
    
    Args:
        texto (str): Texto a sanitizar
        
    Returns:
        str: Texto sanitizado
    """
    if not texto:
        return ""
    
    # Eliminar caracteres peligrosos
    texto_limpio = texto.strip()
    
    # Eliminar caracteres de control y caracteres especiales peligrosos
    texto_limpio = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', texto_limpio)
    
    return texto_limpio


def validar_datos_registro(nombre: str, numero_telefono: str, email: str, password: str) -> Tuple[bool, Optional[str]]:
    """
    Validar todos los datos de registro en una sola función
    
    Args:
        nombre (str): Nombre del usuario
        numero_telefono (str): Número de teléfono
        email (str): Email
        password (str): Contraseña
        
    Returns:
        Tuple[bool, Optional[str]]: (es_valido, mensaje_error)
    """
    # Validar nombre
    valido, error = validar_nombre(nombre)
    if not valido:
        return False, error
    
    # Validar número de teléfono
    valido, error = validar_numero_telefono(numero_telefono)
    if not valido:
        return False, error
    
    # Validar email
    valido, error = validar_email(email)
    if not valido:
        return False, error
    
    # Validar password
    valido, error = validar_password(password)
    if not valido:
        return False, error
    
    return True, None


def validar_datos_transferencia(numero_destino: str, monto, mensaje: str = None) -> Tuple[bool, Optional[str]]:
    """
    Validar todos los datos de transferencia en una sola función
    
    Args:
        numero_destino (str): Número de teléfono destino
        monto: Monto a transferir
        mensaje (str, optional): Mensaje de la transferencia
        
    Returns:
        Tuple[bool, Optional[str]]: (es_valido, mensaje_error)
    """
    # Validar número destino
    valido, error = validar_numero_telefono(numero_destino)
    if not valido:
        return False, error
    
    # Validar monto
    valido, error = validar_monto(monto)
    if not valido:
        return False, error
    
    # Validar mensaje (opcional)
    if mensaje:
        valido, error = validar_mensaje(mensaje)
        if not valido:
            return False, error
    
    return True, None


# Exportar funciones
__all__ = [
    'validar_numero_telefono',
    'validar_email',
    'validar_password',
    'validar_nombre',
    'validar_monto',
    'validar_mensaje',
    'sanitizar_texto',
    'validar_datos_registro',
    'validar_datos_transferencia'
]