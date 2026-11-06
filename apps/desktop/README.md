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

El modo de uso normal guarda JSON **sin cifrar**. La etapa 4 añadió un repositorio **SQLCipher experimental y opcional**; sin backend, APK Android, E2EE ni cifrado de materiales. El modo seguro bloquea materiales en vez de guardarlos sin protección.

## Pruebas

```bash
cd apps/desktop
python -m unittest discover -s tests -v
```

Son 68 casos descubiertos en la suite normal: 42 de funcionalidad y regresión (incluyendo tres pruebas PBKDF2), 22 pruebas SQLCipher omitidas cuando no hay dependencias opcionales, y cuatro pruebas FFI Rust omitidas sin la biblioteca nativa; dos pruebas requieren pantalla gráfica. En CI especial SQLCipher se ejecutan 22/22 sin omisiones. Evidencia: [etapa 1](../../docs/phase-1/1_CIERRE_Y_EVIDENCIAS.md) y [etapa 2](../../docs/phase-2/2_CIERRE_Y_EVIDENCIAS.md).

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

## Modo cifrado opt-in (4.1–4.3)

Instalar `python -m pip install -r requirements-secure.txt` en Windows/Linux con keyring del SO desbloqueado. Establecer `SMARTUNI_STORAGE=secure` y ejecutar `python main.py`. La base local utiliza SQLCipher y, si existe JSON v1, lo migra **conservando el origen**. Si falta clave o servicio de claves, aborta sin crear una base sin cifrar. El EXE clásico de GitHub Actions no incluye SQLCipher; esta configuración debe probarse desde fuente.

El modo seguro mantiene tareas, apuntes y perfil en SQLCipher, registra operaciones cubiertas en la outbox y presenta estados locales discretos. No cifra materiales: su importación se bloquea para evitar filtraciones. No se garantiza aún autorización por sesión ni red; nunca mostrar “sincronizado” sin ACK del servidor. [Acta técnica](../../docs/phase-4/4_CIERRE_Y_EVIDENCIAS.md) y [registro de pendientes P01–P36](../../docs/PENDIENTES_SMART_UNI_2_0.md).

## Protección de hash histórico y etapa 5

Se añadieron límites verificables de costo PBKDF2 (100 000 a 1 000 000 rondas, sal de 16 bytes, digest de 32 bytes) conservando las 260 000 rondas de registros existentes. [Regresión CI](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42225588765). La nueva API remota existe en [services/api](../../services/api/README.md), **sin conexión al cliente Tkinter y sin autorización de sesión local todavía**. No introducir datos reales en el JSON o los materiales clásicos.
