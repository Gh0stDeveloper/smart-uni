"""Aquí están las pantallas de SMART UNI, hechas con Tkinter.

Dejamos las pantallas en este archivo y las funciones del sistema en core.py.
Así podemos explicar cada parte por separado cuando mostremos el código.
"""

from __future__ import annotations

import tkinter as tk
import sys
from tkinter import messagebox
from pathlib import Path

from .core import SmartUniService, ValidationError
from .session import SessionState


# Roles de color y tipografía desde los tokens aprobados.
from .design_system import COLORS, FONT_TITLE, FONT_TEXT


def label(parent, text, size=12, color=None, bold=False, bg=None, **kwargs):
    """Creamos los textos que aparecen en las pantallas."""
    return tk.Label(
        parent,
        text=text,
        font=(
            FONT_TITLE if bold else FONT_TEXT,
            size,
            'bold' if bold else 'normal',
        ),
        fg=color or COLORS['ink'],
        bg=bg or parent.cget('bg'),
        **kwargs,
    )


def action(
    parent,
    text,
    command,
    *,
    background=None,
    foreground='white',
    width=20,
    height=2,
):
    """Creamos un botón y le indicamos qué función debe ejecutar."""
    return tk.Button(
        parent,
        text=text,
        command=command,
        font=(FONT_TEXT, 11, 'bold'),
        bg=background or COLORS['blue'],
        fg=foreground,
        activebackground='#1E65C1',
        activeforeground='white',
        relief='flat',
        bd=0,
        width=width,
        height=height,
        cursor='hand2',
    )


def field(parent, *, password=False):
    """Creamos los campos para escribir correo, contraseña y otros datos."""
    control = tk.Entry(
        parent,
        font=(FONT_TEXT, 12),
        bg='white',
        fg=COLORS['ink'],
        insertbackground=COLORS['ink'],
        show='•' if password else '',
        relief='flat',
        bd=0,
        highlightthickness=1,
        highlightbackground=COLORS['line'],
        highlightcolor=COLORS['blue'],
    )

    return control


class SmartUniApp(tk.Tk):
    """Ventana principal: desde aquí mostramos las diferentes pantallas."""

    def __init__(self, service: SmartUniService):
        super().__init__()
        self.service = service
        self._session = SessionState()

        self.title('Smart Uni | Plataforma Académica')
        self.geometry('1260x840')
        self.minsize(1000, 680)
        self._set_original_icon()
        self.configure(bg=COLORS['page'])
        self.show_login()

    @property
    def user(self) -> dict | None:
        """Interfaz de compatibilidad para las pantallas actuales."""
        return self._session.user

    @user.setter
    def user(self, account: dict | None) -> None:
        self._session.set_user(account)

    def _set_original_icon(self):
        """Usamos el birrete original, no una letra como icono."""
        root = Path(
            getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent)
        )
        icon = root / 'design' / 'previews' / '00_isotipo_smart_uni.png'
        if icon.is_file():
            try:
                self._icon_image = tk.PhotoImage(file=str(icon))
                self.iconphoto(True, self._icon_image)
            except tk.TclError:
                pass

    def _navigation_entries(self):
        """Todas las pantallas están en un solo menú, sin barras duplicadas."""
        return [
            ('GENERAL', [
                ('Panel principal', self.show_dashboard),
                ('Cursos', self.show_courses),
                ('Horario', self.show_schedule),
                ('Anuncios', self.show_announcements),
            ]),
            ('MI ESPACIO', [
                ('Inicio académico', lambda: self.show_student_space('Inicio')),
                ('Perfil', lambda: self.show_student_space('Perfil')),
                ('Amigos', lambda: self.show_student_space('Amigos')),
                ('Calendario', lambda: self.show_student_space('Calendario')),
                ('Material', lambda: self.show_student_space('Material')),
                ('Tareas', lambda: self.show_student_space('Tareas')),
                ('Apuntes', lambda: self.show_student_space('Apuntes')),
            ]),
        ]

    def _toggle_navigation(self):
        """El botón de las tres líneas abre o cierra la navegación."""
        if self._nav_open:
            self._navigation.pack_forget()
        else:
            self._navigation.pack(side='left', fill='y', before=self._content_holder)
        self._nav_open = not self._nav_open
        self._hamburger.configure(text='✕' if self._nav_open else '☰')

    def clear(self):
        """Quitamos la pantalla anterior antes de mostrar la siguiente."""
        for widget in self.winfo_children():
            widget.destroy()

    def brand(self, parent, large=False):
        """Dibujamos el símbolo de SMART UNI y colocamos su nombre."""
        line = tk.Frame(parent, bg=parent.cget('bg'))

        tk.Canvas(
            line,
            width=54 if large else 38,
            height=54 if large else 38,
            bg=parent.cget('bg'),
            bd=0,
            highlightthickness=0,
        ).pack(side='left', padx=(0, 11))

        canvas = line.winfo_children()[0]
        k = 1.25 if large else 0.9

        canvas.create_polygon(
            3 * k, 20 * k,
            24 * k, 7 * k,
            45 * k, 20 * k,
            24 * k, 33 * k,
            fill=COLORS['blue'],
            outline='',
        )
        canvas.create_rectangle(
            15 * k, 28 * k,
            33 * k, 32 * k,
            fill=COLORS['aqua'],
            outline='',
        )
        canvas.create_line(
            39 * k, 22 * k,
            39 * k, 36 * k,
            width=3,
            fill=COLORS['aqua'],
        )

        label(
            line,
            'SMART UNI',
            22 if large else 16,
            COLORS['blue'],
            True,
        ).pack(side='left')

        return line

    def show_login(self):
        """Aquí mostramos el inicio de sesión y revisamos las credenciales."""
        self.clear()

        backdrop = tk.Frame(self, bg=COLORS['login_bg'])
        backdrop.pack(fill='both', expand=True)

        card = tk.Frame(
            backdrop,
            bg='white',
            padx=45,
            pady=37,
            highlightbackground='#C5E0EF',
            highlightthickness=1,
        )
        card.place(
            relx=0.5,
            rely=0.5,
            anchor='center',
            width=460,
            height=590,
        )

        self.brand(card, True).pack(anchor='center', pady=(0, 20))
        label(card, 'Inicia sesión', 23, bold=True).pack(pady=(0, 6))
        label(
            card,
            'Bienvenido a tu espacio académico',
            11,
            COLORS['muted'],
        ).pack(pady=(0, 26))

        label(card, 'Correo institucional', 11, bold=True).pack(
            anchor='w',
            pady=(0, 7),
        )
        email = field(card)
        email.pack(fill='x', ipady=10)

        label(card, 'Contraseña', 11, bold=True).pack(
            anchor='w',
            pady=(18, 7),
        )
        password = field(card, password=True)
        password.pack(fill='x', ipady=10)

        def login(*_):
            # El servicio comprueba los datos; aquí solo decidimos qué mostrar.
            try:
                user = self.service.authenticate(email.get(), password.get())

                if not user:
                    raise ValidationError('Correo o contraseña incorrectos.')

                self.user = user
                self.show_dashboard()

            except ValidationError as exc:
                messagebox.showerror('No se pudo iniciar sesión', str(exc))

        password.bind('<Return>', login)

        action(
            card,
            'INICIAR SESIÓN',
            login,
            background=COLORS['dark_button'],
        ).pack(fill='x', pady=(23, 10))

        action(
            card,
            'CREAR CUENTA NUEVA',
            self.show_register,
            background='#D9D9D9',
            foreground=COLORS['ink'],
        ).pack(fill='x')

        label(
            card,
            'Demo: demo@smartuni.edu / Demo1234!',
            9,
            COLORS['muted'],
        ).pack(pady=(16, 0))

        email.focus_set()

    def show_register(self):
        """Aquí capturamos los datos y mandamos a registrar al estudiante."""
        self.clear()

        backdrop = tk.Frame(self, bg=COLORS['form_bg'])
        backdrop.pack(fill='both', expand=True)

        card = tk.Frame(backdrop, bg='white', padx=46, pady=25)
        card.place(
            relx=0.5,
            rely=0.5,
            anchor='center',
            width=520,
            height=630,
        )

        self.brand(card).pack(anchor='center', pady=(3, 10))
        label(card, 'Registro de estudiante', 20, bold=True).pack(pady=(0, 8))
        label(
            card,
            'Crea tu cuenta para acceder a Smart Uni',
            11,
            COLORS['muted'],
        ).pack(pady=(0, 15))

        entries = {}
        form_fields = [
            ('Nombre completo', 'name', False),
            ('Correo institucional', 'email', False),
            ('Carrera', 'career', False),
            ('Contraseña', 'password', True),
        ]

        for title, key, secret in form_fields:
            label(card, title, 10, bold=True).pack(
                anchor='w',
                pady=(6, 4),
            )

            widget = field(card, password=secret)
            widget.configure(
                bg=COLORS['field'],
                highlightbackground='#AAD3F1',
            )
            widget.pack(fill='x', ipady=7)
            entries[key] = widget

        def register():
            try:
                self.service.register(
                    *(
                        entries[key].get()
                        for key in ('name', 'email', 'career', 'password')
                    )
                )
                messagebox.showinfo(
                    'Registro exitoso',
                    'Cuenta creada correctamente. Inicia sesión.',
                )
                self.show_login()

            except ValidationError as exc:
                messagebox.showerror('Datos inválidos', str(exc))

        action(
            card,
            'CREAR CUENTA',
            register,
            background=COLORS['aqua'],
        ).pack(fill='x', pady=(21, 10))

        action(
            card,
            'VOLVER AL INICIO DE SESIÓN',
            self.show_login,
            background='#E5ECF4',
            foreground=COLORS['ink'],
        ).pack(fill='x')

    def shell(self, current: str):
        """Barra única y menú hamburguesa colocado en el borde izquierdo.

        Antes teníamos dos menús: uno arriba y otro dentro de Mi espacio.
        Ahora las secciones comparten esta navegación y el área de trabajo
        utiliza todo el ancho disponible cuando el menú está cerrado.
        """
        self.clear()

        outer = tk.Frame(self, bg=COLORS['page'])
        outer.pack(fill='both', expand=True)

        bar = tk.Frame(
            outer,
            bg=COLORS['surface'],
            height=78,
            highlightbackground=COLORS['line'],
            highlightthickness=1,
        )
        bar.pack(fill='x')
        bar.pack_propagate(False)

        self._hamburger = tk.Button(
            bar,
            text='☰',
            command=self._toggle_navigation,
            font=(FONT_TEXT, 21),
            bg=COLORS['surface'],
            fg=COLORS['ink'],
            activebackground='#EAF4FF',
            bd=0,
            padx=13,
            pady=0,
            cursor='hand2',
        )
        self._hamburger.pack(side='left', padx=(13, 9))
        self.brand(bar).pack(side='left', padx=(0, 20))

        tk.Frame(bar, width=1, bg=COLORS['line']).pack(
            side='left', fill='y', pady=19, padx=(0, 20)
        )
        label(bar, current, 11, COLORS['muted'], bold=True).pack(side='left')

        tk.Button(
            bar,
            text='Cerrar sesión',
            command=self.logout,
            font=(FONT_TEXT, 10, 'bold'),
            fg=COLORS['blue'],
            bg='#EAF4FF',
            bd=0,
            cursor='hand2',
            padx=15,
            pady=9,
        ).pack(side='right', padx=(10, 25))

        if self.user:
            first = self.user['name'].split()[0]
            label(bar, first, 11, COLORS['ink'], True).pack(side='right', padx=(0, 8))
            initials = ''.join(part[0] for part in self.user['name'].split()[:2]).upper()
            avatar = tk.Frame(bar, bg=COLORS['blue'], width=35, height=35)
            avatar.pack_propagate(False)
            avatar.pack(side='right', padx=(0, 10))
            label(avatar, initials, 10, 'white', True, COLORS['blue']).pack(expand=True)

        workspace = tk.Frame(outer, bg=COLORS['page'])
        workspace.pack(fill='both', expand=True)
        self._navigation = tk.Frame(
            workspace,
            bg='#FFFFFF',
            width=232,
            highlightthickness=1,
            highlightbackground=COLORS['line'],
        )
        self._navigation.pack_propagate(False)
        self._content_holder = tk.Frame(workspace, bg=COLORS['page'])
        self._content_holder.pack(side='left', fill='both', expand=True)
        self._nav_open = False

        for group, entries in self._navigation_entries():
            label(
                self._navigation,
                group,
                9,
                COLORS['muted'],
                True,
                bg='#FFFFFF',
            ).pack(anchor='w', padx=23, pady=(23, 9))
            for title, callback in entries:
                active = (current == title or
                          (current == 'Mi espacio' and title == 'Inicio académico'))
                tk.Button(
                    self._navigation,
                    text=title,
                    command=callback,
                    anchor='w',
                    font=(FONT_TEXT, 10, 'bold' if active else 'normal'),
                    fg=COLORS['blue'] if active else COLORS['ink'],
                    bg='#EAF4FF' if active else '#FFFFFF',
                    activeforeground=COLORS['blue'],
                    activebackground='#EAF4FF',
                    bd=0,
                    relief='flat',
                    cursor='hand2',
                    padx=17,
                    pady=8,
                ).pack(fill='x', padx=11, pady=2)

        content = tk.Frame(
            self._content_holder,
            bg=COLORS['page'],
            padx=32,
            pady=26,
        )
        content.pack(fill='both', expand=True)
        return content

    def logout(self):
        """Quitamos al usuario activo y regresamos al inicio de sesión."""
        self.user = None
        self.show_login()

    def title_block(self, parent, title_text, subtitle):
        """Mostramos el título y una explicación corta de cada pantalla."""
        label(parent, title_text, 24, bold=True).pack(anchor='w')
        label(parent, subtitle, 11, COLORS['muted']).pack(
            anchor='w',
            pady=(7, 23),
        )

    def panel(self, parent, *, padx=18, pady=15):
        """Creamos las tarjetas blancas usadas en varias pantallas."""
        return tk.Frame(
            parent,
            bg='white',
            padx=padx,
            pady=pady,
            highlightbackground=COLORS['line'],
            highlightthickness=1,
        )

    def stat_card(self, parent, heading, value):
        """Creamos una tarjeta con un dato del resumen académico."""
        card = self.panel(parent, padx=23, pady=20)
        label(card, heading, 11, COLORS['muted']).pack(anchor='w')
        label(card, str(value), 27, COLORS['blue'], True).pack(
            anchor='w',
            pady=(9, 0),
        )
        return card

    def show_dashboard(self):
        """Mostramos el resumen, los cursos y los anuncios del estudiante."""
        body = self.shell('Panel principal')
        name = self.user['name'].split()[0] if self.user else 'Estudiante'

        self.title_block(
            body,
            f'Bienvenido, {name}',
            'Resumen de actividad académica, progreso y avisos importantes',
        )

        stats = tk.Frame(body, bg=COLORS['page'])
        stats.pack(fill='x')
        summary = self.service.summary()

        stats_items = [
            ('Cursos activos', summary['total_courses']),
            ('Progreso promedio', f"{summary['average_progress']}%"),
            ('Avisos recientes', summary['total_announcements']),
        ]

        for index, (heading, value) in enumerate(stats_items):
            stats.columnconfigure(index, weight=1, uniform='stat')
            self.stat_card(stats, heading, value).grid(
                row=0,
                column=index,
                sticky='nsew',
                padx=(0, 12) if index < 2 else 0,
            )

        main_area = tk.Frame(body, bg=COLORS['page'])
        main_area.pack(fill='both', expand=True, pady=(22, 0))
        main_area.columnconfigure(0, weight=3)
        main_area.columnconfigure(1, weight=2)

        courses = self.panel(main_area)
        courses.grid(row=0, column=0, sticky='nsew', padx=(0, 15))

        announcements = self.panel(main_area)
        announcements.grid(row=0, column=1, sticky='nsew')

        label(courses, 'Mis cursos', 16, bold=True).pack(
            anchor='w',
            pady=(0, 12),
        )

        for course in self.service.courses():
            line = tk.Frame(courses, bg='white')
            line.pack(fill='x', pady=7)

            label(line, course['nombre'], 11, bold=True).pack(side='left')
            label(
                line,
                f"{course['progreso']}%",
                11,
                COLORS['blue'],
                True,
            ).pack(side='right')

            track = tk.Frame(courses, bg='#E9F1FA', height=8)
            track.pack(fill='x', pady=(0, 5))
            track.update_idletasks()

            tk.Frame(
                track,
                bg=COLORS['blue'],
                width=max(
                    1,
                    int(track.winfo_width() * course['progreso'] / 100),
                ),
                height=8,
            ).place(x=0, y=0)

        label(announcements, 'Anuncios y eventos', 16, bold=True).pack(
            anchor='w',
            pady=(0, 10),
        )

        for note in self.service.announcements():
            item = tk.Frame(
                announcements,
                bg=COLORS['pale'],
                padx=12,
                pady=10,
            )
            item.pack(fill='x', pady=6)

            label(
                item,
                f"{note['fecha']} · {note['titulo']}",
                10,
                COLORS['ink'],
                True,
                bg=COLORS['pale'],
                wraplength=280,
                justify='left',
            ).pack(anchor='w')

            label(
                item,
                note['detalle'],
                9,
                COLORS['muted'],
                bg=COLORS['pale'],
                wraplength=280,
                justify='left',
            ).pack(anchor='w', pady=(4, 0))

    def show_courses(self):
        """Mostramos los cursos y actualizamos la lista mientras buscamos."""
        body = self.shell('Cursos')
        self.title_block(
            body,
            'Mis cursos',
            'Consulta las asignaturas y busca por materia o docente',
        )

        search_bar = tk.Frame(body, bg=COLORS['page'])
        search_bar.pack(fill='x', pady=(0, 15))
        label(search_bar, 'Buscar:', 12, bold=True).pack(
            side='left',
            padx=(0, 10),
        )

        search = field(search_bar)
        search.pack(side='left', fill='x', expand=True, ipady=9)

        results = tk.Frame(body, bg=COLORS['page'])
        results.pack(fill='both', expand=True)

        def refresh(*_):
            for child in results.winfo_children():
                child.destroy()

            courses = self.service.courses(search.get())

            if not courses:
                label(
                    results,
                    'No se encontraron asignaturas.',
                    12,
                    COLORS['muted'],
                ).pack(anchor='w')

            for course in courses:
                row = self.panel(results)
                row.pack(fill='x', pady=5)

                label(row, course['nombre'], 13, bold=True).pack(side='left')
                label(
                    row,
                    f"{course['docente']}  ·  {course['progreso']}% de progreso",
                    11,
                    COLORS['muted'],
                ).pack(side='right')

        search.bind('<KeyRelease>', refresh)
        refresh()

    def show_schedule(self):
        """Mostramos el horario de clases con sus días, horas y aulas."""
        body = self.shell('Horario')
        self.title_block(
            body,
            'Horario de clases',
            'Clases organizadas por día, hora y aula',
        )

        for course in self.service.schedule():
            row = self.panel(body)
            row.pack(fill='x', pady=5)

            label(
                row,
                f"{course['dia']}  ·  {course['hora']}",
                12,
                COLORS['blue'],
                True,
            ).pack(side='left', padx=(0, 28))

            label(row, course['nombre'], 12, bold=True).pack(side='left')
            label(
                row,
                f"Aula {course['aula']}",
                11,
                COLORS['muted'],
            ).pack(side='right')

    def show_announcements(self):
        """Mostramos los avisos y eventos académicos disponibles."""
        body = self.shell('Anuncios')
        self.title_block(
            body,
            'Anuncios y eventos',
            'Mantente al día con la actividad de tu facultad',
        )

        for note in self.service.announcements():
            card = self.panel(body, padx=21, pady=17)
            card.pack(fill='x', pady=7)

            label(card, note['fecha'], 10, COLORS['blue'], True).pack(
                anchor='w'
            )
            label(card, note['titulo'], 15, bold=True).pack(
                anchor='w',
                pady=5,
            )
            label(card, note['detalle'], 11, COLORS['muted']).pack(anchor='w')

    def show_student_space(self, section='Inicio'):
        """Abrimos los nuevos apartados sin cambiar las pantallas anteriores."""
        from .student_ui import StudentSpaceView

        body = self.shell(section if section != 'Inicio' else 'Inicio académico')
        StudentSpaceView(self, body, section)
