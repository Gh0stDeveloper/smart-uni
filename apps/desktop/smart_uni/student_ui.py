"""Pantallas nuevas de SMART UNI: mantenemos el estilo de la aplicación original.

Aquí organizamos el área del estudiante, sus materias y las acciones de cada
apartado. La lógica del archivo JSON se queda en student_data.py.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .core import ValidationError
from .student_data import SUBJECTS, StudentSpaceService
from .ui import COLORS, FONT_TEXT, FONT_TITLE, label


SIDEBAR = '#E9F3FF'
SOFT_BLUE = '#EAF4FF'
PALE_AQUA = '#EAF9FA'
GOLD = '#FFF1CE'
BORDER = '#DCE7F2'

MENU = [
    ('Inicio', 'Inicio'),
    ('Perfil', 'Perfil'),
    ('Amigos', 'Amigos'),
    ('Calendario', 'Calendario'),
    ('Material', 'Material'),
    ('Tareas', 'Tareas'),
    ('Apuntes', 'Apuntes'),
]


class StudentSpaceView:
    """Esta vista se abre desde el nuevo botón Mi espacio del menú original."""

    def __init__(self, app, parent, section='Inicio'):
        self.app = app
        self.parent = parent
        self.section = section if section in dict(MENU) else 'Inicio'
        self.service = StudentSpaceService(app.service)
        self.email = app.user['email']
        self.area = self.service.overview(self.email)
        self.subject_selected = None
        self._build()

    def _build(self):
        """Todo aparece dentro del área principal y sin una barra lateral extra.

        La navegación general ya está en la parte superior de la aplicación.
        Con esto recuperamos el espacio que antes ocupaba el menú repetido.
        """
        container = tk.Frame(self.parent, bg=COLORS['page'])
        container.pack(fill='both', expand=True)

        viewport = tk.Frame(container, bg=COLORS['page'])
        viewport.pack(side='left', fill='both', expand=True)

        canvas = tk.Canvas(viewport, bg=COLORS['page'], bd=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(
            viewport,
            orient='vertical',
            command=canvas.yview,
            width=9,
            relief='flat',
            bd=0,
            troughcolor=COLORS['page'],
            bg='#C6D9EF',
            activebackground=COLORS['blue'],
            highlightthickness=0,
        )
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        self.content = tk.Frame(canvas, bg=COLORS['page'])
        window_id = canvas.create_window((0, 0), window=self.content, anchor='nw')
        self.content.bind(
            '<Configure>',
            lambda _: canvas.configure(scrollregion=canvas.bbox('all')),
        )
        canvas.bind('<Configure>', lambda event: canvas.itemconfigure(window_id, width=event.width))

        def scroll(event):
            delta = -1 if (event.delta > 0 or event.num == 4) else 1
            canvas.yview_scroll(delta * 3, 'units')

        canvas.bind('<Enter>', lambda _: canvas.bind_all('<MouseWheel>', scroll))
        canvas.bind('<Leave>', lambda _: canvas.unbind_all('<MouseWheel>'))
        canvas.bind('<Enter>', lambda _: canvas.bind_all('<Button-4>', scroll), add='+')
        canvas.bind('<Enter>', lambda _: canvas.bind_all('<Button-5>', scroll), add='+')

        pages = {
            'Inicio': self.show_home,
            'Perfil': self.show_profile,
            'Amigos': self.show_friends,
            'Calendario': self.show_calendar,
            'Material': self.show_materials,
            'Tareas': self.show_tasks,
            'Apuntes': self.show_notes,
        }
        pages[self.section]()

    def heading(self, title, subtitle, action_label=None, command=None):
        row = tk.Frame(self.content, bg=COLORS['page'])
        row.pack(fill='x', pady=(0, 24))
        left = tk.Frame(row, bg=COLORS['page'])
        left.pack(side='left', fill='x', expand=True)
        label(left, title, 24, COLORS['ink'], True).pack(anchor='w')
        label(
            left,
            subtitle,
            10,
            COLORS['muted'],
            bg=COLORS['page'],
            wraplength=570,
            justify='left',
        ).pack(anchor='w', pady=(6, 0))

        if action_label and command:
            self.button(row, action_label, command).pack(side='right', padx=(10, 0))

    def card(self, parent=None, padding=18, bg='white'):
        return tk.Frame(
            parent or self.content,
            bg=bg,
            padx=padding,
            pady=padding,
            highlightbackground=BORDER,
            highlightthickness=1,
        )

    def button(self, parent, text, command, *, secondary=False, width=None):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=SOFT_BLUE if secondary else COLORS['blue'],
            fg=COLORS['blue'] if secondary else 'white',
            activebackground=COLORS['aqua'],
            activeforeground='white',
            font=(FONT_TEXT, 10, 'bold'),
            relief='flat',
            bd=0,
            cursor='hand2',
            padx=14,
            pady=9,
            width=width,
        )

    def text(self, parent, value, size=10, color=None, bold=False, **kwargs):
        return label(
            parent,
            value,
            size,
            color or COLORS['ink'],
            bold,
            bg=parent.cget('bg'),
            **kwargs,
        )

    def section_title(self, parent, title, detail=''):
        row = tk.Frame(parent, bg=parent.cget('bg'))
        row.pack(fill='x', pady=(0, 12))
        self.text(row, title, 14, bold=True).pack(side='left')

        if detail:
            self.text(row, detail, 9, COLORS['muted']).pack(side='right')

    def empty(self, parent, message):
        self.text(
            parent,
            message,
            10,
            COLORS['muted'],
            wraplength=440,
            justify='left',
        ).pack(anchor='w', pady=15)

    def line_item(self, parent, title, subtitle='', tag='', command=None):
        row = tk.Frame(parent, bg=parent.cget('bg'))
        row.pack(fill='x', pady=7)
        left = tk.Frame(row, bg=row.cget('bg'))
        left.pack(side='left', fill='x', expand=True)
        self.text(left, title, 11, bold=True, wraplength=400, justify='left').pack(anchor='w')

        if subtitle:
            self.text(left, subtitle, 9, COLORS['muted'], wraplength=410, justify='left').pack(
                anchor='w', pady=(4, 0)
            )

        if tag:
            self.text(row, tag, 10, COLORS['blue'], bold=True).pack(side='right', padx=(10, 0))

        if command:
            self.button(row, 'Abrir', command, secondary=True).pack(side='right', padx=6)

    def two_columns(self):
        layout = tk.Frame(self.content, bg=COLORS['page'])
        layout.pack(fill='both', expand=True)
        layout.columnconfigure(0, weight=1, uniform='columns')
        layout.columnconfigure(1, weight=1, uniform='columns')
        return layout

    def show_home(self):
        first = self.app.user['name'].split()[0]
        self.heading(
            f'Tu espacio, {first}',
            'Tu asistente académico: próximas fechas, materiales y apuntes en un solo lugar.',
        )

        counts = [
            ('Materias', str(len(SUBJECTS))),
            ('Tareas pendientes', str(sum(not task['done'] for task in self.area['tasks']))),
            ('Mis apuntes', str(len(self.area['notes']))),
        ]
        summary = tk.Frame(self.content, bg=COLORS['page'])
        summary.pack(fill='x', pady=(0, 20))

        for i, (title, value) in enumerate(counts):
            summary.columnconfigure(i, weight=1, uniform='summary')
            box = self.card(summary, padding=20)
            box.grid(row=0, column=i, sticky='nsew', padx=(0, 10) if i < 2 else 0)
            self.text(box, title, 9, COLORS['muted']).pack(anchor='w')
            self.text(box, value, 22, COLORS['blue'], True).pack(anchor='w', pady=(7, 0))

        layout = self.two_columns()
        left = tk.Frame(layout, bg=COLORS['page'])
        left.grid(row=0, column=0, sticky='nsew', padx=(0, 9))
        right = tk.Frame(layout, bg=COLORS['page'])
        right.grid(row=0, column=1, sticky='nsew', padx=(9, 0))

        exams = self.card(left)
        exams.pack(fill='x', pady=(0, 15))
        self.section_title(exams, 'Próximos exámenes')
        upcoming = sorted(
            (event for event in self.area['events']
             if event['category'] == 'Examen' and event['date'] >= date.today().isoformat()),
            key=lambda event: event['date'],
        )[:3]

        if not upcoming:
            self.empty(exams, 'Todavía no agregaste exámenes en el calendario.')

        for event in upcoming:
            self.line_item(exams, event['title'], 'Evaluación programada', event['date'])

        self.button(
            exams, '+ Agregar examen', lambda: self.event_form('Examen'), secondary=True
        ).pack(anchor='w', pady=(8, 0))

        notes = self.card(left)
        notes.pack(fill='x', pady=(0, 15))
        self.section_title(notes, 'Últimos apuntes')
        recent = list(reversed(self.area['notes']))[:3]

        if not recent:
            self.empty(notes, 'Tus apuntes aparecerán aquí cuando guardes el primero.')

        for note in recent:
            self.line_item(notes, note['title'], note['subject'])

        self.button(notes, 'Ver mis apuntes', lambda: self.app.show_student_space('Apuntes'), secondary=True).pack(
            anchor='w', pady=(8, 0)
        )

        reminders = self.card(right)
        reminders.pack(fill='x', pady=(0, 15))
        self.section_title(reminders, 'Recordatorios')
        pending = sorted(
            (task for task in self.area['tasks'] if not task['done']),
            key=lambda task: task['due_date'],
        )[:3]
        upcoming_other = sorted(
            (event for event in self.area['events']
             if event['category'] != 'Examen' and event['date'] >= date.today().isoformat()),
            key=lambda event: event['date'],
        )[:2]

        if not pending and not upcoming_other:
            self.empty(reminders, 'Aquí verás tus entregas y avisos del calendario.')

        for task in pending:
            self.line_item(reminders, task['title'], task['subject'], task['due_date'])

        for event in upcoming_other:
            self.line_item(reminders, event['title'], event['category'], event['date'])

        self.button(reminders, 'Consultar tareas', lambda: self.app.show_student_space('Tareas'), secondary=True).pack(
            anchor='w', pady=(8, 0)
        )

        tip = self.card(right, bg=PALE_AQUA)
        tip.pack(fill='x', pady=(0, 15))
        self.section_title(tip, 'Consejo del día')
        self.text(
            tip,
            'Organiza tus apuntes por materia y registra las fechas de entrega para tener todo a la mano.',
            11,
            wraplength=300,
            justify='left',
        ).pack(anchor='w')
        self.text(
            tip,
            'Consejo informativo. No es un chat con inteligencia artificial.',
            8,
            COLORS['muted'],
            wraplength=300,
            justify='left',
        ).pack(anchor='w', pady=(12, 0))

    def show_profile(self):
        self.heading('Mi perfil', 'Aquí podemos revisar nuestros datos y actualizar el nombre o la carrera.')
        card = self.card()
        card.pack(fill='x')
        for name, value in [
            ('Nombre completo', self.app.user['name']),
            ('Correo institucional', self.app.user['email']),
            ('Carrera', self.app.user['career']),
        ]:
            row = tk.Frame(card, bg='white')
            row.pack(fill='x', pady=10)
            self.text(row, name, 10, COLORS['muted']).pack(anchor='w')
            self.text(row, value, 13, bold=True).pack(anchor='w', pady=(4, 0))

        self.button(card, 'Editar perfil', self.edit_profile).pack(anchor='w', pady=(20, 0))

    def show_friends(self):
        self.heading(
            'Amigos',
            'Guarda tus compañeros y sus correos para tenerlos identificados.',
            '+ Agregar amigo',
            self.friend_form,
        )
        items = sorted(self.area['friends'], key=lambda item: item['name'].casefold())

        if not items:
            self.empty(self.content, 'Todavía no tienes compañeros guardados. Puedes agregar el primero.')

        for friend in items:
            row = self.card()
            row.pack(fill='x', pady=6)
            self.button(
                row,
                'Eliminar',
                lambda id=friend['id']: self.confirm_remove('friends', id),
                secondary=True,
            ).pack(side='right')
            self.text(row, friend['name'], 13, bold=True).pack(anchor='w')
            self.text(row, friend['contact'], 10, COLORS['muted']).pack(anchor='w', pady=(5, 0))

    def show_calendar(self):
        self.heading(
            'Calendario académico',
            'Registra exámenes, actividades y recordatorios para organizar tus fechas.',
            '+ Agregar evento',
            self.event_form,
        )
        self.text(
            self.content,
            'Las fechas que agregamos aquí también se muestran en el inicio del espacio estudiantil.',
            10,
            COLORS['muted'],
            wraplength=650,
            justify='left',
        ).pack(anchor='w', pady=(0, 15))

        events = sorted(self.area['events'], key=lambda event: event['date'])
        if not events:
            self.empty(self.content, 'No hay fechas registradas todavía.')

        for event in events:
            row = self.card()
            row.pack(fill='x', pady=6)
            self.button(row, 'Eliminar', lambda id=event['id']: self.confirm_remove('events', id), secondary=True).pack(side='right')
            badge = 'EXAMEN' if event['category'] == 'Examen' else event['category'].upper()
            self.text(row, f"{event['date']}    ·    {badge}", 9, COLORS['blue'], True).pack(anchor='w')
            self.text(row, event['title'], 12, bold=True).pack(anchor='w', pady=(5, 0))
            if event.get('description'):
                self.text(row, event['description'], 10, COLORS['muted']).pack(anchor='w', pady=(3, 0))

    def show_tasks(self):
        self.heading('Mis tareas', 'Registra las entregas y marca las que ya terminaste.', '+ Nueva tarea', self.task_form)
        tasks = sorted(self.area['tasks'], key=lambda task: (task['done'], task['due_date']))
        if not tasks:
            self.empty(self.content, 'Todavía no tienes tareas. Agrega una para empezar.')

        for task in tasks:
            row = self.card()
            row.pack(fill='x', pady=6)
            self.button(row, 'Eliminar', lambda id=task['id']: self.confirm_remove('tasks', id), secondary=True).pack(side='right')
            self.button(
                row,
                'Desmarcar' if task['done'] else 'Terminar',
                lambda id=task['id']: self.run_action(
                    lambda: self.service.toggle_task(self.email, id), 'Tareas'
                ),
                secondary=task['done'],
            ).pack(side='right', padx=(0, 7))
            name = f"✓  {task['title']}" if task['done'] else task['title']
            self.text(row, name, 12, COLORS['muted'] if task['done'] else COLORS['ink'], True).pack(anchor='w')
            self.text(row, f"{task['subject']}  ·  Entrega: {task['due_date']}", 10, COLORS['muted']).pack(anchor='w', pady=(4, 0))

    def show_notes(self):
        self.heading('Mis apuntes', 'Escribe tus notas y consúltalas por materia.', '+ Nuevo apunte', self.note_form)
        notes = list(reversed(self.area['notes']))
        if not notes:
            self.empty(self.content, 'No hay apuntes todavía. Puedes crear el primero.')

        for note in notes:
            row = self.card()
            row.pack(fill='x', pady=6)
            self.button(row, 'Eliminar', lambda id=note['id']: self.confirm_remove('notes', id), secondary=True).pack(side='right')
            self.button(row, 'Ver / Editar', lambda n=note: self.note_form(n)).pack(side='right', padx=(0, 7))
            self.text(row, note['title'], 12, bold=True).pack(anchor='w')
            self.text(row, f"{note['subject']}  ·  {note['created_at']}", 9, COLORS['muted']).pack(anchor='w', pady=(4, 0))
            preview = note['content'].replace('\n', ' ')
            self.text(row, preview[:120] + ('…' if len(preview) > 120 else ''), 10, COLORS['muted'], wraplength=450).pack(anchor='w', pady=(5, 0))

    def show_materials(self):
        self.heading('Material de estudio', 'Tus ocho materias, organizadas en carpetas como en el diseño de referencia.')
        self.text(
            self.content,
            'Selecciona una carpeta para consultar o agregar PDF, documentos, imágenes y presentaciones.',
            10,
            COLORS['muted'],
            wraplength=600,
            justify='left',
        ).pack(anchor='w', pady=(0, 17))

        subjects = tk.Frame(self.content, bg=COLORS['page'])
        subjects.pack(fill='x')
        for i in range(2):
            subjects.columnconfigure(i, weight=1, uniform='subjects')

        for index, name in enumerate(SUBJECTS):
            count = sum(material['subject'] == name for material in self.area['materials'])
            folder = self.card(subjects, padding=14, bg=SOFT_BLUE)
            folder.grid(
                row=index // 2,
                column=index % 2,
                sticky='nsew',
                padx=(0, 10) if index % 2 == 0 else (10, 0),
                pady=7,
            )
            # Dibujamos una carpeta con formas nativas de Tkinter.
            # Así mantenemos el mismo diseño en Windows y Linux.
            icon = tk.Canvas(
                folder,
                width=85,
                height=59,
                bg=SOFT_BLUE,
                bd=0,
                highlightthickness=0,
            )
            icon.pack(anchor='w')
            icon.create_polygon(
                6, 13, 34, 13, 43, 22, 77, 22, 77, 52, 6, 52,
                fill='#E6A139',
                outline='',
            )
            icon.create_rectangle(6, 25, 79, 54, fill='#FFD477', outline='')
            icon.create_line(10, 27, 75, 27, fill='#FFE7AA', width=2)
            self.text(folder, name, 11, bold=True, wraplength=225, justify='left').pack(anchor='w', pady=(3, 4))
            self.text(folder, f'{count} archivo(s)', 9, COLORS['muted']).pack(anchor='w')
            self.button(folder, 'Abrir carpeta', lambda s=name: self.show_subject(s), secondary=True).pack(
                anchor='w', pady=(10, 0)
            )

    def show_subject(self, subject):
        # Mostramos una sola carpeta: quitamos primero el listado anterior.
        for widget in self.content.winfo_children():
            widget.destroy()

        self.heading(
            subject,
            'Documentos guardados dentro de esta materia.',
            '+ Agregar archivo',
            lambda: self.import_material(subject),
        )
        self.button(self.content, '← Volver a carpetas', lambda: self.app.show_student_space('Material'), secondary=True).pack(
            anchor='w', pady=(0, 12)
        )
        materials = [item for item in self.area['materials'] if item['subject'] == subject]
        if not materials:
            self.empty(self.content, 'Esta carpeta está vacía. Puedes importar un archivo de tu computadora.')

        for item in materials:
            row = self.card()
            row.pack(fill='x', pady=6)
            self.button(row, 'Eliminar', lambda id=item['id']: self.remove_material(id), secondary=True).pack(side='right')
            self.button(row, 'Abrir', lambda id=item['id']: self.open_material(id)).pack(side='right', padx=(0, 7))
            self.text(row, item['title'], 11, bold=True, wraplength=400, justify='left').pack(anchor='w')

    def new_dialog(self, title, width=490, height=420):
        dialog = tk.Toplevel(self.app)
        dialog.title(f'{title} | Smart Uni')
        dialog.geometry(f'{width}x{height}')
        dialog.minsize(width, height)
        dialog.resizable(False, False)
        dialog.transient(self.app)
        dialog.grab_set()
        dialog.configure(bg='white')
        form = tk.Frame(dialog, bg='white', padx=28, pady=23)
        form.pack(fill='both', expand=True)
        self.text(form, title, 18, bold=True).pack(anchor='w', pady=(0, 15))
        return dialog, form

    def entry(self, parent, title, value=''):
        self.text(parent, title, 10, bold=True).pack(anchor='w', pady=(7, 4))
        entry = tk.Entry(
            parent,
            font=(FONT_TEXT, 11),
            fg=COLORS['ink'],
            bg='#F3F7FC',
            relief='flat',
            highlightthickness=1,
            highlightbackground=BORDER,
        )
        entry.pack(fill='x', ipady=7)
        entry.insert(0, value)
        return entry

    def combo(self, parent, title, values, selected=None):
        self.text(parent, title, 10, bold=True).pack(anchor='w', pady=(7, 4))
        widget = ttk.Combobox(parent, values=values, state='readonly', font=(FONT_TEXT, 10))
        widget.set(selected or values[0])
        widget.pack(fill='x', ipady=3)
        return widget

    def save_dialog(self, dialog, form, command, section):
        def save():
            try:
                command()
                dialog.destroy()
                self.app.show_student_space(section)
            except (ValidationError, OSError) as exc:
                messagebox.showerror('No se pudo guardar', str(exc), parent=dialog)

        self.button(form, 'Guardar cambios', save).pack(anchor='e', pady=(20, 0))

    def run_action(self, operation, section):
        try:
            operation()
            self.app.show_student_space(section)
        except (ValidationError, OSError) as exc:
            messagebox.showerror('No se pudo completar', str(exc), parent=self.app)

    def confirm_remove(self, section, item_id):
        if messagebox.askyesno('Confirmar', '¿Quieres eliminar este elemento?', parent=self.app):
            self.run_action(lambda: self.service.remove(self.email, section, item_id), self.section)

    def friend_form(self):
        dialog, form = self.new_dialog('Agregar compañero', height=310)
        name = self.entry(form, 'Nombre')
        contact = self.entry(form, 'Correo')
        self.save_dialog(dialog, form, lambda: self.service.add_friend(self.email, name.get(), contact.get()), 'Amigos')

    def event_form(self, category='Evento'):
        dialog, form = self.new_dialog('Nuevo evento', height=455)
        name = self.entry(form, 'Título del evento')
        day = self.entry(form, 'Fecha (AAAA-MM-DD)', date.today().isoformat())
        kind = self.combo(form, 'Tipo', ['Evento', 'Examen', 'Recordatorio'], category)
        description = self.entry(form, 'Descripción (opcional)')
        self.save_dialog(
            dialog,
            form,
            lambda: self.service.add_event(
                self.email, name.get(), day.get(), kind.get(), description.get()
            ),
            'Calendario',
        )

    def task_form(self):
        dialog, form = self.new_dialog('Nueva tarea', height=410)
        title = self.entry(form, 'Tarea')
        subject = self.combo(form, 'Materia', SUBJECTS)
        due = self.entry(form, 'Fecha de entrega (AAAA-MM-DD)', date.today().isoformat())
        self.save_dialog(
            dialog,
            form,
            lambda: self.service.add_task(self.email, title.get(), subject.get(), due.get()),
            'Tareas',
        )

    def note_form(self, note=None):
        dialog, form = self.new_dialog('Editar apunte' if note else 'Nuevo apunte', 520, 540)
        title = self.entry(form, 'Título', note['title'] if note else '')

        if note:
            self.text(form, f"Materia: {note['subject']}", 10, COLORS['muted']).pack(anchor='w', pady=9)
            subject = None
        else:
            subject = self.combo(form, 'Materia', SUBJECTS)

        self.text(form, 'Contenido', 10, bold=True).pack(anchor='w', pady=(12, 5))
        content = tk.Text(form, font=(FONT_TEXT, 11), wrap='word', height=10, relief='flat', bg='#F3F7FC', fg=COLORS['ink'])
        content.pack(fill='both', expand=True)
        if note:
            content.insert('1.0', note['content'])

        if note:
            operation = lambda: self.service.update_note(
                self.email, note['id'], title.get(), content.get('1.0', 'end').strip()
            )
        else:
            operation = lambda: self.service.add_note(
                self.email, title.get(), subject.get(), content.get('1.0', 'end').strip()
            )

        self.save_dialog(dialog, form, operation, 'Apuntes')

    def edit_profile(self):
        dialog, form = self.new_dialog('Editar mi perfil', height=325)
        name = self.entry(form, 'Nombre completo', self.app.user['name'])
        career = self.entry(form, 'Carrera', self.app.user['career'])

        def update():
            self.app.user = self.service.update_profile(self.email, name.get(), career.get())

        self.save_dialog(dialog, form, update, 'Perfil')

    def import_material(self, subject):
        path = filedialog.askopenfilename(
            parent=self.app,
            title=f'Archivo para {subject}',
            filetypes=[
                ('Archivos de estudio', '*.pdf *.txt *.md *.docx *.xlsx *.pptx *.csv *.png *.jpg *.jpeg'),
                ('Todos los archivos', '*.*'),
            ],
        )
        if not path:
            return

        try:
            self.service.add_material(self.email, subject, path)
            self.app.show_student_space('Material')
            messagebox.showinfo('Archivo guardado', f'El archivo se guardó en la carpeta {subject}.', parent=self.app)
        except (ValidationError, OSError) as exc:
            messagebox.showerror('No se pudo importar', str(exc), parent=self.app)

    def open_material(self, item_id):
        try:
            path = self.service.material_path(self.email, item_id)
            if sys.platform == 'win32':
                os.startfile(str(path))
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', str(path)])
            else:
                subprocess.Popen(['xdg-open', str(path)])
        except (ValidationError, OSError) as exc:
            messagebox.showerror('No se pudo abrir', str(exc), parent=self.app)

    def remove_material(self, item_id):
        if messagebox.askyesno('Eliminar archivo', '¿Quieres eliminar este documento guardado?', parent=self.app):
            self.run_action(lambda: self.service.delete_material(self.email, item_id), 'Material')
