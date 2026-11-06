"""Servicios de aplicación de SMART UNI; UI, dominio y almacenamiento separados.

Se preservan las importaciones públicas de la versión 1 y el JSON existente.
"""

from __future__ import annotations

import copy
from pathlib import Path

from .domain import (
    DEFAULT_ANNOUNCEMENTS, DEFAULT_COURSES, ValidationError,
    hash_password, validate_email, validate_student, verify_password,
)
from .repository import JsonRepository, RecordRepository


class SmartUniService:
    """Servicio de aplicación: casos de uso sobre un repositorio intercambiable."""

    def __init__(self, json_path: str | Path, repository: RecordRepository | None = None):
        initial_data = {
            'version': 1,
            'students': [],
            'courses': copy.deepcopy(DEFAULT_COURSES),
            'announcements': copy.deepcopy(DEFAULT_ANNOUNCEMENTS),
        }
        self.repository = repository if repository is not None else JsonRepository(json_path, initial_data)
        self.path = self.repository.path

    def _read(self) -> dict:
        """Compatibilidad con servicios y pruebas de la versión anterior."""
        return self.repository.read()

    def _write(self, data: dict) -> None:
        """Compatibilidad con servicios y pruebas de la versión anterior."""
        self.repository.write(data)

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
