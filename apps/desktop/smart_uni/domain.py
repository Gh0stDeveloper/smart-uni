"""Dominio local del prototipo: datos de ejemplo, validación y claves heredadas.

La migración a Rust, autenticación remota y hashing nuevo NO se implementan aquí.
Se conservan los algoritmos/formato de almacenamiento JSON versión 1.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets

# Estos cursos y anuncios son de ejemplo para poder mostrar la aplicación.
# No estamos consultando información de una universidad real.
DEFAULT_COURSES = [
    {
        'id': 'PRO-101',
        'nombre': 'Programación I',
        'docente': 'Dra. Laura Torres',
        'progreso': 75,
        'dia': 'Lunes',
        'hora': '08:00–10:00',
        'aula': 'B-204',
    },
    {
        'id': 'MAT-201',
        'nombre': 'Matemáticas Discretas',
        'docente': 'Mtro. Miguel Ríos',
        'progreso': 62,
        'dia': 'Martes',
        'hora': '10:00–12:00',
        'aula': 'A-102',
    },
    {
        'id': 'BD-110',
        'nombre': 'Bases de Datos',
        'docente': 'Ing. Ana Moreno',
        'progreso': 88,
        'dia': 'Miércoles',
        'hora': '09:00–11:00',
        'aula': 'Lab-03',
    },
    {
        'id': 'DW-120',
        'nombre': 'Diseño Web',
        'docente': 'Mtra. Carla Gómez',
        'progreso': 50,
        'dia': 'Jueves',
        'hora': '12:00–14:00',
        'aula': 'Lab-01',
    },
]

DEFAULT_ANNOUNCEMENTS = [
    {
        'fecha': '05 nov',
        'titulo': 'Entrega de proyecto final',
        'detalle': 'Programación I · 23:59',
    },
    {
        'fecha': '10 nov',
        'titulo': 'Semana de evaluación',
        'detalle': 'Consulta tu horario de exámenes',
    },
    {
        'fecha': '16 nov',
        'titulo': 'Taller de innovación',
        'detalle': 'Auditorio central · 10:00',
    },
]


class ValidationError(ValueError):
    """Mostramos este error cuando los datos que escribimos no son válidos."""


def validate_email(email: str) -> str:
    """Limpiamos el correo y revisamos que tenga un formato válido."""
    value = email.strip().lower()

    if not re.fullmatch(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}', value):
        raise ValidationError('Introduce un correo institucional válido.')

    return value


def validate_student(
    name: str,
    email: str,
    career: str,
    password: str,
) -> tuple[str, str, str]:
    """Antes del registro comprobamos los cuatro campos del formulario."""
    clean_name = name.strip()
    clean_career = career.strip()
    email = validate_email(email)

    if len(clean_name) < 3:
        raise ValidationError('Escribe tu nombre completo (mínimo 3 caracteres).')

    if len(clean_career) < 3:
        raise ValidationError('Indica tu carrera.')

    if len(password) < 8:
        raise ValidationError('La contraseña debe tener al menos 8 caracteres.')

    return clean_name, email, clean_career


def hash_password(password: str) -> str:
    """Guardamos un hash de la contraseña en lugar de guardar la contraseña."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        260_000,
    )

    return f'pbkdf2_sha256$260000${salt.hex()}${digest.hex()}'


def verify_password(password: str, stored: str) -> bool:
    """Comparamos la contraseña escrita con el hash que ya estaba guardado."""
    try:
        algorithm, rounds, hex_salt, hex_digest = stored.split('$')

        if algorithm != 'pbkdf2_sha256':
            return False

        calculated = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            bytes.fromhex(hex_salt),
            int(rounds),
        )

        return hmac.compare_digest(calculated, bytes.fromhex(hex_digest))

    except (ValueError, AttributeError, TypeError):
        return False


