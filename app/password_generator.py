"""
Generador de contraseñas seguras para usuarios de Office 365.

Este módulo genera contraseñas temporales que cumplen con
los requisitos de seguridad de Office 365.
"""

import secrets
import string


def generate_secure_password(length: int = 12) -> str:
    """
    Genera una contraseña segura y aleatoria.

    La contraseña incluye:
    - Letras mayúsculas
    - Letras minúsculas
    - Números
    - Símbolos seguros

    Evita caracteres ambiguos (0, O, l, 1, I) para facilitar
    su escritura manual.

    Args:
        length: Longitud de la contraseña (mínimo 8, recomendado 12)

    Returns:
        Contraseña generada

    Example:
        >>> password = generate_secure_password(12)
        >>> print(password)
        'Abc123$xyz89'
    """
    if length < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")

    # Definir caracteres permitidos (sin ambiguos)
    uppercase = 'ABCDEFGHJKLMNPQRSTUVWXYZ'  # Sin I, O
    lowercase = 'abcdefghjkmnpqrstuvwxyz'   # Sin l, o
    digits = '23456789'                      # Sin 0, 1
    symbols = '@#$%&*+=?'                    # Símbolos seguros y fáciles de escribir

    # Combinar todos los caracteres
    all_chars = uppercase + lowercase + digits + symbols

    # Generar contraseña asegurando al menos un carácter de cada tipo
    while True:
        password = ''.join(secrets.choice(all_chars) for _ in range(length))

        # Validar que tenga al menos un carácter de cada tipo
        has_upper = any(c in uppercase for c in password)
        has_lower = any(c in lowercase for c in password)
        has_digit = any(c in digits for c in password)
        has_symbol = any(c in symbols for c in password)

        if has_upper and has_lower and has_digit and has_symbol:
            return password


def generate_passwords(count: int, length: int = 12) -> list[str]:
    """
    Genera múltiples contraseñas únicas.

    Args:
        count: Cantidad de contraseñas a generar
        length: Longitud de cada contraseña

    Returns:
        Lista de contraseñas únicas

    Example:
        >>> passwords = generate_passwords(5)
        >>> len(passwords)
        5
    """
    passwords = set()

    while len(passwords) < count:
        passwords.add(generate_secure_password(length))

    return list(passwords)
