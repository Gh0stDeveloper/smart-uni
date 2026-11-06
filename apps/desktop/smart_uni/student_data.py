"""Datos del espacio estudiantil: cada cuenta mantiene sus propios apartados.

Esta parte no crea ventanas. Aquí guardamos amigos, tareas, eventos, apuntes
 y materiales en el mismo JSON que ya utilizaba SMART UNI.
"""

from __future__ import annotations

import copy
import re
import shutil
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

from .core import SmartUniService, ValidationError, validate_email


# Son las ocho carpetas que aparecen en el diseño de referencia.
# No agregamos estas materias al horario original porque son otro catálogo.
SUBJECTS = [
    'Cálculo',
    'Actividad Estudiantil',
    'Habilidades de Comunicación',
    'Maquetación',
    'Historia de Identidad Nacional',
    'Programa Estructurado',
    'Proyecto Integrador',
    'Fundamentos de Informática',
]

VALID_FILE_EXTENSIONS = {
    '.pdf', '.txt', '.md', '.docx', '.xlsx', '.pptx',
    '.csv', '.png', '.jpg', '.jpeg',
}


def new_space() -> dict:
    """Creamos los apartados vacíos cuando un alumno entra por primera vez."""
    return {
        'friends': [],
        'events': [],
        'tasks': [],
        'notes': [],
        'materials': [],
    }


def check_date(value: str) -> str:
    """Las fechas se escriben en formato año-mes-día para ordenarlas bien."""
    value = value.strip()

    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ValidationError('Escribe la fecha como AAAA-MM-DD.') from exc


def required_text(value: str, label: str, max_length: int = 500) -> str:
    value = value.strip()

    if not value:
        raise ValidationError(f'Escribe {label}.')

    if len(value) > max_length:
        raise ValidationError(f'{label.capitalize()} es demasiado largo.')

    return value


class StudentSpaceService:
    """Separamos los datos de cada estudiante utilizando su correo."""

    def __init__(self, base: SmartUniService):
        self.base = base

    def _read_space(self, email: str) -> dict:
        data = self.base._read()
        email = validate_email(email)

        if not any(student['email'] == email for student in data['students']):
            raise ValidationError('No encontramos la cuenta del estudiante.')

        stored = data.get('student_spaces', {}).get(email, {})
        area = new_space()

        for key in area:
            if isinstance(stored.get(key), list):
                area[key] = stored[key]

        return copy.deepcopy(area)

    def overview(self, email: str) -> dict:
        """Leemos una copia, para evitar cambiar el JSON por accidente."""
        return self._read_space(email)

    def _change(self, email: str, section: str, operation, *,
                event_type=None, event_payload=None, entity_id=None):
        """SQLCipher usa transacción con outbox; JSON retiene su flujo original."""
        email = validate_email(email)

        def mutate(data):
            if not any(student['email'] == email for student in data['students']):
                raise ValidationError('No encontramos la cuenta del estudiante.')
            spaces = data.setdefault('student_spaces', {})
            space = spaces.setdefault(email, new_space())
            space.setdefault(section, [])
            return operation(space[section])

        from .secure_storage import EncryptedSQLiteRepository
        if isinstance(self.base.repository, EncryptedSQLiteRepository) and event_type:
            from .offline_queue import OfflineOutbox, make_message
            message = make_message(
                event_type, email,
                event_payload if event_payload is not None else {"section": section},
                entity_id=entity_id,
            )
            inserted, result = OfflineOutbox(self.base.repository).apply(message, mutate)
            if not inserted:
                raise RuntimeError('ID inesperadamente repetido al guardar el cambio.')
            return result

        data = self.base._read()
        result = mutate(data)
        self.base._write(data)
        return result

    def _add(self, email: str, section: str, values: dict) -> dict:
        item = {'id': uuid.uuid4().hex, **values}
        event = {
            'friends': 'friends.add',
            'events': 'events.create',
            'tasks': 'tasks.create',
            'notes': 'notes.create',
            'materials': 'materials.import',
        }.get(section)
        self._change(
            email, section, lambda items: items.append(item),
            event_type=event, event_payload={'section': section, 'item': item},
            entity_id=item['id'],
        )
        return item

    def remove(self, email: str, section: str, item_id: str) -> bool:
        """Solo eliminamos elementos de una sección reconocida."""
        if section not in new_space():
            raise ValidationError('Este apartado no existe.')

        def remove_item(items):
            before = len(items)
            items[:] = [item for item in items if item['id'] != item_id]
            return before != len(items)

        event = {'notes': 'notes.delete', 'materials': 'materials.delete'}.get(section)
        return self._change(
            email, section, remove_item,
            event_type=event,
            event_payload={'section': section, 'item_id': item_id},
            entity_id=item_id,
        )

    def add_friend(self, email: str, name: str, contact: str) -> dict:
        name = required_text(name, 'el nombre del compañero', 100)
        contact = required_text(contact, 'su correo', 150)
        contact = validate_email(contact)

        if contact == validate_email(email):
            raise ValidationError('No necesitas agregarte como amigo.')

        if any(friend['contact'] == contact for friend in self.overview(email)['friends']):
            raise ValidationError('Ese compañero ya está en tu lista.')

        return self._add(email, 'friends', {'name': name, 'contact': contact})

    def add_event(
        self,
        email: str,
        title: str,
        day: str,
        category: str = 'Evento',
        description: str = '',
    ) -> dict:
        title = required_text(title, 'el nombre del evento', 120)
        day = check_date(day)

        if category not in ('Examen', 'Recordatorio', 'Evento'):
            raise ValidationError('Elige un tipo de evento válido.')

        return self._add(
            email,
            'events',
            {
                'title': title,
                'date': day,
                'category': category,
                'description': description.strip()[:300],
            },
        )

    def add_task(
        self,
        email: str,
        title: str,
        subject: str,
        due_date: str,
    ) -> dict:
        title = required_text(title, 'el nombre de la tarea', 120)

        if subject not in SUBJECTS:
            raise ValidationError('Selecciona una de las materias disponibles.')

        return self._add(
            email,
            'tasks',
            {
                'title': title,
                'subject': subject,
                'due_date': check_date(due_date),
                'done': False,
            },
        )

    def toggle_task(self, email: str, item_id: str) -> bool:
        """Al marcar la tarea también guardamos su estado en el JSON."""
        def change(items):
            for item in items:
                if item['id'] == item_id:
                    item['done'] = not item['done']
                    return item['done']

            raise ValidationError('No encontramos esa tarea.')

        return self._change(
            email, 'tasks', change,
            event_type='tasks.toggle',
            event_payload={'item_id': item_id},
            entity_id=item_id,
        )

    def add_note(self, email: str, title: str, subject: str, content: str) -> dict:
        title = required_text(title, 'el título del apunte', 120)
        content = required_text(content, 'el contenido del apunte', 10000)

        if subject not in SUBJECTS:
            raise ValidationError('Selecciona una de las materias disponibles.')

        return self._add(
            email,
            'notes',
            {
                'title': title,
                'subject': subject,
                'content': content,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
            },
        )

    def update_note(self, email: str, note_id: str, title: str, content: str):
        title = required_text(title, 'el título del apunte', 120)
        content = required_text(content, 'el contenido del apunte', 10000)

        def change(items):
            for item in items:
                if item['id'] == note_id:
                    item['title'] = title
                    item['content'] = content
                    return

            raise ValidationError('No encontramos ese apunte.')

        self._change(
            email, 'notes', change,
            event_type='notes.update',
            event_payload={'item_id': note_id, 'title': title, 'content': content},
            entity_id=note_id,
        )

    def add_material(self, email: str, subject: str, source: str) -> dict:
        """El modo seguro no genera copias de materiales sin cifrar."""
        from .secure_storage import EncryptedSQLiteRepository
        if isinstance(self.base.repository, EncryptedSQLiteRepository):
            raise ValidationError(
                'La importación de archivos cifrados está pendiente. '
                'No se guardará ninguna copia sin protección.'
            )
        if subject not in SUBJECTS:
            raise ValidationError('Selecciona una de las materias disponibles.')

        file_path = Path(source)

        if not file_path.is_file():
            raise ValidationError('El archivo seleccionado no existe.')

        if file_path.suffix.lower() not in VALID_FILE_EXTENSIONS:
            raise ValidationError('Selecciona un documento o imagen compatible.')

        if file_path.stat().st_size > 30 * 1024 * 1024:
            raise ValidationError('El archivo no puede superar los 30 MB.')

        item_id = uuid.uuid4().hex
        directory = self.base.path.parent / 'materiales'
        directory.mkdir(parents=True, exist_ok=True)
        saved_name = f'{item_id}{file_path.suffix.lower()}'
        destination = directory / saved_name
        shutil.copy2(file_path, destination)

        try:
            item = self._add(
                email,
                'materials',
                {
                    'subject': subject,
                    'title': file_path.name,
                    'file': saved_name,
                },
            )
        except Exception:
            destination.unlink(missing_ok=True)
            raise

        return item

    def material_path(self, email: str, item_id: str) -> Path:
        """La carpeta del material está controlada por la aplicación."""
        from .secure_storage import EncryptedSQLiteRepository
        if isinstance(self.base.repository, EncryptedSQLiteRepository):
            raise ValidationError('Los adjuntos heredados no están cifrados; acceso bloqueado.')
        item = next(
            (entry for entry in self.overview(email)['materials'] if entry['id'] == item_id),
            None,
        )

        if item is None:
            raise ValidationError('No encontramos ese material.')

        filename = item.get('file', '')
        if not re.fullmatch(r'[0-9a-f]{32}\.[a-z0-9]+', filename):
            raise ValidationError('La ruta del material no es válida.')

        file_path = self.base.path.parent / 'materiales' / filename

        if not file_path.is_file():
            raise ValidationError('No encontramos el documento guardado.')

        return file_path

    def delete_material(self, email: str, item_id: str) -> bool:
        file_path = self.material_path(email, item_id)
        removed = self.remove(email, 'materials', item_id)

        if removed:
            file_path.unlink(missing_ok=True)

        return removed

    def update_profile(self, email: str, name: str, career: str) -> dict:
        """Cambiamos solamente los datos públicos de la cuenta ya iniciada."""
        name = required_text(name, 'tu nombre completo', 100)
        career = required_text(career, 'tu carrera', 100)
        email = validate_email(email)

        def change(data):
            for student in data['students']:
                if student['email'] == email:
                    student['name'] = name
                    student['career'] = career
                    return {'name': name, 'email': email, 'career': career}
            raise ValidationError('No encontramos la cuenta del estudiante.')

        from .secure_storage import EncryptedSQLiteRepository
        if isinstance(self.base.repository, EncryptedSQLiteRepository):
            from .offline_queue import OfflineOutbox, make_message
            message = make_message('profile.update', email, {'name': name, 'career': career})
            return OfflineOutbox(self.base.repository).apply(message, change)[1]
        data = self.base._read()
        result = change(data)
        self.base._write(data)
        return result


def seed_student_demo(space: StudentSpaceService):
    """Estos datos ilustrativos son únicamente para el usuario de demostración."""
    email = 'demo@smartuni.edu'

    data = space.base._read()
    existing = data.get('student_spaces', {}).get(email, {})

    # Lo hacemos una sola vez. Si después borramos los ejemplos, no vuelven.
    if existing.get('_demo_initialized') or any(
        existing.get(section) for section in ('events', 'tasks', 'notes')
    ):
        return

    today = date.today()
    space.add_event(email, 'Examen de Cálculo', (today + timedelta(days=7)).isoformat(), 'Examen')
    space.add_event(email, 'Examen de Programación', (today + timedelta(days=11)).isoformat(), 'Examen')
    space.add_event(email, 'Inscripción académica', (today + timedelta(days=14)).isoformat(), 'Recordatorio')
    space.add_task(email, 'Entregar ejercicio de Cálculo', 'Cálculo', (today + timedelta(days=5)).isoformat())
    space.add_task(email, 'Avanzar proyecto integrador', 'Proyecto Integrador', (today + timedelta(days=9)).isoformat())
    space.add_note(email, 'Resumen de álgebra', 'Cálculo', 'Aquí podemos escribir las fórmulas y ejemplos de la clase.')
    space.add_note(email, 'Redes y conceptos', 'Fundamentos de Informática', 'Apunte de ejemplo para enseñar cómo funciona esta sección.')

    # Dejamos una marca para que los ejemplos no se restauren al reiniciar.
    data = space.base._read()
    data['student_spaces'][email]['_demo_initialized'] = True
    space.base._write(data)

