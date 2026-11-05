"""Aquí tenemos las funciones de SMART UNI y el guardado de datos en JSON.

Este archivo está separado de las pantallas para que podamos explicar la lógica
sin mezclarla con botones, colores o ventanas.
"""

from __future__ import annotations

import copy
import hashlib
import hmac
import json
import os
import re
import secrets
import tempfile
from pathlib import Path


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


class SmartUniService:
    """Este servicio conecta el registro, las consultas y el archivo JSON."""

    def __init__(self, json_path: str | Path):
        self.path = Path(json_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # La primera vez creamos el JSON con datos de ejemplo.
        # Si el archivo ya existe, no lo sobrescribimos.
        if not self.path.exists():
            self._write(
                {
                    'version': 1,
                    'students': [],
                    'courses': copy.deepcopy(DEFAULT_COURSES),
                    'announcements': copy.deepcopy(DEFAULT_ANNOUNCEMENTS),
                }
            )

    def _read(self) -> dict:
        """Cada vez que necesitamos datos, los leemos del archivo JSON."""
        try:
            with self.path.open('r', encoding='utf-8') as fh:
                data = json.load(fh)

            required_fields = ('students', 'courses', 'announcements')
            if not isinstance(data, dict) or not all(
                key in data for key in required_fields
            ):
                raise ValueError('Estructura JSON incompleta')

            return data

        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError(f'No se pudo leer la base JSON: {exc}') from exc

    def _write(self, data: dict) -> None:
        """Guardamos el JSON sin dejar el archivo a medias si algo se interrumpe."""
        # Primero lo escribimos en un archivo temporal y después lo reemplazamos.
        # Esto se conoce como escritura atómica.
        descriptor, temp_name = tempfile.mkstemp(
            prefix='.smartuni-',
            suffix='.json',
            dir=self.path.parent,
        )

        try:
            with os.fdopen(descriptor, 'w', encoding='utf-8') as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
                fh.write('\n')
                fh.flush()
                os.fsync(fh.fileno())

            os.replace(temp_name, self.path)

        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def register(
        self,
        name: str,
        email: str,
        career: str,
        password: str,
    ) -> dict:
        """Validamos, revisamos duplicados y guardamos al nuevo estudiante."""
        name, email, career = validate_student(name, email, career, password)
        data = self._read()

        if any(student['email'] == email for student in data['students']):
            raise ValidationError('Este correo ya está registrado.')

        student = {
            'name': name,
            'email': email,
            'career': career,
            'password_hash': hash_password(password),
        }

        data['students'].append(student)
        self._write(data)

        return {
            'name': name,
            'email': email,
            'career': career,
        }

    def authenticate(self, email: str, password: str) -> dict | None:
        """Buscamos al estudiante y comprobamos si sus datos coinciden."""
        email = validate_email(email)

        for student in self._read()['students']:
            if student['email'] == email and verify_password(
                password, student['password_hash']
            ):
                return {
                    key: student[key]
                    for key in ('name', 'email', 'career')
                }

        return None

    def courses(self, query: str = '') -> list[dict]:
        """Devolvemos todos los cursos o filtramos por materia o docente."""
        courses = self._read()['courses']
        key = query.strip().casefold()

        if not key:
            return courses

        return [
            course
            for course in courses
            if key in course['nombre'].casefold()
            or key in course['docente'].casefold()
        ]

    def schedule(self) -> list[dict]:
        """Ordenamos los cursos por día de la semana y por hora."""
        order = {
            'Lunes': 0,
            'Martes': 1,
            'Miércoles': 2,
            'Jueves': 3,
            'Viernes': 4,
            'Sábado': 5,
        }

        return sorted(
            self._read()['courses'],
            key=lambda course: (order.get(course['dia'], 99), course['hora']),
        )

    def announcements(self) -> list[dict]:
        """Obtenemos los avisos que vamos a mostrar en las pantallas."""
        return self._read()['announcements']

    def summary(self) -> dict:
        """Calculamos los números que aparecen arriba del panel principal."""
        courses = self.courses()

        return {
            'total_courses': len(courses),
            'average_progress': (
                round(sum(course['progreso'] for course in courses) / len(courses))
                if courses
                else 0
            ),
            'total_announcements': len(self.announcements()),
        }


def seed_demo(service: SmartUniService) -> None:
    """Creamos una cuenta de prueba para poder presentar la aplicación."""
    try:
        service.register(
            'Alex Rivera',
            'demo@smartuni.edu',
            'Ingeniería en Sistemas',
            'Demo1234!',
        )
    except ValidationError as exc:
        # Si ya se creó anteriormente, no queremos crearla dos veces.
        if 'ya está registrado' not in str(exc):
            raise
