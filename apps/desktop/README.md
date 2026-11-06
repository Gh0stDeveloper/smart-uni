# SMART UNI — aplicación de escritorio (prototipo)

Esta es la versión de SMART UNI que ya desarrollamos en Python/Tkinter para Windows y Linux. **Conservamos el inicio de sesión, la navegación actual y el icono original del birrete azul/turquesa.** No estamos modificando su diseño para empezar SMART UNI 2.0.

## Cómo ejecutar

Necesitamos Python 3.10+ con Tkinter:

```bash
cd apps/desktop
python main.py
```

**Para la exposición únicamente:** correo `demo@smartuni.edu`, contraseña `Demo1234!`. Esta cuenta se eliminará en producción.

## Funciones existentes

Registro y acceso local, panel, cursos, horarios, anuncios, Inicio, Perfil, Amigos, Calendario, Material, Tareas y Apuntes.

Los registros se guardan en JSON. Todavía **no existe sincronización real, cifrado de base de datos, servidor ni aplicación Android**.

## Pruebas

```bash
cd apps/desktop
python -m unittest discover -s tests -v
```

Son 39 pruebas automatizadas (17 originales + 9 de línea base + 13 de la etapa 2); dos requieren pantalla gráfica. Evidencia: [etapa 1](../../docs/phase-1/1_CIERRE_Y_EVIDENCIAS.md) y [etapa 2](../../docs/phase-2/2_CIERRE_Y_EVIDENCIAS.md).

## Windows

Puedes ejecutar `compilar_exe_windows.bat` en una computadora con Python instalado. Utiliza PyInstaller para crear `dist/Smart_Uni.exe`. El script genera un icono .ico a partir del isotipo original, sin cambiar las pantallas.

También hay un flujo de GitHub Actions para compilar la aplicación.

## Figma

La fuente del diseño está en `design/figma_svg/` y los colores/fuentes en `design/tokens.json`. Los recursos actuales son una base de referencia; algunas maquetas antiguas pueden no representar la navegación final. La interfaz ejecutable es la referencia de comportamiento visual actual.

Las decisiones de SMART UNI 2.0 están en `../../docs/architecture/`.
## Organización de la etapa 2

`smart_uni/domain.py` mantiene validaciones y algoritmos heredados; `repository.py` abstrae el JSON; `session.py` conserva la identidad local sin introducir API online; `core.py` y `student_data.py` implementan los servicios, y las pantallas originales permanecen en `ui.py` y `student_ui.py`. Los roles visuales se leen mediante `design_system.py` de los tokens originales. Ningún control remoto de autorización, SQLite, Rust ni sincronización está implementado todavía.

## Núcleo nativo Rust disponible (etapa 3)

El adaptador opcional `smart_uni/native_bridge.py` puede cargar una biblioteca Rust local construida con Cargo al definir `SMARTUNI_NATIVE_LIB`; no participa en el arranque de Tkinter ni cambia el login o los datos actuales. [Documentación y pruebas](../../docs/phase-3/3_CIERRE_Y_EVIDENCIAS.md). En el workflow normal hay 43 tests descubiertos (39 ejecutados + 4 de puente omitidos); en el workflow Rust se ejecutan los cuatro tests de FFI **contra código nativo real**, tanto en Windows como en Linux.
