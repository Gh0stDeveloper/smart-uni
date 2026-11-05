"""Aquí generamos los diseños SVG que podemos importar en Figma.

Este script también crea las imágenes PNG de referencia. Los mismos tamaños,
colores y elementos del diseño original se mantienen sin cambios.
"""

import json
from html import escape
from pathlib import Path

import cairosvg


BASE = Path(__file__).parent
OUT = BASE / 'figma_svg'
PREV = BASE / 'previews'

OUT.mkdir(exist_ok=True)
PREV.mkdir(exist_ok=True)

# Colores que utilizamos en nuestra guía de SMART UNI.
BLUE = '#2B80EC'
CYAN = '#2BB2C4'
INK = '#243448'
MUTED = '#65768C'
PAGE = '#F3F7FC'
LINE = '#E2E8F0'
PALE = '#D8EBFD'


def tag(x, y, txt, size=20, color=INK, bold=False, anchor='start', font=None):
    """Agregamos un texto al diseño SVG con su tamaño y color."""
    font = font or ('Poppins' if bold else 'Roboto')

    return (
        f'<text x="{x}" y="{y}" fill="{color}" '
        f'font-family="{font},Arial,sans-serif" font-size="{size}" '
        f'font-weight="{700 if bold else 400}" text-anchor="{anchor}">'
        f'{escape(str(txt))}</text>'
    )


def rect(x, y, w, h, fill='#FFFFFF', r=0, stroke=None, stroke_w=1):
    """Agregamos un rectángulo, por ejemplo, para un campo o una tarjeta."""
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
        f'rx="{r}" fill="{fill}"'
        + (
            f' stroke="{stroke}" stroke-width="{stroke_w}"'
            if stroke
            else ''
        )
        + '/>'
    )


def logo(x, y, scale=1, with_name=True):
    """Dibujamos el birrete y, cuando corresponde, agregamos SMART UNI."""
    content = f'<g transform="translate({x},{y}) scale({scale})">'
    content += '<path d="M2 20 L24 6 L46 20 L24 34 Z" fill="#2B80EC"/>'
    content += '<path d="M13 29 L13 39 Q24 45 35 39 L35 29 L24 35 Z" fill="#2BB2C4"/>'
    content += '<path d="M42 21 L42 38" stroke="#2BB2C4" stroke-width="3" stroke-linecap="round"/>'
    content += '</g>'

    if with_name:
        content += tag(x + 56 * scale, y + 31 * scale, 'SMART UNI', 24 * scale, BLUE, True)

    return content


def wrap(body, w=1440, h=900):
    """Colocamos todos los elementos dentro del tamaño de lienzo indicado."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" '
        f'height="{h}" viewBox="0 0 {w} {h}">'
        + body
        + '</svg>'
    )


def save(name, body, w=1440, h=900):
    """Guardamos el SVG y tratamos de crear también su vista previa PNG."""
    path = OUT / name
    path.write_text(wrap(body, w, h), encoding='utf-8')

    try:
        cairosvg.svg2png(
            bytestring=path.read_bytes(),
            write_to=str(PREV / name.replace('.svg', '.png')),
            output_width=w // 2,
            output_height=h // 2,
        )
    except Exception as err:
        print('Could not rasterize', name, err)


# Primero guardamos el logotipo y el isotipo por separado.
save('00_logo_smart_uni.svg', logo(68, 80, 3, True), w=680, h=250)
save('00_isotipo_smart_uni.svg', logo(45, 38, 3, False), w=225, h=185)


# PANTALLA 1: Inicio de sesión.
# El fondo es azul claro y el botón principal es gris oscuro.
s = rect(0, 0, 1440, 900, '#91C8F0')
s += rect(435, 103, 570, 694, '#FFFFFF', 26)
s += logo(562, 162, 1.35)
s += tag(720, 301, 'Inicia sesión', 36, INK, True, 'middle')
s += tag(720, 345, 'Bienvenido a tu espacio académico', 19, MUTED, False, 'middle')
s += tag(503, 419, 'Correo institucional', 18, INK, True)
s += rect(503, 439, 434, 59, '#FFFFFF', 10, '#CBD5E1', 2)
s += tag(524, 476, 'estudiante@universidad.edu', 17, '#98A6B6')
s += tag(503, 538, 'Contraseña', 18, INK, True)
s += rect(503, 557, 434, 59, '#FFFFFF', 10, '#CBD5E1', 2)
s += tag(524, 595, '••••••••••', 20, '#98A6B6')
s += rect(503, 648, 434, 62, '#333333', 10)
s += tag(720, 688, 'INICIAR SESIÓN', 18, '#FFFFFF', True, 'middle')
s += rect(503, 723, 434, 50, '#D9D9D9', 10)
s += tag(720, 756, 'CREAR CUENTA NUEVA', 16, INK, True, 'middle')
s += tag(
    720, 846, 'SMART UNI / Prototipo de interfaz · Diseño académico',
    15, INK, False, 'middle',
)
save('01_inicio_sesion.svg', s)


# PANTALLA 2: Registro de estudiante.
# Aquí agregamos el formulario y el botón Crear cuenta.
s = rect(0, 0, 1440, 900, '#D3D3D3')
s += rect(420, 42, 600, 815, '#FFFFFF', 24)
s += logo(566, 84, 1.25)
s += tag(720, 213, 'Registro de estudiante', 32, INK, True, 'middle')
s += tag(720, 250, 'Crea tu cuenta institucional', 18, MUTED, False, 'middle')

items = [
    ('Nombre completo', 'Escribe tu nombre completo'),
    ('Correo institucional', 'nombre@universidad.edu'),
    ('Carrera', 'Ingeniería en Sistemas'),
    ('Contraseña', '••••••••••'),
]

for i, (title, placeholder) in enumerate(items):
    y = 303 + i * 109
    s += tag(492, y, title, 17, INK, True)
    s += rect(492, y + 17, 456, 60, '#8ACDF7', 9)
    s += tag(514, y + 56, placeholder, 17, '#4E6478')

s += rect(492, 748, 456, 59, CYAN, 9)
s += tag(720, 787, 'CREAR CUENTA', 18, '#FFFFFF', True, 'middle')
s += tag(720, 837, '¿Ya tienes cuenta? Inicia sesión', 15, BLUE, False, 'middle')
save('02_registro_estudiante.svg', s)


# PANTALLA 3: Panel principal.
# Mostramos la navegación, los indicadores, las materias y los anuncios.
s = rect(0, 0, 1440, 900, PAGE)
s += rect(0, 0, 1440, 94, '#FFFFFF') + logo(47, 20, 1.0)

navigation = [
    (385, 'Panel principal'),
    (570, 'Cursos'),
    (685, 'Horario'),
    (805, 'Anuncios'),
]

for x, text_label in navigation:
    if text_label == 'Panel principal':
        s += rect(x - 20, 25, 164, 43, '#E7F2FF', 12)

    s += tag(
        x,
        54,
        text_label,
        18,
        BLUE if text_label == 'Panel principal' else MUTED,
        text_label == 'Panel principal',
    )

s += rect(1290, 26, 105, 40, '#E7F2FF', 13)
s += tag(1342, 52, 'Alex R.', 16, BLUE, True, 'middle')
s += tag(75, 178, 'Bienvenido, Alex', 42, INK, True)
s += tag(75, 220, 'Resumen de actividad académica, horario, cursos y avisos', 20, MUTED)

stats = [
    ('Cursos activos', '04'),
    ('Progreso promedio', '69%'),
    ('Avisos recientes', '03'),
]

for i, (heading, value) in enumerate(stats):
    x = 75 + i * 444
    s += rect(x, 268, 418, 150, '#FFFFFF', 17, LINE)
    s += tag(x + 25, 314, heading, 19, MUTED)
    s += tag(x + 25, 382, value, 50, BLUE, True)

s += rect(75, 443, 831, 394, '#FFFFFF', 16, LINE)
s += rect(933, 443, 432, 394, '#FFFFFF', 16, LINE)
s += tag(107, 493, 'Mis cursos', 25, INK, True)

courses = [
    ('Programación I', 75),
    ('Matemáticas Discretas', 62),
    ('Bases de Datos', 88),
    ('Diseño Web', 50),
]

for i, (course, progress) in enumerate(courses):
    y = 544 + i * 67
    s += tag(109, y, course, 18, INK, True)
    s += tag(851, y, f'{progress}%', 16, BLUE, True, 'end')
    s += rect(109, y + 13, 738, 9, '#E8F2FB', 5)
    s += rect(109, y + 13, 738 * progress / 100, 9, BLUE, 5)

s += tag(958, 493, 'Anuncios y eventos', 24, INK, True)

announcements = [
    ('05 nov', 'Entrega de proyecto final', 'Programación I · 23:59'),
    ('10 nov', 'Semana de evaluación', 'Consulta tu horario'),
    ('16 nov', 'Taller de innovación', 'Auditorio central'),
]

for i, (date, title, description) in enumerate(announcements):
    y = 521 + i * 97
    s += rect(958, y, 378, 87, PALE, 11)
    s += tag(973, y + 27, f'{date} · {title}', 15, INK, True)
    s += tag(973, y + 55, description, 15, MUTED)

save('03_panel_principal.svg', s)


# PANTALLA 4: Guía visual.
# Dejamos el logo, las fuentes, la paleta y algunos componentes de ejemplo.
s = rect(0, 0, 1440, 900, '#F6FAFE')
s += tag(70, 99, 'Sistema de diseño · SMART UNI', 39, BLUE, True)
s += tag(71, 140, 'Guía para Figma · Tipografía, colores, componentes y marca', 18, MUTED)
s += rect(70, 180, 590, 250, '#FFFFFF', 18, LINE)
s += tag(104, 228, 'Marca / Logotipo', 23, INK, True)
s += logo(156, 285, 2.6)
s += rect(694, 180, 676, 250, '#FFFFFF', 18, LINE)
s += tag(730, 228, 'Tipografías', 23, INK, True)
s += tag(733, 293, 'Poppins  /  Encabezados y títulos', 26, INK, True)
s += tag(733, 357, 'Roboto  /  Cuerpo de texto y formularios', 23, INK)
s += tag(71, 494, 'Paleta cromática', 26, INK, True)

colors = [
    ('#91C8F0', 'Inicio / Fondo'),
    (CYAN, 'Registro / CTA'),
    (BLUE, 'Primario'),
    ('#8ACDF7', 'Campos'),
    ('#D8EBFD', 'Destacados'),
    ('#333333', 'Acción oscura'),
]

for i, (color, caption) in enumerate(colors):
    x = 70 + i * 219
    s += rect(x, 523, 198, 158, '#FFFFFF', 15, LINE)
    s += rect(x + 13, 534, 172, 94, color, 11)
    s += tag(x + 14, 652, color, 16, INK, True)
    s += tag(x + 14, 672, caption, 13, MUTED)

s += tag(70, 744, 'Componentes de interfaz', 26, INK, True)
s += rect(70, 780, 248, 62, BLUE, 9)
s += tag(194, 818, 'Botón primario', 17, '#FFFFFF', True, 'middle')
s += rect(344, 780, 260, 62, '#FFFFFF', 9, BLUE, 2)
s += tag(474, 818, 'Botón secundario', 17, BLUE, True, 'middle')
s += rect(631, 780, 326, 62, '#FFFFFF', 9, LINE)
s += tag(649, 819, 'Campo de formulario', 17, MUTED)
s += rect(991, 772, 379, 80, '#FFFFFF', 13, LINE)
s += tag(1011, 821, 'Tarjeta de contenido', 18, INK, True)

save('04_guia_estilos_logo.svg', s)


# Guardamos también los colores y las fuentes en un JSON para consultarlos.
tokens = {
    'project': 'SMART UNI',
    'typography': {
        'headings': 'Poppins',
        'body': 'Roboto',
    },
    'colors': {
        'login_background': '#91C8F0',
        'registration_background': '#D3D3D3',
        'registration_fields': '#8ACDF7',
        'login_action': '#333333',
        'cta': '#2BB2C4',
        'primary': '#2B80EC',
        'white': '#FFFFFF',
        'content_background': '#F3F7FC',
        'highlight': '#D8EBFD',
    },
    'radii': {
        'buttons': 8,
        'cards': 12,
    },
    'figma_canvas': {
        'width': 1440,
        'height': 900,
    },
}

(BASE / 'tokens.json').write_text(
    json.dumps(tokens, ensure_ascii=False, indent=2),
    encoding='utf-8',
)

print('Generated:', *[path.name for path in OUT.glob('*.svg')])
