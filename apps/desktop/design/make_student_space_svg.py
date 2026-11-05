"""Dos pantallas vectoriales para seguir editando el diseño en Figma.

No reemplazamos los SVG originales; agregamos Mi espacio y Material.
"""

from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).parent / 'figma_svg'
OUT.mkdir(parents=True, exist_ok=True)


def rect(x, y, w, h, fill, stroke='none', radius=0):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" />'


def txt(x, y, value, size=18, color='#243448', weight='400'):
    return (
        f'<text x="{x}" y="{y}" font-family="Roboto, sans-serif" '
        f'font-size="{size}" fill="{color}" font-weight="{weight}">'
        f'{escape(str(value))}</text>'
    )


def frame(active, title, subtitle):
    s = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="740" viewBox="0 0 1100 740">',
        rect(0, 0, 1100, 740, '#F3F7FC'),
        rect(0, 0, 1100, 78, '#FFFFFF'),
        txt(33, 46, '◆ SMART UNI', 22, '#2B80EC', '700'),
    ]
    for x, text, width in [
        (252, 'Panel principal', 130),
        (386, 'Cursos', 75),
        (465, 'Horario', 80),
        (549, 'Anuncios', 90),
        (643, 'Mi espacio', 100),
    ]:
        chosen = text == 'Mi espacio'
        s.append(rect(x, 18, width, 40, '#E7F2FF' if chosen else '#FFFFFF', '#D9E0E7'))
        s.append(txt(x + 14, 43, text, 14, '#2B80EC' if chosen else '#65768C', '700'))
    s.append(txt(957, 44, 'Cerrar sesión', 14, '#2B80EC'))
    s.append(rect(35, 106, 192, 606, '#E9F3FF', '#DCE7F2'))
    s.append(rect(53, 123, 52, 52, '#2B80EC'))
    s.append(txt(66, 157, 'AR', 20, '#FFFFFF', '700'))
    s.append(txt(54, 202, 'Alex Rivera', 16, '#243448', '700'))
    s.append(txt(54, 226, 'MI ESPACIO ACADÉMICO', 10, '#65768C'))
    for i, text in enumerate(['Inicio', 'Perfil', 'Amigos', 'Calendario', 'Material', 'Tareas', 'Apuntes']):
        y = 251 + i * 49
        selected = active == text
        s.append(rect(47, y, 168, 44, '#2B80EC' if selected else '#E9F3FF', 'none' if selected else '#DCE7F2'))
        s.append(txt(62, y + 28, text, 15, '#FFFFFF' if selected else '#243448', '700' if selected else '400'))
    s.append(txt(62, 691, '← Volver al panel', 14, '#2B80EC'))
    s.append(txt(248, 141, title, 30, '#243448', '700'))
    s.append(txt(248, 173, subtitle, 14, '#65768C'))
    return s


def box(x, y, w, h, title, background='#FFFFFF'):
    return [rect(x, y, w, h, background, '#DCE7F2'), txt(x + 19, y + 35, title, 20, '#243448', '700')]


def make_home():
    s = frame('Inicio', 'Tu espacio, Alex', 'Próximas fechas, materiales y apuntes en un solo lugar.')
    for x, title, amount in [(248, 'Materias', '8'), (514, 'Tareas pendientes', '2'), (780, 'Mis apuntes', '2')]:
        s += [rect(x, 200, 256, 105, '#FFFFFF', '#DCE7F2'), txt(x + 18, 228, title, 14, '#65768C'), txt(x + 18, 279, amount, 30, '#2B80EC', '700')]
    s += box(248, 321, 392, 256, 'Próximos exámenes')
    s += [txt(267, 406, 'Examen de Cálculo', 16, '#243448', '700'), txt(548, 406, '08 nov', 14, '#2B80EC'),
          txt(267, 468, 'Examen de Programación', 16, '#243448', '700'), txt(548, 468, '12 nov', 14, '#2B80EC')]
    s += box(657, 321, 392, 256, 'Recordatorios')
    s += [txt(676, 406, 'Entrega de ejercicio', 16, '#243448', '700'), txt(955, 406, '06 nov', 14, '#2B80EC'),
          txt(676, 468, 'Proyecto integrador', 16, '#243448', '700'), txt(955, 468, '10 nov', 14, '#2B80EC')]
    s += box(248, 592, 392, 120, 'Últimos apuntes')
    s += [txt(267, 664, 'Resumen de álgebra', 16, '#243448')]
    s += box(657, 592, 392, 120, 'Consejo del día', '#EAF9FA')
    s += [txt(676, 667, 'Organiza tus apuntes por materia.', 15, '#243448')]
    s.append('</svg>')
    return '\n'.join(s)


def make_material():
    s = frame('Material', 'Material de estudio', 'Tus ocho materias organizadas en carpetas.')
    names = [
        'Cálculo', 'Actividad Estudiantil',
        'Habilidades de Comunicación', 'Maquetación',
        'Historia de Identidad Nacional', 'Programa Estructurado',
        'Proyecto Integrador', 'Fundamentos de Informática',
    ]
    for index, name in enumerate(names):
        x = 248 + (index % 2) * 401
        y = 198 + (index // 2) * 127
        s.append(rect(x, y, 384, 112, '#EAF4FF', '#DCE7F2'))
        s.append(rect(x + 18, y + 16, 32, 12, '#E6A139'))
        s.append(rect(x + 18, y + 24, 64, 36, '#FFD477'))
        s.append(txt(x + 98, y + 43, name, 14, '#243448', '700'))
        s.append(txt(x + 98, y + 72, 'Abrir carpeta', 12, '#2B80EC'))
    s.append('</svg>')
    return '\n'.join(s)


(OUT / '05_mi_espacio.svg').write_text(make_home(), encoding='utf-8')
(OUT / '06_material_8_materias.svg').write_text(make_material(), encoding='utf-8')
print('Pantallas SVG nuevas listas para importar en Figma.')
